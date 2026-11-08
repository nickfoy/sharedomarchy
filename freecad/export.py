#!/usr/bin/env python3
"""Export selected saved FreeCAD preferences; never copy an entire user.cfg."""
import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET

# Unlisted groups and strings stay private. Numeric appearance values have no
# file paths, but geometry/column widths are intentionally not in these groups.
NUMERIC_GROUPS = {'View', 'Editor', 'Themes', 'OutputWindow', 'NaviCube'}
KEYS = {
    'General': {'AutoloadModule', 'FontSize'},
    'Units': {'UserSchema', 'Decimals'},
    'View': {'NavigationStyle'},
    'TreeView': {'FontSize', 'ItemBackgroundPadding', 'TreeActiveColor', 'TreeEditColor'},
    'MainWindow': {'Theme', 'QtStyle', 'StyleSheet', 'OverlayActiveStyleSheet',
                   'InputHintEnabled', 'QuickMeasureEnabled', 'StatusBar'},
    'Editor': {'Font'},
}


def portable_profile(source):
    result = ET.Element('FCParameters')
    root = ET.SubElement(result, 'FCParamGroup', Name='Root')
    base = ET.SubElement(root, 'FCParamGroup', Name='BaseApp')
    prefs = ET.SubElement(base, 'FCParamGroup', Name='Preferences')
    src_base = source.find("./FCParamGroup[@Name='Root']/FCParamGroup[@Name='BaseApp']")
    if src_base is None:
        raise ValueError('Not a FreeCAD user.cfg: missing Root/BaseApp')
    src_prefs = src_base.find("FCParamGroup[@Name='Preferences']")
    if src_prefs is None:
        raise ValueError('Missing Preferences group')
    count = 0
    for group in src_prefs:
        name = group.get('Name')
        selected = []
        for entry in group:
            key = entry.get('Name', '')
            allowed = key in KEYS.get(name, set())
            allowed |= name in NUMERIC_GROUPS and entry.tag in {'FCInt', 'FCUInt', 'FCFloat', 'FCBool'}
            if not allowed or entry.tag == 'FCParamGroup':
                continue
            if entry.tag == 'FCText':
                text = entry.text or ''
                if any(token in text for token in ('/', '\\', ':')) and key != 'NavigationStyle':
                    continue
            selected.append(copy.deepcopy(entry))
        if selected:
            dest = ET.SubElement(prefs, 'FCParamGroup', Name=name)
            dest.extend(selected)
            count += len(selected)
    # Visibility toggles are portable; serialized Qt layout and window positions are not.
    toolbars = src_base.find("FCParamGroup[@Name='MainWindow']/FCParamGroup[@Name='Toolbars']")
    if toolbars is not None:
        dest = ET.SubElement(ET.SubElement(base, 'FCParamGroup', Name='MainWindow'), 'FCParamGroup', Name='Toolbars')
        dest.extend(copy.deepcopy(e) for e in toolbars if e.tag == 'FCBool')
    if not count:
        raise ValueError('No supported preferences found')
    ET.indent(result, space='  ')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Saved user.cfg; close FreeCAD first to flush changes')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'pack/NickOmarchy/NickOmarchy.cfg')
    args = parser.parse_args()
    result = portable_profile(ET.parse(args.source).getroot())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(result).write(args.output, encoding='UTF-8', xml_declaration=True)
    print(f'Exported portable baseline to {args.output}')


if __name__ == '__main__':
    main()
