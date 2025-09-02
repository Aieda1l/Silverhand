from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QRect
from PyQt6.QtGui import QPainter, QBrush, QColor


class ScreenOverlay(QWidget):
    """
    A transparent, full-screen widget to draw chess move highlights
    directly over the screen.
    """

    def __init__(self):
        super().__init__()

        # Make the window frameless, always on top, and transparent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |  # Prevents it from appearing in the taskbar
            Qt.WindowType.WindowTransparentForInput  # Makes the window transparent for all input events
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Make it non-interactive

        # Data for drawing
        self.board_bbox = None  # The bounding box of the chessboard on the screen
        self.highlights = {}  # Dict of {square_index: (color, priority)}

    def update_drawing_data(self, board_bbox, highlights):
        """
        Receives the necessary data from the main window to draw highlights.
        """
        self.board_bbox = board_bbox
        self.highlights = highlights

        # Resize the overlay to match the screen containing the board
        if self.board_bbox:
            screen = self.screen()
            if screen:
                self.setGeometry(screen.geometry())

        # Trigger a repaint
        self.update()

    def clear_drawing(self):
        """Clears all highlights from the overlay."""
        self.board_bbox = None
        self.highlights = {}
        self.update()

    def paintEvent(self, event):
        """The main drawing event for the overlay."""
        super().paintEvent(event)

        if not self.board_bbox or not self.highlights:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # The bounding box is in global screen coordinates. We need to translate
        # it to be relative to our overlay widget's position.
        relative_bbox = self.board_bbox.translated(-self.geometry().topLeft())

        square_width = relative_bbox.width() / 8
        square_height = relative_bbox.height() / 8

        # Use the same multi-pass logic as the chessboard widget for correct layering
        # Pass 1: Low priority (alternate moves)
        for square, (color, priority) in self.highlights.items():
            if priority == 0:
                file = square % 8
                rank = 7 - (square // 8)  # FEN ranks are top-to-bottom

                rect = QRectF(
                    relative_bbox.left() + file * square_width,
                    relative_bbox.top() + rank * square_height,
                    square_width,
                    square_height
                )
                painter.fillRect(rect, color)

        # Pass 2: High priority (best move)
        for square, (color, priority) in self.highlights.items():
            if priority == 1:
                file = square % 8
                rank = 7 - (square // 8)

                rect = QRectF(
                    relative_bbox.left() + file * square_width,
                    relative_bbox.top() + rank * square_height,
                    square_width,
                    square_height
                )
                painter.fillRect(rect, color)

    def showEvent(self, event):
        """Ensure the widget is full-screen when shown."""
        if self.board_bbox:
            screen = self.screen()
            if screen:
                self.setGeometry(screen.geometry())
        super().showEvent(event)