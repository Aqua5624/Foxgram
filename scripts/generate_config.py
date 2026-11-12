#!/usr/bin/env python3
"""Generate the Telegram-iOS build configuration for Foxgram.

The output follows upstream's
`build-system/template_minimal_development_configuration.json` field-for-field.

api_id / api_hash are read from the FOXGRAM_API_ID / FOXGRAM_API_HASH
environment variables (wired to GitHub repository secrets in the workflow).
When they are unset or empty, clearly-dummy placeholder values are used:
this build test measures buildability only, and an IPA built with the
placeholders cannot log in to Telegram.
"""

import argparse
import json
import os

DUMMY_API_ID = "1234567"
DUMMY_API_HASH = "0123456789abcdef0123456789abcdef"

# The fake-codesigning provisioning profiles shipped by upstream are issued
# for this team id; the configuration must match it (see remap_profiles.py).
FAKE_TEAM_ID = "C67CF9S4VU"

BUNDLE_ID = "org.aqua5624.foxgram"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    api_id = os.environ.get("FOXGRAM_API_ID") or ""
    api_hash = os.environ.get("FOXGRAM_API_HASH") or ""
    using_dummy = not (api_id and api_hash)
    if using_dummy:
        api_id = DUMMY_API_ID
        api_hash = DUMMY_API_HASH

    config = {
        "bundle_id": BUNDLE_ID,
        "api_id": str(api_id),
        "api_hash": str(api_hash),
        "team_id": FAKE_TEAM_ID,
        "is_internal_build": "true",
        "is_appstore_build": "false",
        "appstore_id": "0",
        "app_specific_url_scheme": "tg",
        "premium_iap_product_id": "",
        "enable_siri": False,
        "enable_icloud": False,
    }

    with open(args.output, "w") as f:
        json.dump(config, f, indent="\t")
        f.write("\n")

    print("Wrote configuration to {}".format(args.output))
    print("bundle_id={}".format(BUNDLE_ID))
    print(
        "api credentials: {}".format(
            "DUMMY placeholders (buildability test only — IPA cannot log in)"
            if using_dummy
            else "from repository secrets"
        )
    )


if __name__ == "__main__":
    main()
