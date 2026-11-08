# Fusion 360 window compatibility for Omarchy

This packages the workaround tested on Nick's laptop on November 8, 2026. It keeps Fusion's auxiliary windows with their main frame, prevents a blank MessageTray from covering other applications, restores palette transparency, and lets modal dialogs receive input.

## Install on a new laptop

Install Fusion separately first. From the running Omarchy/Hyprland session:

```bash
git clone https://github.com/nickfoy/sharedomarchy.git
cd sharedomarchy
python3 fusion360/install.py install
```

Prerequisites:

- Omarchy's **Lua-based Hyprland configuration**, including the `o.window` helper. This package does not support older `.conf` configurations.
- Python 3.10+, `hyprctl`, `xprop`, `libX11`, and `libXext`.
- Fusion running under Wine's X11 driver / XWayland. Native Wine Wayland mode is outside the tested scope.

On Arch, if these dependencies are missing:

```bash
sudo pacman -S --needed python xorg-xprop libx11 libxext
```

The installer copies the two runtime files, backs up any originals, adds one marked import to `~/.config/hypr/hyprland.lua`, and reloads Hyprland. It checks `hyprctl configerrors` afterward. It requires no root access and does not restart Fusion. Running it again updates the package without duplicating the import or replacing the original backup.

The module locates Fusion's main window by process ID and title and follows its workspace. It has no fixed workspace number, display ID, username, Wine prefix, or Fusion version path.

For offline staging, use `--no-reload`. This skips session/dependency checks and reload; apply and validate manually when inside Hyprland. `--home /path/to/home --no-reload` supports staging another home directory. Symlinked managed files are rejected; dotfile-manager users should integrate the two payloads and Lua import through their own manager.

## What is installed

| File | Purpose |
| --- | --- |
| `~/.config/hypr/fusion-windows.lua` | Workspace ownership, MessageTray rules and window event hooks |
| `~/.local/share/fusion-window-compat/opacity.py` | Scalar opacity/input repair and ARGB palette refresh |
| `~/.local/share/fusion-window-compat/install-state.json` | Original-file locations and installed hashes used for safe updates/removal |
| `~/.local/share/fusion-window-compat-backups/<timestamp>/` | Original runtime files and Hyprland config snapshot |

Only `Msg:QTView:(number)MessageTray` is hidden, on `special:fusion-helpers`. The Browser and other useful palettes remain visible. The helper matches X11 windows by process, title, dimensions and monitor scale; ambiguous matches are left untouched.

Fusion's modal dimmer advertises `_NET_WM_WINDOW_OPACITY`, which the tested Hyprland XWayland implementation does not honor. The helper applies that value to Hyprland's active/inactive/fullscreen opacity, empties the dimmer's input region and raises the actual dialog above it. This keeps the dimmer from swallowing clicks.

For palettes without scalar opacity, a brief X11 bounding-shape change followed by restoring the full shape refreshes XWayland's ARGB presentation. No persistent crop or per-pixel mask is left behind, so newly expanded Browser rows can still draw. This is a compatibility workaround, not an upstream compositor or Wine patch.

## Tested environment and limits

- Hyprland **0.56.2**, Omarchy Lua configuration.
- Lolig4 `fusion-wine-build`, **Wine 11.17**, runner release **Version_1**.
- Fusion Qt **6.8.3**, XWayland, display scale **1.25**.
- Live checks: main-window resize/redraw, black MessageTray suppression, Browser transparency, modal opacity and mouse input, utility placement with the parent window. Nick confirmed the resulting UI worked.

Different Wine/Fusion/Hyprland versions and multi-monitor layouts still need live verification. Changes upstream may make this workaround unnecessary. A new laptop must be checked rather than assumed equivalent. The pure installer/Lua tests do not simulate Wine's rendering or an actual compositor.

## Verify after installing

1. Run `hyprctl configerrors`; expect no errors.
2. Open a design. Resize Fusion with **Super + right-drag**; its canvas should redraw.
3. Expand and collapse the Browser tree. The unused area should show the canvas, not black, and newly shown rows should remain visible and clickable.
4. Open “What do you want to create?” or Preferences. Verify buttons and options respond, and dismiss with Cancel.
5. Switch workspaces while Fusion is open. Its utilities should stay with the main window; a black MessageTray should not cover other apps.

If rendering regresses after an upstream update, uninstall and compare before changing Wine or the compositor.

## Update and uninstall

```bash
git pull --ff-only
python3 fusion360/install.py install
# To remove this package later:
python3 fusion360/install.py uninstall
```

Uninstall removes only the managed import block and restores pre-install runtime files, or removes them if there were none. It preserves unrelated config edits and retains timestamped backups. If you had the original local fix, its original import/files are restored. If installed payloads or the import block were edited afterward, installation/removal stops instead of discarding those edits; reconcile or back up those files first.

If a reload reports errors, inspect `hyprctl configerrors`. The full original config snapshot is retained in the backup directory; do not overwrite newer unrelated edits with that snapshot blindly.

## Scoped development checks

From the repository root:

```bash
python3 fusion360/tests/test_install.py
lua fusion360/tests/windows.test.lua
luac -p fusion360/fusion-windows.lua
```

Installer tests use temporary home directories with spaces, cover reinstallation and removal, restore previous fixes, preserve unrelated edits and refuse to discard edited payloads. Lua tests cover same-process ownership, separate Fusion instances, no workspace focus stealing, and shell quoting. GitHub Actions also checks Python syntax. Live visual/input verification remains necessary on the destination laptop.
