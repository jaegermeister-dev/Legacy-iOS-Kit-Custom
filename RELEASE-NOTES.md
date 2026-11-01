# Legacy iOS Kit (Custom) 1.0.0

Restore to iOS 10.3.4 (14G61) with Socket's jailbreak assets, Zebra, and the
Procyon untether installed during restoration. No sideloading, second DFU boot,
or installer app is required.

- Tested restore, reboot, Zebra, and tweak injection on iPhone5,2, iPhone5,4,
  and iPad3,4. The remaining iPhone 5/5C and iPad 4 variants have experimental,
  hardware-untested support following firmware checks.
- Regular CoolBooter booted secondary iOS 6 on iPhone5,2 and iPad3,4.
- Removed development notices and the Automatic first boot questionnaire.
- Added optional startup diagnostic logging, local log paths, and support guidance.
- Preserved the tested restore payloads, system partition sizing, RAM option,
  IPSW reuse, progress displays, and existing host binaries and directory layout.
- Optional updates from this fork's GitHub releases. Declining an update never
  exits or blocks the script. No functionality is disabled. Offline operations
  remain accessible; operations requiring internet still try and fail without
  a connection. If an online feature fails while connected, accept an available
  update at launch: it may contain fixes for changes to external services.

Read the README warnings before restoring. First boot may take longer. Procyon
reports about 93% boot success on iPad 4 with iOS 10.3.2 or later; failed boot
attempts need a manual reboot. Comparable reliability to Socket is expected,
not independently measured. Do not use CoolBooter Untetherer or sideload/run
Socket on this installation. Linux support is untested but expected to work.

For pwnDFU retries, use the same Restore/Downgrade flow and choose Reuse IPSW.
Manual pwnDFU through Useful Utilities does not work with this custom flow.

The iOS 10 jailbreak integration supports Latest 10.3.4 only. SHSH jailbreak
routes are not supported by this release. See README.md for complete instructions,
credits, model status and issue reporting rules.

Download [Legacy-iOS-Kit-Custom-1.0.0.tar.gz](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/releases/download/v1.0.0/Legacy-iOS-Kit-Custom-1.0.0.tar.gz) and verify it with [SHA256SUMS](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/releases/download/v1.0.0/SHA256SUMS).
