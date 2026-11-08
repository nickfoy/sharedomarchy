import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

INSTALLER = Path(__file__).resolve().parents[1] / 'install.py'

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freecad laptop's home ")
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.data = self.home / '.local/share/FreeCAD/v1-1'
        self.template = self.home / 'upstream.desktop'
        self.template.write_text('[Desktop Entry]\nName=FreeCAD\nExec=FreeCAD - --single-instance %F\n')
        self.wrapper = self.home / '.local/bin/freecad-omarchy'
        self.wrapper.parent.mkdir(parents=True)
        self.wrapper.write_text('# preexisting launcher\n')
        self.config = self.home / '.config/FreeCAD/v1-1/user.cfg'
        self.config.parent.mkdir(parents=True)
        self.config.write_text('private settings must stay unchanged')

    def run_action(self, action, success=True):
        result = subprocess.run([sys.executable, str(INSTALLER), action, '--home',str(self.home),
            '--data-dir',str(self.data),'--desktop-template',str(self.template)],capture_output=True,text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)

    def test_roundtrip_preserves_live_preferences_and_previous_launcher(self):
        self.run_action('install')
        first = self.wrapper.read_bytes()
        self.run_action('install')
        self.assertEqual(first,self.wrapper.read_bytes())
        pack=self.data/'Preference Packs/NickOmarchy/NickOmarchy/NickOmarchy.cfg'
        self.assertTrue(pack.exists())
        desktop=self.home/'.local/share/applications/org.freecad.FreeCAD.desktop'
        self.assertIn('"'+str(self.wrapper)+'" - --single-instance %F',desktop.read_text())
        self.assertEqual(self.config.read_text(),'private settings must stay unchanged')
        self.run_action('uninstall')
        self.assertEqual(self.wrapper.read_text(),'# preexisting launcher\n')
        self.assertFalse(pack.exists())
        self.assertFalse(desktop.exists())
        self.run_action('uninstall')

    def test_edited_payload_is_preserved(self):
        self.run_action('install')
        self.wrapper.write_text('# later edits\n')
        self.run_action('uninstall',success=False)
        self.assertEqual(self.wrapper.read_text(),'# later edits\n')

    def test_missing_backup_prevents_partial_uninstall(self):
        self.run_action('install')
        state=json.loads((self.home/'.local/share/sharedomarchy-freecad/state.json').read_text())
        backup=next(v['backup'] for v in state.values() if v['backup'])
        Path(backup).unlink()
        previous=self.wrapper.read_bytes()
        self.run_action('uninstall',success=False)
        self.assertEqual(self.wrapper.read_bytes(),previous)

if __name__ == '__main__': unittest.main()
