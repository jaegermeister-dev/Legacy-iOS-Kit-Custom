# Legacy iOS Kit (Custom)

Restore an iPhone 5, iPhone 5C, or iPad 4 to **iOS 10.3.4 (14G61), already jailbroken and untethered**, using Socket's jailbreak assets, Zebra, and Procyon. Installation completes during the restore: no sideloading, second DFU boot, or installer app is required.

This is a separately maintained fork of [LukeZGD's Legacy iOS Kit](https://github.com/LukeZGD/Legacy-iOS-Kit). Original Kit features and credits are retained. **Report issues to this fork by default. Contact the official developer only after reproducing the same issue with the official Kit.** Issues specific to this fork belong here.

## Download and launch

Download the [1.0.0 archive](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/releases/download/v1.0.0/Legacy-iOS-Kit-Custom-1.0.0.tar.gz) from the [**Latest release**](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/releases/latest), also shown in the Releases section on the right. [SHA-256 checksum](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/releases/download/v1.0.0/SHA256SUMS). Extract the complete folder, open Terminal there, and run:

```sh
./restore.sh
```

Keep `restore.sh`, `bin`, and `resources` together. Do not replace them with files from another Kit version. See [STANDALONE.txt](STANDALONE.txt) for local usage details and the original [host setup instructions](https://github.com/LukeZGD/Legacy-iOS-Kit/wiki/How-to-Use) for dependencies.

**macOS and Linux are supported host platforms. This fork's Linux support has not been tested, but is expected to work.** If a problem occurs, enable diagnostic logging at startup and include the saved log in an issue here. The original macOS, Linux x86_64, and Linux ARM64 tools remain in their original separate directories, unchanged. Both platforms package the same device-side restore components; Linux users do not need Xcode.

## iOS 10 restore

1. Back up anything you want to keep. **Start Restore erases the device.**
2. Launch the script and choose whether to enable diagnostic logging.
3. Choose **Restore/Downgrade → Latest iOS (10.3.4)** and select the stock, unmodified IPSW for your device family.
4. Choose **Start Restore**, read the jailbreak warnings, and enable the jailbreak option. Choosing No performs a normal restore.
5. Choose whether to reuse a compatible prepared IPSW or build a new one. Fresh creation also offers the RAM option. Follow the restore flow's DFU instructions.
6. After restoration, let the device boot and complete Setup normally. Zebra should be on the Home Screen. **The first boot may take longer than subsequent boots. Allow time for it to finish.**

The iOS 10 jailbreak integration supports **Latest iOS 10.3.4 (14G61)**. The option is shown for iOS 10 SHSH selections, but enabling it on a SHSH or other firmware route is blocked before device preparation. Those jailbreak routes are not supported in this release; existing normal SHSH restore features remain available.

**Do not enter pwnDFU manually through Useful Utilities for this custom restore: that route does not work with this flow.** If pwnDFU fails after IPSW creation, relaunch the script, return through the same Restore/Downgrade menu, select **Reuse IPSW**, and follow that flow's DFU instructions. A compatible image can be reused without rebuilding it.

## Changes from official Legacy iOS Kit

- Added the iOS 10.3.4 untethered jailbreak restore option using Socket assets, Zebra, and Procyon.
- Added custom image creation with RAM support, compatible-image reuse, progress displays, and space checks.
- Added optional startup diagnostic transcripts and restore evidence for troubleshooting.
- Added model test status, untether reliability, first-boot, and retry guidance.
- Replaced forced upstream updates with optional updates from this fork's releases. Declining or being offline keeps the script usable and does not disable any feature.
- Added fork-specific support routing and release documentation. Existing macOS and Linux host binaries and their folder layout are unchanged in 1.0.0.

## Device support

| Device | Identifier | Board | Test status |
| --- | --- | --- | --- |
| iPhone 5 GSM | iPhone5,1 | n41ap | Experimental; firmware checked, hardware untested |
| iPhone 5 Global | iPhone5,2 | n42ap | Restore, reboot, Zebra and tweak injection tested |
| iPhone 5C GSM | iPhone5,3 | n48ap | Experimental; firmware checked, hardware untested |
| iPhone 5C Global | iPhone5,4 | n49ap | Restore, reboot, Zebra and tweak injection tested |
| iPad 4 Wi-Fi | iPad3,4 | p101ap | Restore, reboot, Zebra and tweak injection tested |
| iPad 4 GSM | iPad3,5 | p102ap | Experimental; firmware checked, hardware untested |
| iPad 4 Global | iPad3,6 | p103ap | Experimental; firmware checked, hardware untested |

These hardware results are from manual testing on macOS. Regular CoolBooter installed and booted secondary iOS 6 on iPhone5,2 and iPad3,4; primary iOS 10 also booted with Zebra and tweaks after CoolBooter installation. This is not a claim about every secondary firmware or untested model.

## Untether guidance

- **iPad 4:** Procyon documents a base boot success rate of about **93% on iOS 10.3.2 and later**. Approximately 7% of boot attempts may not reach the Home Screen; manually reboot and try again. This applies to boot attempts, including later boots, rather than a percentage of devices or restores. [Procyon information](https://github.com/staturnzz/procyon#information)
- Socket leaves the untether disabled by default on affected iPads. **Enabling this fork's jailbreak option installs the untether on those iPads.** Socket's linked installation guide says that particular reliability issue does not affect the iPhone 5 or 5C. [Socket installation guidance](https://ios.cfw.guide/installing-socket/)
- This uses the same Procyon untether as Socket. Comparable boot reliability is expected for the same hardware and firmware, but identical rates have not been independently measured in this fork. Keep backups and exercise care on all supported devices.
- **Do not install CoolBooter Untetherer.** Procyon identifies it as incompatible and says it causes a blank screen. This is separate from the regular CoolBooter app tested above. [Procyon information](https://github.com/staturnzz/procyon#information)
- **Do not sideload or run the Socket app on this installation.** It may conflict with the installed assets. Socket app compatibility is not supported by this method. If you want Socket's option to boot without the jailbreak, restore fresh to stock iOS and use Socket normally.

## Diagnostics and support

At startup, choose whether to enable a local Terminal transcript. The script displays its path under `saved/diagnostics` and again when it exits. Nothing is uploaded automatically. Review logs before sharing: device identifiers and local filesystem paths can appear in output. Keystrokes are not recorded.

Choosing No leaves the normal workflow available. Essential restore logs and image-reuse records remain under `saved/ios10`; these are separate from the optional full-session transcript. If a DCSD cable is available, the existing restore flow can also save a serial trace. No special cable is required to restore.

Report the version, host OS, device model, operation, and error, together with the diagnostic log where available. Use [**this repository's Issues**](https://github.com/jaegermeister-dev/Legacy-iOS-Kit-Custom/issues) by default. Only report to LukeZGD after reproducing the problem in the official Kit. Do not upload IPSWs or the entire `saved` directory as an issue attachment.

## Updates and internet access

**This fork never forces updates or closes because an update is declined.** At startup it checks this fork's latest GitHub release and offers to download and install a newer version. Choose No to keep using the current version. A failed check, private repository, or lack of internet does not block startup. Use `--no-update-check` to skip the check. Declining an update or skipping the startup connectivity check does not disable internet features.

Accepted updates download this fork's release archive, check its SHA-256 checksum, and preserve saved IPSWs, logs, and other user files. Previous program files are retained under `saved/updates`. Restart the script after a successful update. Source checkouts are updated manually to preserve local changes.

Features that may need internet include firmware and tool downloads, Apple signing requests, activation, and online package repositories. Locally available operations remain accessible offline, but a restore can still require a current signing response. **No functionality is disabled** by declining an update or being offline. Features requiring an internet connection will still attempt to run and fail if that connection is unavailable. If an internet-dependent feature fails while connected, accept an available update offered at launch; it may account for changes to Apple or other services. Check the release notes for those fixes.

## Source, licenses, and credits

Version 1.0.0 is based on upstream commit `23622f8fe72c09952089d5145a7b008cfcc90d9b`, with custom source changes dated 2026-11-01. The source and existing license notices are included. See [LICENSE](LICENSE), [binary credits](bin/README.md), and the retained [upstream project README](UPSTREAM-README.md).

Credit to **LukeZGD** and Legacy iOS Kit's contributors, **staturnz** for [Socket](https://github.com/staturnzz/socket) and [Procyon](https://github.com/staturnzz/procyon), [Zebra](https://github.com/zbrateam/Zebra), and the authors of the bundled tools and jailbreak components. This fork integrates their work; it does not claim authorship of their exploits.
