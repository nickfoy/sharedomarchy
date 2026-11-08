# Nick's FreeCAD setup

A portable **NickOmarchy Preference Pack**, the Omarchy text-scaling launcher, and a home for future modeling macros. Baseline captured from saved FreeCAD 1.1.4 settings on November 8, 2026.

## New laptop

Install native FreeCAD on Omarchy/Arch first, then register this setup:

```bash
omarchy pkg add freecad
git clone https://github.com/nickfoy/sharedomarchy.git
cd sharedomarchy
python3 freecad/install.py install
```

Restart FreeCAD from its app-launcher entry when convenient. In **Edit → Preferences → General**, find **NickOmarchy** and apply it explicitly to restore the baseline. Installing this package registers it but does **not** overwrite your live preferences or close your documents. FreeCAD may request a restart after applying a pack.

The installer queries `FreeCADCmd --get-config UserAppData` to find the version-specific data directory. On the tested system it is `~/.local/share/FreeCAD/v1-1/`. Runtime prerequisites are native `/usr/bin/FreeCAD`, `FreeCADCmd`, Python 3.10+, `gsettings`, and the Arch desktop entry `/usr/share/applications/org.freecad.FreeCAD.desktop`.

## Baseline contents

- Part Design startup workbench; Standard millimeter/kilogram/second units.
- CAD navigation style.
- FreeCAD Dark theme, built-in stylesheet names and view/background/selection colors.
- Saved editor/console appearance, tree font/padding and navigation-cube appearance where present.
- Toolbar visibility. Screen coordinates, window dimensions and serialized Qt layouts are excluded.

The exporter uses a defined set of preference groups/keys. It excludes recent files/macros, document paths, plugin paths, language, account data, unknown text preferences and absolute stylesheet paths. A future preference outside this set must be deliberately added to `export.py` and its tests. It does not copy all of `user.cfg`.

**Font scaling is independent of the pack.** The launcher reads `org.gnome.desktop.interface text-scaling-factor` at each start and supplies `QT_FONT_DPI=round(96×scale)`. On the tested desktop the factor was `0.8182`, producing `79` DPI instead of Qt's default `96`. An explicit existing `QT_FONT_DPI` is respected. If settings are unavailable or invalid it falls back to Qt's default. The default GTK font family still comes from the desktop. Font changes require restarting FreeCAD; this is not a live settings watcher. Launching `/usr/bin/FreeCAD` directly bypasses the wrapper.

## Save future adjustments

1. Make your FreeCAD changes, save your documents, then close FreeCAD so its current preferences are written.
2. Export selected saved preferences into the version-controlled pack:

   ```bash
   cd ~/Work/sharedomarchy   # or wherever you cloned it
   python3 freecad/export.py --source ~/.config/FreeCAD/v1-1/user.cfg
   git diff -- freecad/pack/NickOmarchy/NickOmarchy.cfg
   ```

   Adjust the `v1-1` path for a future FreeCAD version. Inspect the diff before publishing, especially if you extend the export rules.
3. Run the scoped tests below, then commit/push the pack changes.
4. Run `python3 freecad/install.py install` to update the registered pack. Applying the pack is optional on the laptop where you just made the settings; those preferences are already active there.

You can also use FreeCAD's **Save new…** Preference Pack UI to capture selected preferences. Review any resulting CFG before adding it to this public repository. Keep full `user.cfg` backups local/private because they can contain recent file paths and other personal state.

## Files and removal

The installer backs up and manages these files only:

- `~/.local/bin/freecad-omarchy`
- `~/.local/share/applications/org.freecad.FreeCAD.desktop`
- `<FreeCAD UserAppData>/Preference Packs/NickOmarchy/package.xml`
- `<FreeCAD UserAppData>/Preference Packs/NickOmarchy/LICENSE`
- `<FreeCAD UserAppData>/Preference Packs/NickOmarchy/NickOmarchy/NickOmarchy.cfg`

State and retained backups are under `~/.local/share/sharedomarchy-freecad/`. Reinstalling preserves the original backup; local modifications to managed files cause a refusal rather than being discarded. Missing backups prevent removal before any managed files are changed. Symlinked managed files are rejected; integrate them through your dotfile manager instead.

```bash
python3 freecad/install.py uninstall
```

Uninstall restores pre-existing files or removes files the package created. It leaves your actual FreeCAD preferences and documents unchanged. If you applied NickOmarchy and want to undo those preferences, restore the timestamped backup FreeCAD made when applying the pack (under `SavedPreferencePacks/Backups` in UserAppData). FreeCAD normally retains these for one week; keep a separate local backup for longer retention. Uninstalling the package does not undo applied preferences.

For offline staging/tests, `--home /target/home --data-dir /target/freecad-data --desktop-template /path/to/upstream.desktop` avoids querying a running installation. After a FreeCAD upgrade changes the data directory, uninstall the old registration before installing to the new version.

## Macros

`macros/` is reserved for reusable modeling automation. No startup/pre/post macro is installed: restoring preferences should not run modeling code.

## Validation

From the repo root:

```bash
python3 freecad/tests/test_profile.py
python3 freecad/tests/test_install.py
python3 freecad/tests/test_launcher.py
```

The pack was also loaded by FreeCADCmd **1.1.4** using an isolated temporary user configuration, with the live settings hash verified unchanged. The app and font launcher were commissioned on Hyprland **0.56.2**, native Wayland, scale **1.25**. That commissioning included editable parameter recompute, save/reopen, STEP round-trip, watertight STL export and GUI resize/redraw. Test models/screenshots and full workstation settings are not included here.

On a new laptop, verify launcher startup, text sizing, pack appearance in Preferences, apply/restart, toolbar/navigation settings, and model save/reopen. Unit tests do not simulate Qt, the Preference Pack selection UI or a compositor.
