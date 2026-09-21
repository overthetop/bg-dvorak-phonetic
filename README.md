# Bulgarian Dvorak Phonetic keyboard layout

This layout maps the physical keys of US Dvorak to Bulgarian Cyrillic. See the [Linux layout](linux/layout.jpg) and [macOS layout](mac-os/layout.jpg).

## Install on Ubuntu GNOME 24.04

Download an Ubuntu installer ZIP (version 1.2.0 or later) from [Releases](https://github.com/overthetop/bg-dvorak-phonetic/releases) and extract it. Open a terminal in the extracted folder and run:

```sh
./install.sh
```

Enter your administrator password if prompted. In **Settings > Keyboard > Input Sources**, add **Bulgarian (Dvorak phonetic)**. If the layout is not listed, sign out and back in, then try again. The installer supports both GNOME Wayland and GNOME X11 sessions; it does not restart your display manager.

To remove it, run `./uninstall.sh` from the extracted folder and remove the input source in Settings. An Ubuntu XKB package update may replace the system registry entry; rerun `./install.sh` if the layout disappears. If you previously followed the old manual instructions, remove those edits separately after confirming they are yours; the uninstaller only removes files and registration it owns.

## Install on macOS

Download a macOS installer ZIP (version 1.2.0 or later) from [Releases](https://github.com/overthetop/bg-dvorak-phonetic/releases) and extract it. Run `./install.command` in Terminal from the extracted folder, or double-click it in Finder. Then open **System Settings > Keyboard > Text Input > Edit > Add** and select **Bulgarian (Dvorak phonetic)**. Sign out and back in if it does not appear immediately.

Run `./uninstall.command` to remove the bundle, then remove the input source in Settings. Installation is for the current user and does not require administrator access.

## Platform verification

GitHub Actions checks the Ubuntu and macOS release archives and install lifecycle. On Ubuntu it queries GNOME's layout registry, checks the keymap advertised by a headless Wayland compositor, and verifies representative X11 mappings. On macOS it registers the installed input source and translates representative keys through the system keyboard API. These checks run without manual release steps; they do not simulate clicks in system Settings. Windows 11 support is planned; see the [Windows plan](docs/windows-11-plan.md).
