"""Run with FreeCADCmd -u <temporary-user.cfg> freecad/tests/check_freecad.py.

Copy the pack CFG to the temporary user.cfg first; this only reads it.
"""
from pathlib import Path
import FreeCAD as App

profile = Path(__file__).resolve().parents[1] / 'pack/NickOmarchy/NickOmarchy.cfg'
prefs = App.ParamGet('User parameter:BaseApp/Preferences')
assert prefs.GetGroup('General').GetString('AutoloadModule') == 'PartDesignWorkbench'
assert prefs.GetGroup('Units').GetInt('UserSchema', -1) == 0
assert prefs.GetGroup('View').GetString('NavigationStyle') == 'Gui::CADNavigationStyle'
assert prefs.GetGroup('MainWindow').GetString('Theme') == 'FreeCAD Dark'
assert prefs.GetGroup('General').GetString('FileOpenSavePath') == ''
print('PROFILE_LOAD_PASSED', '.'.join(App.Version()[:3]))
