#!/usr/bin/env python3
"""Install/remove only the Fusion compatibility files and managed Lua import."""
import argparse
import ctypes.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

IMPORT = 'o.fusionWindows = require("hypr.fusion-windows")'
BLOCK = '-- BEGIN sharedomarchy fusion360\n' + IMPORT + '\n-- END sharedomarchy fusion360\n'
FILES = {
    'fusion-windows.lua': '.config/hypr/fusion-windows.lua',
    'opacity.py': '.local/share/fusion-window-compat/opacity.py',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def check_runtime():
    for cmd in ('hyprctl', 'python3', 'xprop'):
        if not shutil.which(cmd):
            raise RuntimeError(f'Missing {cmd}; see fusion360/README.md prerequisites.')
    for lib in ('X11', 'Xext'):
        if not ctypes.util.find_library(lib):
            raise RuntimeError(f'Missing lib{lib}; see prerequisites.')
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        raise RuntimeError('Run inside your Hyprland session, or stage files with --no-reload.')


def manage(action, home):
    config = home / '.config/hypr/hyprland.lua'
    state_path = home / '.local/share/fusion-window-compat/install-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if action == 'uninstall' and state is None:
        print('Nothing installed by this installer.')
        return
    if not config.is_file() or config.is_symlink():
        raise RuntimeError('Expected a regular ~/.config/hypr/hyprland.lua. Handle symlinked dotfiles manually.')
    content = config.read_text()
    if state:
        for relative, expected in state['installed_hashes'].items():
            path = home / relative
            if path.is_symlink() or digest(path) != expected:
                raise RuntimeError(f'{path} was edited or removed. Preserve/reconcile it before {action}.')
        if BLOCK not in content:
            raise RuntimeError('Managed Lua block was edited. Reconcile it before updating/removing.')
    if action == 'uninstall':
        # Read every backup before touching live files. Missing/unreadable
        # backups must leave a retryable installation, not a half-uninstall.
        originals = {relative: (Path(original).read_bytes() if original else None)
                     for relative, original in state['originals'].items()}
        for relative, original in state['originals'].items():
            target = home / relative
            if original:
                target.write_bytes(originals[relative])
                shutil.copystat(original, target)
            else:
                target.unlink()
        config.write_text(content.replace(BLOCK, state['previous_import'], 1))
        state_path.unlink()
        print('Removed managed installation; restored original files. Backups retained.')
        return

    source = Path(__file__).resolve().parent
    if not state:
        if 'sharedomarchy fusion360' in content:
            raise RuntimeError('Found a managed block without installation state; reconcile it first.')
        if any((home / relative).is_symlink() for relative in FILES.values()):
            raise RuntimeError('An existing payload is a symlink; handle that dotfile manually.')
        # Migrate the original workstation import without adding a second require.
        lines = content.splitlines(keepends=True)
        legacy = [line for line in lines if line.strip() == IMPORT]
        if len(legacy) > 1:
            raise RuntimeError('Multiple Fusion imports found; reconcile them first.')
        previous_import = legacy[0] if legacy else ''
        if previous_import:
            content = content.replace(previous_import, BLOCK, 1)
        else:
            if content and not content.endswith('\n'):
                raise RuntimeError('Config must end with a newline before appending the managed block.')
            content += BLOCK
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        backup = home / '.local/share/fusion-window-compat-backups' / stamp
        backup.mkdir(parents=True)
        shutil.copy2(config, backup / 'hyprland.lua')
        originals = {}
        for name, relative in FILES.items():
            target = home / relative
            originals[relative] = str(backup / name) if target.exists() else None
            if target.exists():
                shutil.copy2(target, backup / name)
        state = dict(originals=originals, previous_import=previous_import)

    installed_hashes = {}
    for name, relative in FILES.items():
        target = home / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, target)
        installed_hashes[relative] = digest(target)
    state['installed_hashes'] = installed_hashes
    state_path.write_text(json.dumps(state, indent=2) + '\n')
    config.write_text(content)
    print('Installed Fusion window compatibility. Original configuration backed up.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'uninstall'))
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--no-reload', action='store_true', help='Stage files without session/dependency checks or reload')
    args = parser.parse_args()
    if not args.no_reload:
        if args.home.resolve() != Path.home().resolve():
            parser.error('--home requires --no-reload when targeting another home')
        check_runtime()
    manage(args.action, args.home.resolve())
    if not args.no_reload:
        subprocess.run(['hyprctl', 'reload'], check=True)
        result = subprocess.run(['hyprctl', 'configerrors'], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            raise RuntimeError('Hyprland reported configuration errors:\n' + result.stdout)
        print('Hyprland reloaded without configuration errors.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
