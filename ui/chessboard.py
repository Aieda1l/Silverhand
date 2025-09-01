import sys
import chess
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

from config import PIECES_DIR, BOARD_SIZE, SQUARE_COLORS


class ChessboardWidget(QWidget):
    """
    A custom widget to display a chessboard, pieces, and highlights.
    """
    PIECE_MAP = {
        (chess.PAWN, chess.WHITE): "pawn-w",
        (chess.PAWN, chess.BLACK): "pawn-b",
        (chess.KNIGHT, chess.WHITE): "knight-w",
        (chess.KNIGHT, chess.BLACK): "knight-b",
        (chess.BISHOP, chess.WHITE): "bishop-w",
        (chess.BISHOP, chess.BLACK): "bishop-b",
        (chess.ROOK, chess.WHITE): "rook-w",
        (chess.ROOK, chess.BLACK): "rook-b",
        (chess.QUEEN, chess.WHITE): "queen-w",
        (chess.QUEEN, chess.BLACK): "queen-b",
        (chess.KING, chess.WHITE): "king-w",
        (chess.KING, chess.BLACK): "king-b",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(BOARD_SIZE, BOARD_SIZE)
        self.board = chess.Board()
        self.square_size = BOARD_SIZE // 8
        self._highlights = {}  # E.g., {chess.E4: QColor(...), ...}
        self._piece_items = {}  # Cache for QGraphicsSvgItem
        self._load_piece_svgs()

    def _load_piece_svgs(self):
        """Pre-loads SVG items for chess pieces to improve performance."""
        for piece_code, filename in self.PIECE_MAP.items():
            path = str(PIECES_DIR / f"{filename}.svg")
            item = QGraphicsSvgItem(path)
            if not item.renderer().isValid():
                print(f"Warning: Could not load piece SVG: {path}")
            self._piece_items[piece_code] = item

    def set_fen(self, fen: str):
        """Updates the board state from a FEN string."""
        try:
            self.board.set_fen(fen)
            self.update()
        except ValueError as e:
            print(f"Error setting FEN '{fen}': {e}")
            self.board.clear()
            self.update()

    def clear_highlights(self):
        """Removes all highlights from the board."""
        self._highlights.clear()
        self.update()

    def add_highlight(self, square: int, color: QColor):
        """Adds a highlight to a specific square."""
        if 0 <= square < 64:
            self._highlights[square] = color
            self.update()

    def highlight_move(self, move: chess.Move, color: QColor):
        """Highlights the from and to squares of a move."""
        self.add_highlight(move.from_square, color)
        self.add_highlight(move.to_square, color)

    def paintEvent(self, event):
        """Renders the board, pieces, and highlights in the correct order."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.square_size = min(self.width(), self.height()) // 8

        # 1. Draw the board squares first
        for square in chess.SQUARES:
            self._draw_square(painter, square)

        # 2. Draw highlights on top of the squares
        self._draw_highlights(painter)

        # 3. Draw pieces on top of squares and highlights
        self._draw_pieces(painter)

        # 4. Draw coordinates last so they are on top of everything
        self._draw_coordinates(painter)

    def _draw_square(self, painter: QPainter, square: int):
        """Draws a single square on the board."""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        is_light = (file_idx + rank_idx) % 2 != 0
        color = QColor(SQUARE_COLORS["light"] if is_light else SQUARE_COLORS["dark"])

        painter.fillRect(self._square_rect(square), color)

    def _draw_highlights(self, painter: QPainter):
        """Draws all stored highlights."""
        painter.save()
        for square, color in self._highlights.items():
            painter.fillRect(self._square_rect(square), color)
        painter.restore()

    def _draw_pieces(self, painter: QPainter):
        """Draws all the pieces on the board."""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_code = (piece.piece_type, piece.color)
                if piece_code in self._piece_items:
                    item = self._piece_items[piece_code]
                    target_rect = self._square_rect(square)
                    item.renderer().render(painter, QRectF(target_rect))

    def _draw_coordinates(self, painter: QPainter):
        """Draws rank and file coordinates."""
        painter.save()
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)

        margin = self.square_size * 0.1

        for file_idx in range(8):
            # Coordinate color should contrast with the square color
            is_light_square = (file_idx + 7) % 2 != 0
            color = QColor(SQUARE_COLORS["dark"] if is_light_square else SQUARE_COLORS["light"])
            painter.setPen(color)

            file_char = chess.FILE_NAMES[file_idx]
            text_rect = QRectF(
                file_idx * self.square_size,
                7 * self.square_size + self.square_size - margin * 1.5,
                self.square_size - margin * 0.5,
                margin * 1.5
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight, file_char)

        for rank_idx in range(8):
            is_light_square = (0 + rank_idx) % 2 != 0
            color = QColor(SQUARE_COLORS["dark"] if is_light_square else SQUARE_COLORS["light"])
            painter.setPen(color)

            rank_char = chess.RANK_NAMES[7 - rank_idx]  # Draw from top to bottom
            text_rect = QRectF(
                margin * 0.5,
                rank_idx * self.square_size,
                self.square_size - margin,
                margin * 1.5
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, rank_char)

        painter.restore()

    def _square_rect(self, square: int) -> QRectF:
        """Calculates the pixel rectangle for a given square index."""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        # Board is drawn from top-left, so we invert the rank
        return QRectF(
            file_idx * self.square_size,
            (7 - rank_idx) * self.square_size,
            self.square_size,
            self.square_size
        )


# --- Example Usage for Testing ---
if __name__ == '__main__':
    if not PIECES_DIR.exists():
        print(f"Creating directory: {PIECES_DIR}")
        PIECES_DIR.mkdir(parents=True, exist_ok=True)
        print("Please place your piece SVG files in the above directory.")
        print("Example: 'king-w.svg', 'pawn-b.svg', etc.")

    app = QApplication(sys.argv)

    main_window = QWidget()
    main_window.setWindowTitle("Chessboard Widget Test")
    main_window.setGeometry(100, 100, BOARD_SIZE + 50, BOARD_SIZE + 50)

    board_widget = ChessboardWidget(main_window)
    board_widget.move(25, 25)

    sicilian_fen = "r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    print(f"Setting FEN to: {sicilian_fen}")
    board_widget.set_fen(sicilian_fen)

    print("Highlighting move d2d4")
    move_to_highlight = chess.Move.from_uci("d2d4")
    board_widget.highlight_move(move_to_highlight, QColor(SQUARE_COLORS["highlight_best"]))

    print("Highlighting square c3")
    board_widget.add_highlight(chess.C3, QColor(SQUARE_COLORS["highlight_alt"]))

    main_window.show()
    sys.exit(app.exec())