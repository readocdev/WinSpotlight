import os
import sys
import numpy as np
from ctypes import wintypes
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QAbstractNativeEventFilter

from overlay.window import ShadowOverlay
from src.hotkeys import HotKeys
from src.capture import CameraManager
from src.devices import eject_all, eject_by_letter


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, manager: HotKeys):
        super().__init__()
        self.manager = manager

    def nativeEventFilter(self, eventType, message):
        if eventType != b"windows_generic_MSG":
            return False, 0

        ptr = int(message)
        if not ptr:
            return False, 0

        # SAFE: let ctypes map MSG properly
        msg = wintypes.MSG.from_address(ptr)

        if msg.message == 0x0312:  # WM_HOTKEY
            if self.manager.process_native_msg(msg):
                return True, 0

        return False, 0


# DPI / scaling (OK as is)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = ShadowOverlay()
    camera = CameraManager()
    hotkeys = HotKeys()

    event_filter = WinEventFilter(hotkeys)
    app.installNativeEventFilter(event_filter)

    overlay.hotkeys_manager = hotkeys

    def handle_activate() -> None:
        if overlay.isVisible():
            return

        frame: Optional[object] = camera.get_frame()

        if frame is None:
            print("[DEBUG] DXCAM returned None")
            return
        if not isinstance(frame, np.ndarray):
            print(f"[DEBUG] Invalid frame type: {type(frame)}")
            return
        if len(frame.shape) != 3:
            print(f"[DEBUG] Invalid frame shape: {frame.shape}")
            return
        
        try:
            overlay.set_screenshot(frame)
            overlay.show_and_update()
            overlay.activateWindow()
        except Exception as e:
            print(f"[ERROR] Failed to display overlay: {e}")

    def handle_eject() -> None:
        if overlay.eject_all_mode:
            result = eject_all()
        else:
            result = eject_by_letter(overlay.target_letter)

        overlay.notify_usb(result)

    hotkeys.set_hotkeys({
        "show": "alt+z",
        "eject_usb": "alt+e",
    })

    hotkeys.activated.connect(handle_activate)
    hotkeys.deactivated.connect(overlay.hide_overlay)
    hotkeys.request_eject.connect(handle_eject)

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
