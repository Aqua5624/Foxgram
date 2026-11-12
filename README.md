# Foxgram

Foxgram is a planned Nekogram-style iOS client, built as a fork-configuration
layer on top of the official open-source **Telegram-iOS** client. This
repository is intentionally small: it contains **no Telegram source code**.
It holds only the CI workflow and the configuration tooling needed to build
Telegram-iOS as "Foxgram".

## Build test (Phase 0.5)

The `Build Foxgram` workflow (manually dispatched) does the following on a
GitHub-hosted `macos-26` runner:

1. Clones `TelegramMessenger/Telegram-iOS` at the pinned app-12.10 commit
   `72e573e8b69f8f12736ac6086c826ab10e37d242` (versions.json: Xcode 26.6,
   Bazel 8.4.2, macOS 26 — matching the `macos-26` runner image).
2. Selects `/Applications/Xcode_26.6.app` as the active Xcode.
3. Generates the build configuration (`scripts/generate_config.py`):
   bundle id `org.aqua5624.foxgram`, app configuration in the shape of
   upstream's `template_minimal_development_configuration.json`.
4. Re-issues upstream's fake-codesigning provisioning profiles for the
   Foxgram bundle id (`scripts/remap_profiles.py`). Upstream profiles are
   bound to `ph.telegra.Telegraph`; `Make.py` only accepts profiles whose
   application-identifier matches the configured bundle id, so the profiles
   are decoded, rewritten, and re-signed with upstream's own SelfSigned
   certificate — the same technique as upstream's
   `build-system/Make/GenerateProfiles.py`. No upstream source code is
   modified.
5. Builds the **unmodified** upstream tree with upstream's own tooling
   (`ImportCertificates.py` + `Make.py build --configuration=release_arm64`)
   and publishes the resulting unsigned IPA as a GitHub Release asset
   (tag `build-test-1`) and as a workflow artifact.

## API credentials

The build configuration reads the repository secrets `FOXGRAM_API_ID` and
`FOXGRAM_API_HASH` when they are set. **They are currently not set**, so the
build falls back to clearly-dummy placeholder values
(api_id `1234567`, api_hash `0123456789abcdef0123456789abcdef`).

> ⚠️ An IPA produced with the dummy placeholders **cannot log in to
> Telegram**. This run measures buildability only. Real credentials will be
> injected via GitHub Secrets later; they never pass through this
> repository's files or chat.

## License note

Telegram-iOS and Nekogram are GPL-licensed (GPLv2-or-later / GPL-2.0). This
repository is private and personal-use only for now; distributing an IPA
would require publishing the corresponding source under the GPL.
