import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict

# WinAPI constants
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

class HotKeys(QObject):
    """
    Manages global system hotkeys using RegisterHotKey (thread-level)
    and exposes them as Qt signals.
    """

    activated = pyqtSignal()
    deactivated = pyqtSignal()
    request_eject = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._user32 = ctypes.windll.user32
        self._hotkey_map: Dict[int, str] = {}
        self._toggled = False

    def set_hotkeys(self, config: Dict[str, str]) -> None:
        """
        Registers hotkeys like:
        {
            "show": "alt+z",
            "eject_usb": "alt+e"
        }
        """
        self.unbind_all()

        mod_lookup = {
            "alt": MOD_ALT,
            "ctrl": MOD_CONTROL,
            "shift": MOD_SHIFT,
            "win": MOD_WIN,
        }

        for hk_id, (action, hotkey_str) in enumerate(config.items()):
            parts = hotkey_str.lower().split("+")
            main_key = parts[-1]

            mods = 0
            for part in parts[:-1]:
                mods |= mod_lookup.get(part, 0)

            vk = ord(main_key.upper())

            ok = self._user32.RegisterHotKey(
                None,       # HWND = NULL → thread-level hotkey (СТАБИЛЬНО)
                hk_id,
                mods,
                vk
            )

            if ok:
                self._hotkey_map[hk_id] = action
            else:
                err = ctypes.GetLastError()
                print(
                    f"[RegisterHotKey ERROR] "
                    f"{hotkey_str} (action={action}), code={err}"
                )

    def process_native_msg(self, msg: wintypes.MSG) -> bool:
        """
        Handles WM_HOTKEY messages.
        Returns True if the message was consumed.
        """
        if msg.message != WM_HOTKEY:
            return False

        action = self._hotkey_map.get(msg.wParam)
        if not action:
            return False

        if action == "show":
            self._toggled = not self._toggled
            if self._toggled:
                self.activated.emit()
            else:
                self.deactivated.emit()
            return True

        if action == "eject_usb":
            self.request_eject.emit()
            return True

        return False

    def unbind_all(self) -> None:
        """Unregister all previously registered hotkeys."""
        for hk_id in self._hotkey_map.keys():
            self._user32.UnregisterHotKey(None, hk_id)
        self._hotkey_map.clear()
