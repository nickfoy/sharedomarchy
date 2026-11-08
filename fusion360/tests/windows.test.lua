-- Run from the repository root: lua fusion360/tests/windows.test.lua
local calls, commands = {}, {}
local home = "/tmp/a laptop's home"
local original_getenv = os.getenv
os.getenv = function(key) if key == 'HOME' then return home end return original_getenv(key) end
local function window(address, title, pid, id, class)
  return { address=address, title=title, pid=pid, class=class or 'fusion360.exe', workspace={id=id, name=tostring(id)} }
end
local windows = {
  window('0x1', 'Part - Autodesk Fusion Personal', 11, 27),
  window('0x2', 'Fusion360', 11, 26),
  window('0x3', 'Msg:QTView:(102)MessageTray', 11, 27),
  window('0x4', 'Other - Autodesk Fusion Personal', 22, 8),
  window('0x5', 'Preferences', 22, 9),
  window('0x6', 'Browser', 33, 9, 'firefox'),
}
o = { window = function() end }
hl = {
  get_windows = function() return windows end,
  exec_cmd = function(cmd) table.insert(commands, cmd) end,
  dispatch = function(action) table.insert(calls, action) end,
  on = function() end,
  timer = function() end,
  dsp = { window = { move = function(args) return args end } },
}
local module = assert(loadfile('fusion360/fusion-windows.lua'))()
module.sync()
assert(#calls == 3, 'only the two misplaced utilities and blank tray should move')
assert(calls[1].window.address == '0x2' and calls[1].workspace == '27')
assert(calls[2].window.address == '0x3' and calls[2].workspace == 'special:fusion-helpers')
assert(calls[3].window.address == '0x5' and calls[3].workspace == '8', 'must use same-process owner')
for _, call in ipairs(calls) do assert(call.follow == false, 'must not switch the user workspace') end
assert(#commands == 1)
assert(commands[1] == "python3 '/tmp/a laptop'\\''s home/.local/share/fusion-window-compat/opacity.py' 0x2",
       'helper path must be shell-quoted')
print('Workspace ownership, process isolation and HOME quoting passed')
