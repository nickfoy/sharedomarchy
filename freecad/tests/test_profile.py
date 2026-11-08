import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1] / 'export.py'

class ProfileTests(unittest.TestCase):
    def test_export_keeps_portable_preferences_and_excludes_private_state(self):
        self.assertTrue(MODULE.exists(), 'portable exporter is missing')
        spec = importlib.util.spec_from_file_location('profile_export', MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = ET.fromstring('''<FCParameters><FCParamGroup Name="Root"><FCParamGroup Name="BaseApp">
        <FCParamGroup Name="Preferences">
          <FCParamGroup Name="General"><FCText Name="AutoloadModule">PartDesignWorkbench</FCText><FCText Name="FileOpenSavePath">/home/private/designs</FCText></FCParamGroup>
          <FCParamGroup Name="Units"><FCInt Name="UserSchema" Value="0"/></FCParamGroup>
          <FCParamGroup Name="View"><FCText Name="NavigationStyle">Gui::CADNavigationStyle</FCText><FCUInt Name="BackgroundColor" Value="42"/></FCParamGroup>
          <FCParamGroup Name="MainWindow"><FCText Name="Theme">FreeCAD Dark</FCText><FCText Name="Geometry">-3072 0 1470 818</FCText><FCText Name="StyleSheet">/home/private/theme.qss</FCText></FCParamGroup>
          <FCParamGroup Name="RecentFiles"><FCText Name="MRU0">/home/private/secret.FCStd</FCText></FCParamGroup>
          <FCParamGroup Name="TreeView"><FCInt Name="FontSize" Value="11"/><FCInt Name="ColumnSize1" Value="260"/></FCParamGroup>
        </FCParamGroup>
        <FCParamGroup Name="MainWindow"><FCParamGroup Name="Toolbars"><FCBool Name="File" Value="1"/></FCParamGroup></FCParamGroup>
        </FCParamGroup></FCParamGroup></FCParameters>''')
        result = ET.tostring(module.portable_profile(source), encoding='unicode')
        for value in ['AutoloadModule','UserSchema','NavigationStyle','BackgroundColor','Theme','FontSize','Toolbars']:
            self.assertIn(value, result)
        for value in ['/home/', 'FileOpenSavePath','Geometry','StyleSheet','RecentFiles','ColumnSize1']:
            self.assertNotIn(value, result)

if __name__ == '__main__':
    unittest.main()
