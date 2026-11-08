import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'launcher.py'

class LauncherTests(unittest.TestCase):
    def run_launcher(self, scale, existing=None):
        env = {} if existing is None else {'QT_FONT_DPI':existing}
        captured = {}
        def execute(binary, args):
            captured.update(binary=binary,args=args,dpi=os.environ.get('QT_FONT_DPI'))
        with patch.dict(os.environ,env,clear=True), patch('subprocess.check_output',return_value=scale), patch('os.execv',side_effect=execute), patch('sys.argv',[str(SCRIPT),'--single-instance','a part.FCStd']):
            runpy.run_path(str(SCRIPT),run_name='__main__')
        return captured

    def test_omarchy_scale_and_filename_are_forwarded(self):
        result=self.run_launcher('0.8182\n')
        self.assertEqual(result['dpi'],'79')
        self.assertEqual(result['args'],['/usr/bin/FreeCAD','--single-instance','a part.FCStd'])

    def test_explicit_qt_override_is_preserved(self):
        self.assertEqual(self.run_launcher('0.8182','88')['dpi'],'88')

    def test_invalid_scale_uses_qt_default(self):
        for invalid in ['nan','garbage','0','999']:
            with self.subTest(invalid=invalid):
                self.assertIsNone(self.run_launcher(invalid)['dpi'])

if __name__ == '__main__': unittest.main()
