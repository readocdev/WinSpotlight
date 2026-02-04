import numpy as np
from typing import Optional

from PyQt6.QtGui import (
    QAction, QImage, QPixmap, QPainter, QColor,
    QBrush, QPainterPath, QPen, QWheelEvent, QMouseEvent, QPaintEvent
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QSettings
from PyQt6.QtWidgets import (
    QMainWindow, QSystemTrayIcon, QStyle, QMenu, QApplication,
    QInputDialog, QLineEdit
)

class ShadowOverlay(QMainWindow):
    """
    Main overlay window responsible for screen dimming,
    magnification (zoom) and custom cursorr rendering.
    """
    def __init__(self) -> None:
        super().__init__()
        # graphics and zoom state
        self.current_pixmap = None
        self.cursor_pos = QPoint(0, 0)
        self.radius = 150
        self.zoom_factor = 2.0
        self.min_zoom = 1.0
        self.max_zoom = 5.0
        self.zoom_step = 0.2
        self.settings = QSettings("WinSpotlight", "USBConfig")
        self.target_letter = self.settings.value("drive_letter", "F")
        self.eject_all_mode = self.settings.value("eject_all_mode", False, type=bool)
        self.hotkeys_manager = None

        # window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.hide()
        self._init_tray() 

    def _init_tray(self) -> None:
        """Initialize system tray icon and context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.setToolTip("WinSpotlight 2026")

        tray_menu = QMenu() 
        tray_menu.setStyleSheet("""
            QMenu { background-color: #2b2b2b; color: white; border: 1px solid #3d3d3d; }
            QMenu::item:selected { background-color: #4a4a4a; }
            QMenu::separator{ background-color: #3d3d3d; height: 1px; margin: 4px; }
        """)

        title_action = QAction("WinSpotlight v1.0", self)
        title_action.setEnabled(False)

        self.all_mode_action = QAction("Извлечь все флешки", self)
        self.all_mode_action.setCheckable(True)
        self.all_mode_action.setChecked(self.eject_all_mode)
        self.all_mode_action.triggered.connect(self._toggle_eject_mode)

        self.eject_action = QAction(f"Извлечь диск ({self.target_letter}:)", self)
        self.eject_action.triggered.connect(lambda: self._handle_eject())

        self.setup_action = QAction("Настроить букву диска...", self)
        self.setup_action.triggered.connect(self._change_usb_letter)

        quit_action = QAction("Выход", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(title_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.all_mode_action)
        tray_menu.addAction(self.eject_action)
        tray_menu.addAction(self.setup_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def set_hotkeys_manager(self, manager):
        self.hotkeys_manager = manager
     
    def _toggle_eject_mode(self, checked: bool) -> None:
        """
        Toggles between 'Eject All' and 'Single Drive' modes.

        Updates the configuration and enables/disables corresponding UI actions
        based on the selected mode.
        """
        self.eject_all_mode = checked
        self.settings.setValue("eject_all_mode", checked)

        self.eject_action.setEnabled(not checked)
        self.setup_action.setEnabled(not checked)
    
    def _change_usb_letter(self) -> None:
        """
        Opens and input dialog to update the target USB drive letter.

        Normalizes the input to a single uppercase character, persists it
        to settings, and updates the action label.
        """
        text, ok = QInputDialog.getText(
            self, "Настройка USB",
            "Введите букву флешки (например, G):",
            QLineEdit.EchoMode.Normal, self.target_letter
        )

        if ok and text:
            new_letter = text.strip().upper()[0]
            self.target_letter = new_letter
            self.settings.setValue("drive_letter", new_letter)
            self.eject_action.setText(f"Извлечь диск ({new_letter}:)")
    
    def _handle_eject(self) -> None:
        """
        Executes the ejection process based on the current mode.

        Triggers either a full system-wide ejection or a specific drive ejection
        depending on 'eject_all_mode', then displays a notification with the result.
        """
        from src.devices import eject_by_letter, eject_all

        if self.eject_all_mode:
            result = eject_all()
        else:
            result = eject_by_letter(self.target_letter)
        
        self.notify_usb(result)
            
    def set_screenshot(self, frame: Optional[np.ndarray]) -> None:
        """Convert raw dxcam frame to QPixmap."""
        if frame is None or not isinstance(frame, np.ndarray) or len(frame.shape) != 3:
            print(f"[DEBUG] set_screenshot skipped invalid frame: {getattr(frame, "shape", None)}")
            return

        try:
            height, width, channels = frame.shape
            bytes_per_line = channels * width

            q_img = QImage(
                frame.tobytes(),
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            ).copy()

            pixmap = QPixmap.fromImage(q_img)
            pixmap.setDevicePixelRatio(1.0)
            self.current_pixmap = pixmap
            self.update()

        except Exception as e:
            print(f"[ERROR] set_screenshot failed: {e}")
    
    def show_and_update(self) -> None:
        """Triggered on hotkey press."""
        self.showFullScreen()
        self.activateWindow()
        self.setFocus()

        try:
            self.grabMouse()
        except RuntimeError: pass

        self.setCursor(Qt.CursorShape.BlankCursor)
        self.cursor_pos = self.mapFromGlobal(self.cursor().pos())
        self.update()

    def hide_overlay(self) -> None:
        """Triggered on hotkey release."""
        try: 
            self.releaseMouse()
        except RuntimeError: pass

        self.unsetCursor()
        self.hide()
        self.current_pixmap = None
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Updates the local cursor position and triggers a repaint."""
        self.cursor_pos = self.mapFromGlobal(event.globalPosition().toPoint())
        self.update()
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Adjusts the zoom factor based on the mouse wheel delta."""
        delta = event.angleDelta().y()

        if delta == 0:
            return
        
        if delta > 0:
            self.zoom_factor += self.zoom_step
        else:
            self.zoom_factor -= self.zoom_step
        
        self.zoom_factor = round(max(1.0, min(10.0, self.zoom_factor)), 1) 
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Main rendering pipeline."""
        if self.current_pixmap is None: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # background image
        painter.drawPixmap(self.rect(), self.current_pixmap)

        # dimming overlay with hole
        full_screen_path = QPainterPath()
        full_screen_path.addRect(0, 0, self.width(), self.height())

        circle_path = QPainterPath()
        circle_path.addEllipse(QPointF(self.cursor_pos), self.radius, self.radius)

        dark_overlay_path = full_screen_path.subtracted(circle_path)

        overlay_color = QColor(0, 0, 0, 160)
        
        painter.fillPath(dark_overlay_path, QBrush(overlay_color))

        # zoom login (source in physical px, target in logical px)
        dpr = self.devicePixelRatio()

        real_x = self.cursor_pos.x() * dpr
        real_y = self.cursor_pos.y() * dpr
        real_radius = self.radius * dpr

        source_width = (real_radius * 2) / self.zoom_factor
        source_height = (real_radius * 2) / self.zoom_factor

        source_rect = QRectF(
            real_x - source_width / 2,
            real_y - source_height / 2,
            source_width,
            source_height
        )

        target_rect = QRectF(
            self.cursor_pos.x() - self.radius,
            self.cursor_pos.y() - self.radius,
            self.radius * 2,
            self.radius * 2
        )

        painter.setClipPath(circle_path)
        painter.drawPixmap(target_rect, self.current_pixmap, source_rect)
        painter.setClipping(False)

        # circular border
        painter.setPen(QPen(QColor(255, 255, 255, 50), 2))
        painter.drawEllipse(QPointF(self.cursor_pos), self.radius, self.radius)

        # custom cursor
        self._draw_custom_cursor(painter)
    
    def _draw_custom_cursor(self, painter: QPainter) -> None:
        """Draw aesthetic crosshair with outline for hight visibility."""
        cx, cy = self.cursor_pos.x(), self.cursor_pos.y()
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # center dot
        dot_color = QColor(255, 255, 255, 180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(QPointF(cx, cy), 1.5, 1.5)

        length, gap = 8, 5
        
        for is_outline in [True, False]:
            if is_outline:
                pen = QPen(QColor(0, 0, 0, 100), 3)
            else:
                pen = QPen(QColor(255, 255, 255, 230), 1)
            
                painter.setPen(pen)
                # drawing crosshair lines 
                painter.drawLine(QPointF(cx - gap - length, cy), QPointF(cx - gap, cy))
                painter.drawLine(QPointF(cx + gap, cy), QPointF(cx + gap + length, cy))
                painter.drawLine(QPointF(cx, cy - gap - length), QPointF(cx, cy - gap))
                painter.drawLine(QPointF(cx, cy + gap), QPointF(cx, cy + gap + length))
    
    def notify_usb(self, success: bool) -> None:
        """Display a system tray notification about the USB ejection status."""
        status = {
            True: {
                "title": "Извлечение USB",
                "msg": "Устройство успешно извлечено!",
                "icon": QSystemTrayIcon.MessageIcon.Information
            },
            False: {
                "title": "Ошибка USB",
                "msg": "Не удалось найти или извлечь накопитель",
                "icon": QSystemTrayIcon.MessageIcon.Warning
            }
        }

        cfg = status[success]

        self.tray_icon.showMessage(
            cfg["title"],
            cfg["msg"],
            cfg["icon"],
            3000
        )
