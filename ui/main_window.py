import sys
import chess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QFrame, QApplication, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QSize

from config import (
    APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, ELO_MIN, ELO_MAX, ELO_STEP,
    ELO_DEFAULT, SCREENSHOT_CAPTURE_PATH, WEBCAM_CAPTURE_PATH, SQUARE_COLORS
)
from ui.chessboard import ChessboardWidget
from core.image_capture import ScreenshotManager, WebcamManager
from core.ocr import OCRManager
from core.engine import EngineManager
from workers.ocr_worker import OCRWorker
from workers.engine_worker import EngineWorker


class MainWindow(QMainWindow):
    """
    The main application window for the Silverhand Chess Bot.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(_get_stylesheet())

        # --- State ---
        self.current_fen = None
        self.ocr_worker = None
        self.engine_worker = None

        # --- Core Components ---
        print("Initializing core components...")
        self.screenshot_manager = ScreenshotManager(SCREENSHOT_CAPTURE_PATH)
        self.webcam_manager = WebcamManager(WEBCAM_CAPTURE_PATH)
        self.ocr_manager = OCRManager()
        self.engine_manager = EngineManager()  # Singleton, safe to call
        print("Initialization complete.")

        # --- UI Widgets ---
        self._init_ui()
        self._connect_signals()

        self.update_status("Ready. Capture a board to begin.")

    def _init_ui(self):
        """Initializes the main layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Controls ---
        controls_layout = self._create_controls_panel()

        # --- Center Panel: Chessboard ---
        self.board_widget = ChessboardWidget()

        # --- Right Panel: Analysis ---
        analysis_layout = self._create_analysis_panel()

        main_layout.addLayout(controls_layout, 2)
        main_layout.addWidget(self.board_widget, 5)
        main_layout.addLayout(analysis_layout, 2)

        # --- Status Bar ---
        self.statusBar().showMessage("Welcome to Silverhand!")

    def _create_controls_panel(self):
        """Creates the left panel with capture buttons and ELO slider."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Title ---
        title_label = QLabel("Controls")
        title_label.setObjectName("TitleLabel")

        # --- Capture Buttons ---
        self.screenshot_button = QPushButton("Capture Screenshot")
        self.webcam_button = QPushButton("Capture from Webcam")

        # --- ELO Slider ---
        elo_group_label = QLabel("Engine Skill Level (ELO)")
        elo_group_label.setObjectName("GroupLabel")

        self.elo_slider = QSlider(Qt.Orientation.Horizontal)
        self.elo_slider.setRange(ELO_MIN, ELO_MAX)
        self.elo_slider.setSingleStep(ELO_STEP)
        self.elo_slider.setTickInterval(ELO_STEP)
        self.elo_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.elo_slider.setValue(ELO_DEFAULT)

        self.elo_label = QLabel(f"{ELO_DEFAULT} ELO")
        self.elo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(self.screenshot_button)
        layout.addWidget(self.webcam_button)
        layout.addSpacing(20)
        layout.addWidget(elo_group_label)
        layout.addWidget(self.elo_slider)
        layout.addWidget(self.elo_label)

        return layout

    def _create_analysis_panel(self):
        """Creates the right panel to display move analysis results."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Analysis")
        title_label.setObjectName("TitleLabel")

        self.win_prob_label = QLabel("Win Probability: --%")
        self.win_prob_label.setObjectName("InfoLabel")

        moves_label = QLabel("Top Moves")
        moves_label.setObjectName("GroupLabel")

        # Use a list of labels to display top moves
        self.top_moves_labels = [QLabel(f"{i + 1}. --") for i in range(3)]

        layout.addWidget(title_label)
        layout.addWidget(self.win_prob_label)
        layout.addSpacing(20)
        layout.addWidget(moves_label)
        for label in self.top_moves_labels:
            label.setObjectName("InfoLabel")
            layout.addWidget(label)

        return layout

    def _connect_signals(self):
        """Connects widget signals to their corresponding slots."""
        self.screenshot_button.clicked.connect(self.capture_screenshot)
        self.webcam_button.clicked.connect(self.capture_webcam)
        self.elo_slider.valueChanged.connect(self.update_elo_label)
        self.elo_slider.sliderReleased.connect(self.rerun_analysis)

    def update_status(self, message: str, is_error=False):
        """Updates the message in the status bar."""
        style = "color: #E74C3C;" if is_error else ""
        self.statusBar().setStyleSheet(style)
        self.statusBar().showMessage(message, 5000)  # Message disappears after 5s
        print(message)

    def update_elo_label(self, value):
        """Updates the ELO display label as the slider moves."""
        # Snap value to the nearest step
        snapped_value = round(value / ELO_STEP) * ELO_STEP
        self.elo_label.setText(f"{snapped_value} ELO")
        if self.elo_slider.value() != snapped_value:
            self.elo_slider.setValue(snapped_value)

    def capture_screenshot(self):
        """Handles the screenshot capture process."""
        self.hide()  # Hide main window to capture screen
        image_path = self.screenshot_manager.take_screenshot()
        self.show()  # Show it again

        if image_path:
            self.start_ocr_process(image_path)
        else:
            self.update_status("Screenshot capture canceled.")

    def capture_webcam(self):
        """Handles the webcam capture process."""
        self.update_status("Capturing from webcam...")
        # For simplicity, we're not showing a live feed, just a single capture.
        # A live feed would require a more complex setup with another thread/camera dialog.
        image_path = self.webcam_manager.capture_frame()
        if image_path:
            self.start_ocr_process(image_path)
        else:
            self.update_status("Failed to capture from webcam.", is_error=True)

    def start_ocr_process(self, image_path):
        """Initiates the OCR worker thread."""
        self.clear_analysis_results()
        self.board_widget.clear_highlights()

        self.ocr_worker = OCRWorker(image_path, self.ocr_manager)
        self.ocr_worker.progress.connect(self.update_status)
        self.ocr_worker.error.connect(lambda msg: self.update_status(msg, is_error=True))
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.start()

    def on_ocr_finished(self, fen, cropped_image_path):
        """Handles the results from a successful OCR process."""
        self.current_fen = fen
        self.board_widget.set_fen(fen)
        # Highlight the last move if FEN indicates one
        try:
            board = chess.Board(fen)
            if board.move_stack:
                last_move = board.move_stack[-1]
                self.board_widget.highlight_move(
                    last_move, QColor(SQUARE_COLORS['highlight_last'])
                )
        except Exception:
            pass  # FEN might be invalid for move stack

        self.rerun_analysis()

    def rerun_analysis(self):
        """Starts the engine analysis if a valid FEN is available."""
        if self.current_fen:
            self.clear_analysis_results()
            elo = self.elo_slider.value()
            self.engine_worker = EngineWorker(self.current_fen, elo, self.engine_manager)
            self.engine_worker.progress.connect(self.update_status)
            self.engine_worker.error.connect(lambda msg: self.update_status(msg, is_error=True))
            self.engine_worker.finished.connect(self.on_engine_finished)
            self.engine_worker.start()

    def on_engine_finished(self, predictions):
        """Displays the results from the engine analysis."""
        move_probs = predictions.get("move_probabilities", {})
        win_prob = predictions.get("win_probability", 0.0)

        # Update win probability label
        self.win_prob_label.setText(f"Win Probability: {win_prob:.1%}")

        # Update top moves and highlight them on the board
        self.board_widget.clear_highlights()
        top_moves = list(move_probs.items())

        for i, label in enumerate(self.top_moves_labels):
            if i < len(top_moves):
                move_uci, prob = top_moves[i]
                label.setText(f"{i + 1}. {move_uci} ({prob:.1%})")

                # Highlight the moves on the board
                move = chess.Move.from_uci(move_uci)
                if i == 0:  # Best move
                    color = QColor(SQUARE_COLORS['highlight_best'])
                else:  # Alternate moves
                    color = QColor(SQUARE_COLORS['highlight_alt'])
                self.board_widget.highlight_move(move, color)
            else:
                label.setText(f"{i + 1}. --")

    def clear_analysis_results(self):
        """Resets the analysis panel to its default state."""
        self.win_prob_label.setText("Win Probability: --%")
        for i, label in enumerate(self.top_moves_labels):
            label.setText(f"{i + 1}. --")


def _get_stylesheet():
    """Returns the application's stylesheet."""
    return """
        QMainWindow, QWidget {
            background-color: #2C3E50;
            color: #ECF0F1;
        }
        #TitleLabel {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        #GroupLabel {
            font-size: 16px;
            font-weight: bold;
            margin-top: 15px;
            color: #BDC3C7;
        }
        #InfoLabel {
            font-size: 14px;
        }
        QPushButton {
            background-color: #3498DB;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #2980B9;
        }
        QPushButton:pressed {
            background-color: #1F618D;
        }
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: #4A6278;
            height: 8px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #3498DB;
            border: 1px solid #3498DB;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }
        QSlider::add-page:horizontal {
            background: #4A6278;
        }
        QSlider::sub-page:horizontal {
            background: #5DADE2;
        }
        QStatusBar {
            background-color: #212F3D;
            font-size: 12px;
        }
    """


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())