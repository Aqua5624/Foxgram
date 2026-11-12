#!/usr/bin/env python3
"""Re-issue upstream fake-codesigning provisioning profiles for Foxgram.

Upstream Telegram-iOS ships fake-codesigning profiles bound to the bundle id
`ph.telegra.Telegraph` (team `C67CF9S4VU`). Its build tooling
(`BuildConfiguration.copy_profiles_from_directory`) only accepts a profile
whose application-identifier starts with "{team_id}.{bundle_id}" taken from
the build configuration, and decodes profiles with
`openssl smime -verify -noverify` (no chain verification).

This script mirrors upstream's own `build-system/Make/GenerateProfiles.py`
approach — temporary keychain with the upstream SelfSigned.p12, decode with
`security cms -D`, re-sign with `security cms -S` — and additionally rewrites
the bundle-id strings inside the profile plist so the profiles match the
Foxgram bundle id. No upstream source code is touched; this only re-issues
codesigning material, which every fork must supply for itself (see the
"Advanced Compilation Guide" in upstream's README).
"""

import argparse
import os
import plistlib
import subprocess
import sys
import tempfile


def run(cmd, check=True):
    print("+ {}".format(" ".join(cmd)))
    result = subprocess.run(cmd, capture_output=True)
    if check and result.returncode != 0:
        sys.stdout.write(result.stdout.decode("utf-8", "replace"))
        sys.stderr.write(result.stderr.decode("utf-8", "replace"))
        raise SystemExit("command failed: {}".format(cmd[0]))
    return result


def replace_bundle(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, bytes):
        return value
    if isinstance(value, list):
        return [replace_bundle(v, old, new) for v in value]
    if isinstance(value, dict):
        return {k: replace_bundle(v, old, new) for k, v in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Directory with upstream .mobileprovision files")
    parser.add_argument("--certs", required=True, help="Directory containing SelfSigned.p12")
    parser.add_argument("--destination", required=True, help="Output directory for re-issued profiles")
    parser.add_argument("--old-bundle-id", default="ph.telegra.Telegraph")
    parser.add_argument("--new-bundle-id", required=True)
    args = parser.parse_args()

    p12_path = os.path.join(args.certs, "SelfSigned.p12")
    if not os.path.exists(p12_path):
        print("{} does not exist".format(p12_path))
        sys.exit(1)
    os.makedirs(args.destination, exist_ok=True)

    keychain = "foxgram-profiles.keychain"
    keychain_password = "foxgram"

    run(["security", "delete-keychain", keychain], check=False)
    run(["security", "create-keychain", "-p", keychain_password, keychain])
    existing = (
        run(["security", "list-keychains", "-d", "user"])
        .stdout.decode("utf-8", "replace")
        .replace('"', "")
        .split()
    )
    run(["security", "list-keychains", "-d", "user", "-s", keychain] + existing)
    run(["security", "set-keychain-settings", keychain])
    run(["security", "unlock-keychain", "-p", keychain_password, keychain])
    run(
        [
            "security", "import", p12_path, "-k", keychain, "-P", "",
            "-T", "/usr/bin/codesign", "-T", "/usr/bin/security",
        ]
    )
    run(
        [
            "security", "set-key-partition-list", "-S", "apple-tool:,apple:",
            "-k", keychain_password, keychain,
        ]
    )

    identities = run(
        ["security", "find-identity", "-v", "-p", "codesigning", keychain]
    ).stdout.decode("utf-8", "replace")
    identity = None
    for line in identities.splitlines():
        if '"' in line:
            identity = line.split('"')[1]
            break
    if not identity:
        print("No codesigning identity found after importing {}".format(p12_path))
        sys.exit(1)
    print("Using signing identity: {}".format(identity))

    try:
        count = 0
        for file_name in sorted(os.listdir(args.source)):
            if not file_name.endswith(".mobileprovision"):
                continue
            source_path = os.path.join(args.source, file_name)
            destination_path = os.path.join(args.destination, file_name)

            decoded = run(["security", "cms", "-D", "-i", source_path]).stdout
            profile = plistlib.loads(decoded)
            profile = replace_bundle(profile, args.old_bundle_id, args.new_bundle_id)
            profile.pop("DER-Encoded-Profile", None)

            with tempfile.NamedTemporaryFile("wb", suffix=".plist", delete=False) as tf:
                plistlib.dump(profile, tf)
                plist_path = tf.name
            try:
                run(
                    [
                        "security", "cms", "-S", "-k", keychain, "-N", identity,
                        "-i", plist_path, "-o", destination_path,
                    ]
                )
            finally:
                os.unlink(plist_path)

            check = plistlib.loads(
                run(["security", "cms", "-D", "-i", destination_path]).stdout
            )
            app_id = check["Entitlements"]["application-identifier"]
            print("{} -> {}".format(file_name, app_id))
            if args.new_bundle_id not in app_id:
                print("bundle id rewrite failed for {}".format(file_name))
                sys.exit(1)
            count += 1
        print("Re-issued {} profiles for {}".format(count, args.new_bundle_id))
    finally:
        run(["security", "delete-keychain", keychain], check=False)


if __name__ == "__main__":
    main()
