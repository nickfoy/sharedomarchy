#!/usr/bin/env python3
"""Register Nick's FreeCAD Preference Pack and install the Omarchy launcher."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def desktop_quote(path):
    text = str(path).replace('%', '%%')
    for char in ('\\', '"', '`', '$'):
        text = text.replace(char, '\\' + char)
    return '"' + text + '"'


def manage(args):
    home = args.home.resolve()
    state_file = home / '.local/share/sharedomarchy-freecad/state.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else None
    if args.action == 'uninstall':
        if not state:
            print('No managed FreeCAD setup to remove.')
            return
        for target, record in state.items():
            path = Path(target)
            if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != record['sha']:
                raise RuntimeError(f'Preserving edited/missing file: {target}. Reconcile it before removal.')
        # Validate all backup reads before making any changes.
        originals = {target: Path(r['backup']).read_bytes() if r['backup'] else None
                     for target, r in state.items()}
        for target, original in originals.items():
            path = Path(target)
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)
                shutil.copystat(state[target]['backup'], path)
        state_file.unlink()
        print('Removed managed files and restored originals; preferences and backups retained.')
        return

    if args.home.resolve() != Path.home().resolve() and args.data_dir is None:
        raise RuntimeError('--home for another user requires --data-dir for offline staging.')
    data_dir = args.data_dir
    if data_dir is None:
        value = subprocess.check_output(['FreeCADCmd', '--get-config', 'UserAppData'], text=True).strip()
        data_dir = Path(value)
        if not data_dir.is_absolute():
            raise RuntimeError('Could not determine the FreeCAD user data directory.')
    pack_dir = data_dir.resolve() / 'Preference Packs/NickOmarchy'
    source = Path(__file__).resolve().parent
    template = args.desktop_template.read_text()
    wrapper = home / '.local/bin/freecad-omarchy'
    desktop, count = re.subn(r'^Exec=(?:FreeCAD|freecad|/usr/bin/FreeCAD)([^\n]*)$',
        lambda m: 'Exec=' + desktop_quote(wrapper) + m[1], template, flags=re.M)
    if count != 1:
        raise RuntimeError('Unexpected upstream desktop Exec; no files changed.')
    files = {
        wrapper: (source / 'launcher.py').read_bytes(),
        home / '.local/share/applications/org.freecad.FreeCAD.desktop': desktop.encode(),
        pack_dir / 'package.xml': (source / 'pack/package.xml').read_bytes(),
        pack_dir / 'LICENSE': (source.parent / 'LICENSE').read_bytes(),
        pack_dir / 'NickOmarchy/NickOmarchy.cfg': (source / 'pack/NickOmarchy/NickOmarchy.cfg').read_bytes(),
    }
    if state and set(state) != {str(p) for p in files}:
        raise RuntimeError('FreeCAD data location changed; uninstall the old registration before reinstalling.')
    for target in files:
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise RuntimeError(f'Refusing to replace a symlink or directory: {target}')
        if state and (not target.exists() or sha(target.read_bytes()) != state[str(target)]['sha']):
            raise RuntimeError(f'Preserving edited/missing file: {target}. Reconcile it before updating.')
    if not state:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        backup_dir = home / '.local/share/sharedomarchy-freecad/backups' / stamp
        backup_dir.mkdir(parents=True)
        state = {}
        for index, target in enumerate(files):
            backup = backup_dir / str(index) if target.exists() else None
            if backup:
                shutil.copy2(target, backup)
            state[str(target)] = {'backup': str(backup) if backup else None}
    for target, payload in files.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o755 if target == wrapper else 0o644)
        state[str(target)]['sha'] = sha(payload)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2) + '\n')
    print('Installed launcher and registered NickOmarchy. Apply it from FreeCAD Preferences when desired.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'uninstall'))
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--data-dir', type=Path, help='FreeCAD UserAppData directory; auto-detected by default')
    parser.add_argument('--desktop-template', type=Path,
                        default=Path('/usr/share/applications/org.freecad.FreeCAD.desktop'))
    manage(parser.parse_args())


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
