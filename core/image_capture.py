import mss
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QDialog
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QGuiApplication


class ScreenshotManager:
    """
    Handles capturing an entire monitor screen.
    Creates a full-screen overlay for the user to select a monitor.
    """

    def __init__(self, output_path):
        self.output_path = str(output_path)
        self.overlay = None

    def select_monitor_and_capture(self) -> tuple[str | None, QRect | None]:
        """
        Shows an overlay for the user to select a monitor and captures it.

        Returns:
            A tuple containing:
            - The path to the saved screenshot or None if canceled.
            - The QRect geometry of the captured monitor or None.
        """
        self.overlay = ScreenshotOverlay()
        if self.overlay.exec() == QDialog.DialogCode.Accepted:
            monitor_geometry = self.overlay.selected_monitor_geometry
            if monitor_geometry:
                self.capture_screen_area(monitor_geometry)
                return self.output_path, monitor_geometry
        return None, None

    def capture_screen_area(self, geometry: QRect):
        """
        Captures a specific rectangular area of the screen.

        Args:
            geometry (QRect): The geometry of the monitor to capture.
        """
        with mss.mss() as sct:
            # Define the capture region based on the monitor's geometry
            monitor_details = {
                "top": geometry.top(),
                "left": geometry.left(),
                "width": geometry.width(),
                "height": geometry.height(),
            }
            sct_img = sct.grab(monitor_details)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=self.output_path)
        return self.output_path


class ScreenshotOverlay(QWidget):
    """
    A semi-transparent, full-screen widget for selecting a monitor to capture.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.screens = QGuiApplication.screens()
        self.monitor_rects = [screen.geometry() for screen in self.screens]

        total_geometry = QRect()
        for rect in self.monitor_rects:
            total_geometry = total_geometry.united(rect)
        self.setGeometry(total_geometry)

        self.hover_monitor_index = -1
        self.selected_monitor_geometry = None

        self._info_label = QLabel(
            "Click on a monitor to capture it. Press Esc to cancel.", self
        )
        self._setup_info_label()

        self.setMouseTracking(True)

    def _setup_info_label(self):
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: white;
            font-size: 18px;
            padding: 10px;
            border-radius: 5px;
        """)
        self._info_label.adjustSize()
        primary_screen_geo = QGuiApplication.primaryScreen().geometry()
        self._info_label.move(
            int(primary_screen_geo.x() + (primary_screen_geo.width() - self._info_label.width()) / 2),
            int(primary_screen_geo.y() + (primary_screen_geo.height() - self._info_label.height()) / 2),
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(100, 100, 100, 100))

        for i, rect in enumerate(self.monitor_rects):
            relative_rect = rect.translated(-self.geometry().topLeft())
            if i == self.hover_monitor_index:
                pen = QPen(QColor(30, 200, 30, 255), 4, Qt.PenStyle.SolidLine)
                painter.setBrush(QColor(30, 200, 30, 70))
            else:
                pen = QPen(QColor(200, 200, 200, 150), 2, Qt.PenStyle.DashLine)
                painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawRect(relative_rect)

    def mouseMoveEvent(self, event):
        pos = event.globalPosition().toPoint()
        current_hover = -1
        for i, rect in enumerate(self.monitor_rects):
            if rect.contains(pos):
                current_hover = i
                break
        if current_hover != self.hover_monitor_index:
            self.hover_monitor_index = current_hover
            self.update()

    def mousePressEvent(self, event):
        pos = event.globalPosition().toPoint()
        for rect in self.monitor_rects:
            if rect.contains(pos):
                self.selected_monitor_geometry = rect
                self.accept()
                return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()

    def exec(self):
        self.show()
        self.accepted = False
        self.rejected = False
        while not self.accepted and not self.rejected:
            QApplication.instance().processEvents()
        self.hide()
        return QDialog.DialogCode.Accepted if self.accepted else QDialog.DialogCode.Rejected

    def accept(self):
        self.accepted = True

    def reject(self):
        self.rejected = True


# The WebcamManager class remains unchanged.
class WebcamManager:
    """
    Handles capturing an image from the default webcam.
    """

    def __init__(self, output_path, camera_index=0):
        self.output_path = str(output_path)
        self.camera_index = camera_index

    def capture_frame(self):
        """
        Opens the webcam, captures a single frame, and saves it.
        Returns the path to the saved image or None on failure.
        """
        import cv2
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return None

        ret, frame = cap.read()
        cap.release()

        if ret:
            cv2.imwrite(self.output_path, frame)
            return self.output_path
        else:
            print("Error: Could not read frame from webcam.")
            return None


if __name__ == '__main__':
    # Example usage for testing
    import sys

    app = QApplication(sys.argv)

    # --- Test Screenshot ---
    print("Testing screenshot functionality...")
    screenshot_path = "test_screenshot.png"
    ss_manager = ScreenshotManager(screenshot_path)
    saved_path = ss_manager.take_screenshot()
    if saved_path:
        print(f"Screenshot saved to {saved_path}")
    else:
        print("Screenshot canceled.")

    # --- Test Webcam ---
    # print("\nTesting webcam capture...")
    # webcam_path = "test_webcam.png"
    # wc_manager = WebcamManager(webcam_path)
    # saved_webcam_path = wc_manager.capture_frame()
    # if saved_webcam_path:
    #     print(f"Webcam image saved to {saved_webcam_path}")
    # else:
    #     print("Webcam capture failed.")

    sys.exit(app.exec())