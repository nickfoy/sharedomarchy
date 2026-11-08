import pathlib
import json
import subprocess
import sys
import tempfile
import unittest

INSTALLER = pathlib.Path(__file__).resolve().parents[1] / 'install.py'
IMPORT = 'o.fusionWindows = require("hypr.fusion-windows")'


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='fusion home ')
        self.addCleanup(self.tmp.cleanup)
        self.home = pathlib.Path(self.tmp.name)
        self.config = self.home / '.config/hypr/hyprland.lua'
        self.config.parent.mkdir(parents=True)
        self.config.write_text('-- my settings\n')
        self.module = self.config.with_name('fusion-windows.lua')
        self.helper = self.home / '.local/share/fusion-window-compat/opacity.py'

    def run_installer(self, action='install', success=True):
        result = subprocess.run([sys.executable, str(INSTALLER), action,
                                 '--home', str(self.home), '--no-reload'],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_install_reinstall_and_uninstall_preserve_unrelated_edits(self):
        self.run_installer()
        self.assertTrue(self.module.exists())
        self.assertTrue(self.helper.exists())
        first = self.config.read_text()
        self.run_installer()
        self.assertEqual(first, self.config.read_text())
        self.assertEqual(first.count(IMPORT), 1)
        self.config.write_text(first + '-- added later\n')
        self.run_installer('uninstall')
        self.assertEqual(self.config.read_text(), '-- my settings\n-- added later\n')
        self.assertFalse(self.module.exists())
        self.assertFalse(self.helper.exists())
        self.run_installer('uninstall')

    def test_existing_fix_is_restored_on_uninstall(self):
        self.config.write_text('-- old config\n' + IMPORT + '\n')
        self.module.write_text('-- old module\n')
        self.helper.parent.mkdir(parents=True)
        self.helper.write_text('# old helper\n')
        original_config = self.config.read_bytes()
        self.run_installer()
        self.assertEqual(self.config.read_text().count(IMPORT), 1)
        self.run_installer('uninstall')
        self.assertEqual(self.config.read_bytes(), original_config)
        self.assertEqual(self.module.read_text(), '-- old module\n')
        self.assertEqual(self.helper.read_text(), '# old helper\n')

    def test_uninstall_refuses_to_discard_local_payload_changes(self):
        self.run_installer()
        self.module.write_text('-- edited\n')
        config = self.config.read_bytes()
        self.run_installer('uninstall', success=False)
        self.assertEqual(self.module.read_text(), '-- edited\n')
        self.assertEqual(self.config.read_bytes(), config)

    def test_missing_hyprland_config_is_rejected_without_installing(self):
        self.config.unlink()
        self.run_installer(success=False)
        self.assertFalse(self.module.exists())
        self.assertFalse(self.helper.exists())

    def test_missing_original_backup_leaves_installation_unchanged(self):
        self.module.write_text('-- original\n')
        self.run_installer()
        state_path = self.home / '.local/share/fusion-window-compat/install-state.json'
        state = json.loads(state_path.read_text())
        pathlib.Path(state['originals']['.config/hypr/fusion-windows.lua']).unlink()
        config, module = self.config.read_bytes(), self.module.read_bytes()
        self.run_installer('uninstall', success=False)
        self.assertEqual(self.config.read_bytes(), config)
        self.assertEqual(self.module.read_bytes(), module)
        self.assertTrue(state_path.exists())


if __name__ == '__main__':
    unittest.main()
