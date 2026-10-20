# ymdsh 1.0.11

This version bundles DSH 0.2.1-rc.2 and refines first-time installation and runtime diagnostics for Android 13.

- Checks offline tool metadata through the verified installation root to avoid false `PARENT_LINK` failures caused by Android private-path aliases.
- Resolves the storage module from the nested dependency layout used by newer DSH builds.
- Separates Ubuntu base-environment readiness from full DSH runtime health.
- Retains ADB, the three appearance palettes, the native interface, and the separate recovery environment.

**Signing change:** This release uses a new ymdsh signing certificate. It cannot be installed as a direct update over an APK signed by the previous certificate. Export and safely back up all existing app data before changing signatures.
