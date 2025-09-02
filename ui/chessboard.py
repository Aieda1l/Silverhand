import sys
import chess
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

from config import PIECES_DIR, BOARD_SIZE, SQUARE_COLORS


class ChessboardWidget(QWidget):
    """
    A custom widget to display a chessboard, pieces, highlights, and coordinates.
    """
    PIECE_MAP = {
        (chess.PAWN, chess.WHITE): "pawn-w", (chess.PAWN, chess.BLACK): "pawn-b",
        (chess.KNIGHT, chess.WHITE): "knight-w", (chess.KNIGHT, chess.BLACK): "knight-b",
        (chess.BISHOP, chess.WHITE): "bishop-w", (chess.BISHOP, chess.BLACK): "bishop-b",
        (chess.ROOK, chess.WHITE): "rook-w", (chess.ROOK, chess.BLACK): "rook-b",
        (chess.QUEEN, chess.WHITE): "queen-w", (chess.QUEEN, chess.BLACK): "queen-b",
        (chess.KING, chess.WHITE): "king-w", (chess.KING, chess.BLACK): "king-b",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(BOARD_SIZE, BOARD_SIZE)
        self.board = chess.Board()
        self.coord_padding = 20
        self.square_size = (BOARD_SIZE - self.coord_padding) // 8
        self._highlights = {}  # E.g., {chess.E4: (QColor, priority), ...}
        self._piece_items = {}
        self._load_piece_svgs()

    def _load_piece_svgs(self):
        for piece_code, filename in self.PIECE_MAP.items():
            path = str(PIECES_DIR / f"{filename}.svg")
            item = QGraphicsSvgItem(path);
            self._piece_items[piece_code] = item

    def set_fen(self, fen: str):
        try:
            self.board.set_fen(fen); self.update()
        except ValueError:
            self.board.clear(); self.update()

    def clear_highlights(self):
        self._highlights.clear()
        self.update()

    def add_highlight(self, square: int, color: QColor, priority: int = 0):
        """
        Adds a highlight to a specific square, enforcing priority rules.
        A higher priority highlight will always replace a lower priority one.
        An equal or lower priority highlight will be ignored if one already exists.
        """
        if 0 <= square < 64:
            # Check if a highlight already exists for this square
            if square in self._highlights:
                _, existing_priority = self._highlights[square]
                # Only add/replace if the new highlight has higher priority
                if priority > existing_priority:
                    self._highlights[square] = (color, priority)
            else:
                # If no highlight exists, add it
                self._highlights[square] = (color, priority)

            self.update()

    def highlight_move(self, move: chess.Move, color: QColor, priority: int = 0):
        """Adds highlights for a move's from and to squares."""
        self.add_highlight(move.from_square, color, priority)
        self.add_highlight(move.to_square, color, priority)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        min_dim = min(self.width(), self.height())
        self.square_size = (min_dim - self.coord_padding) // 8
        self.board_offset = self.coord_padding // 2

        for square in chess.SQUARES: self._draw_square(painter, square)
        self._draw_highlights(painter)  # Now simplified
        self._draw_pieces(painter)
        self._draw_coordinates(painter)

    def _draw_square(self, painter: QPainter, square: int):
        file_idx = chess.square_file(square);
        rank_idx = chess.square_rank(square)
        is_light = (file_idx + rank_idx) % 2 != 0
        color = QColor(SQUARE_COLORS["light"] if is_light else SQUARE_COLORS["dark"])
        painter.fillRect(self._square_rect(square), color)

    def _draw_highlights(self, painter: QPainter):
        """
        Draws all highlights. The logic in 'add_highlight' ensures that the
        correct color (the one with the highest priority) is already stored.
        """
        painter.save()
        # No special sorting or passes needed anymore. Just draw what's stored.
        for square, (color, _) in self._highlights.items():
            painter.fillRect(self._square_rect(square), color)
        painter.restore()

    def _draw_pieces(self, painter: QPainter):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_code = (piece.piece_type, piece.color)
                if piece_code in self._piece_items:
                    item = self._piece_items[piece_code]
                    item.renderer().render(painter, QRectF(self._square_rect(square)))

    def _draw_coordinates(self, painter: QPainter):
        painter.save()
        font = QFont("Arial", 10);
        painter.setFont(font)
        painter.setPen(QColor("#BDC3C7"))

        for file_idx in range(8):
            file_char = chess.FILE_NAMES[file_idx]
            text_x = self.board_offset + file_idx * self.square_size + (
                        self.square_size / 2) - painter.fontMetrics().horizontalAdvance(file_char) / 2
            text_y = self.board_offset + 8 * self.square_size + self.coord_padding / 2 + painter.fontMetrics().height() / 4
            painter.drawText(int(text_x), int(text_y), file_char)

        for rank_idx in range(8):
            rank_char = chess.RANK_NAMES[rank_idx]
            text_x = self.board_offset / 2 - painter.fontMetrics().horizontalAdvance(rank_char) / 2
            text_y = self.board_offset + (7 - rank_idx) * self.square_size + (
                        self.square_size / 2) + painter.fontMetrics().height() / 4
            painter.drawText(int(text_x), int(text_y), rank_char)

        painter.restore()

    def _square_rect(self, square: int) -> QRectF:
        file_idx = chess.square_file(square);
        rank_idx = chess.square_rank(square)
        return QRectF(self.board_offset + file_idx * self.square_size,
                      self.board_offset + (7 - rank_idx) * self.square_size, self.square_size, self.square_size)