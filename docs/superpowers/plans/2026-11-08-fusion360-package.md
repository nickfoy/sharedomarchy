# Fusion window compatibility package

Preserve the tested local Fusion workaround under `fusion360/` in nickfoy/sharedomarchy.

- [x] Copy the Lua module and opacity/ARGB helper; quote HOME paths for portability.
- [x] Add a reversible installer/uninstaller. Back up existing files, add one managed Lua import, preserve unrelated configuration, refuse to overwrite locally edited payloads.
- [x] Test those lifecycle behaviors in temporary home directories (including spaces). Run only the explicit installer test file locally.
- [x] Document dependencies, the tested Wine/Hyprland versions, limitations, manual live verification and rollback. Add GitHub validation for all package files.
- [ ] Review the complete diff, push, and verify GitHub checks before integrating into main.

Runtime behavior stays the same as the user-confirmed workstation fix. No Wine files, credentials, session IDs, screenshots or device-specific configuration are packaged.
