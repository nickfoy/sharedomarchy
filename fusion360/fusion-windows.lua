-- Fusion's Wine palettes are separate managed X11 windows. Keep them with the
-- main frame; new palettes otherwise open on whichever workspace is active.
local M = {}
local helper = os.getenv("HOME") .. "/.local/share/fusion-window-compat/opacity.py"

o.window({ class = "^fusion360[.]exe$", title = "^Msg:QTView:[(][0-9]+[)]MessageTray$" }, {
  workspace = "special:fusion-helpers silent",
  no_initial_focus = true,
  no_focus = true,
  opacity = "0 override 0 override",
  border_size = 0,
  no_shadow = true,
})

function M.sync()
  local windows = hl.get_windows()
  for _, window in ipairs(windows) do
    if window.class == "fusion360.exe" then
      local destination
      if window.title:match("^Msg:QTView:%(%d+%)MessageTray$") then
        destination = "special:fusion-helpers"
      else
        for _, owner in ipairs(windows) do
          if owner.class == window.class and owner.pid == window.pid
              and owner.title:find(" - Autodesk Fusion", 1, true) then
            destination = tostring(owner.workspace.id)
            break
          end
        end
      end
      if destination and destination ~= tostring(window.workspace.id)
          and destination ~= window.workspace.name then
        hl.dispatch(hl.dsp.window.move({ workspace = destination, follow = false, window = window }))
      end
      if window.title == "Fusion360" then
        -- Match using settled geometry; the helper preserves palettes without
        -- an X11 scalar opacity and does not change their per-pixel alpha.
        -- Shell-quote HOME: a new laptop may have spaces or quotes in its path.
        local quoted_helper = "'" .. helper:gsub("'", "'\\''") .. "'"
        hl.exec_cmd("python3 " .. quoted_helper .. " " .. window.address)
      end
    end
  end
end

local function on_change(window)
  if window and window.class == "fusion360.exe" then
    hl.timer(M.sync, { timeout = 200, type = "oneshot" })
  end
end
hl.on("window.open", on_change)
hl.on("window.title", on_change)
hl.on("window.move_to_workspace", on_change)
hl.timer(M.sync, { timeout = 300, type = "oneshot" })
return M
