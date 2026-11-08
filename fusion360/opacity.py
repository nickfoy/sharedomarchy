#!/usr/bin/env python3
"""Refresh Fusion's ARGB palettes and bridge scalar opacity to Hyprland.

Hyprland 0.56 ignores _NET_WM_WINDOW_OPACITY. Only touch an unambiguously
matched Fusion utility window, preserving its requested opacity or alpha.
"""
import json
import ctypes
import re
import subprocess
import sys


def output(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refresh_argb_window(xid, width, height):
    """Force XWayland to refresh its ARGB shape, then restore the full shape.

    This is a transient redraw, not a crop: new Browser rows remain drawable.
    """
    class Rect(ctypes.Structure):
        _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                    ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]
    x11 = ctypes.CDLL("libX11.so.6")
    shape = ctypes.CDLL("libXext.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    shape.XShapeCombineRectangles.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int]
    shape.XShapeCombineMask.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int]
    display = x11.XOpenDisplay(None)
    if not display:
        return
    rects = (Rect * 2)(Rect(0, 0, width - 1, height), Rect(width - 1, 0, 1, height - 1))
    shape.XShapeCombineRectangles(display, int(xid, 16), 0, 0, 0, rects, 2, 0, 0)
    x11.XSync(display, 0)
    shape.XShapeCombineMask(display, int(xid, 16), 0, 0, 0, 0, 0)
    x11.XCloseDisplay(display)


def main(address):
    if not re.fullmatch(r"0x[0-9a-f]+", address):
        return
    clients = json.loads(output("hyprctl", "clients", "-j"))
    target = next((c for c in clients if c["address"] == address), None)
    if not target or target["class"] != "fusion360.exe" or target["title"] != "Fusion360":
        return
    monitors = json.loads(output("hyprctl", "monitors", "-j"))
    scale = next(m["scale"] for m in monitors if m["id"] == target["monitor"])
    matches = []
    for xid in re.findall(r"0x[0-9a-f]+", output("xprop", "-root", "_NET_CLIENT_LIST")):
        try:
            props = output("xprop", "-id", xid, "WM_NAME", "_NET_WM_PID",
                           "WM_NORMAL_HINTS", "_NET_WM_WINDOW_OPACITY")
        except subprocess.CalledProcessError:
            continue  # A dialog may have closed between the two queries.
        pid = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", props)
        size = re.search(r"minimum size: (\d+) by (\d+)", props)
        alpha = re.search(r"_NET_WM_WINDOW_OPACITY\(CARDINAL\) = (\d+)", props)
        if not pid or int(pid[1]) != target["pid"] or not size:
            continue
        if 'WM_NAME(STRING) = "Fusion360"' not in props:
            continue
        if any(abs(int(size[i + 1]) / scale - target["size"][i]) > 2 for i in range(2)):
            continue
        matches.append((xid, int(alpha[1]) / 0xffffffff if alpha else None,
                        int(size[1]), int(size[2])))
    if len(matches) != 1:
        return  # Never guess between palettes with the same title.
    xid, alpha, width, height = matches[0]
    if alpha is None:
        refresh_argb_window(xid, width, height)
        return
    value = str(alpha)
    for prop in ("opacity", "opacity_inactive", "opacity_fullscreen"):
        code = 'hl.dsp.window.set_prop({window="address:%s",prop="%s",value="%s"})' % (address, prop, value)
        output("hyprctl", "dispatch", code)
    # This scalar-alpha window is Fusion's modal scrim, not a palette. Wine
    # maps it above its dialog; it must never intercept the dialog's input.
    x11 = ctypes.CDLL("libX11.so.6")
    shape = ctypes.CDLL("libXext.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    shape.XShapeCombineRectangles.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int]
    display = x11.XOpenDisplay(None)
    if display:
        shape.XShapeCombineRectangles(display, int(xid, 16), 2, 0, 0, None, 0, 0, 0)
        x11.XCloseDisplay(display)
    output("hyprctl", "dispatch", 'hl.dsp.window.set_prop({window="address:%s",prop="no_focus",value="1"})' % address)
    for client in clients:
        if (client["pid"] == target["pid"] and client["floating"]
                and client["title"] not in ("Fusion360", "")
                and not client["title"].startswith(("Msg:", "QTView:"))):
            output("hyprctl", "dispatch", 'hl.dsp.window.alter_zorder({window="address:%s",mode="top"})' % client["address"])


if __name__ == "__main__":
    main(sys.argv[1])
