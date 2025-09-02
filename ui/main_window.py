import sys
import chess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QFrame, QApplication, QSizePolicy, QCheckBox, QComboBox
)
from PyQt6.QtGui import QPixmap, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer, QRect

from config import (
    APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, ELO_MIN, ELO_MAX, ELO_STEP,
    ELO_DEFAULT, SCREENSHOT_CAPTURE_PATH, WEBCAM_CAPTURE_PATH, SQUARE_COLORS,
    REALTIME_ANALYSIS_INTERVAL_MS, AVAILABLE_MODELS, DEFAULT_MODEL
)
from ui.chessboard import ChessboardWidget
from ui.screen_overlay import ScreenOverlay
from core.image_capture import ScreenshotManager
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
        self.last_screenshot_path = None
        self.monitored_screen_geometry = None
        self.board_bbox_on_screen = None
        self.ocr_worker = None
        self.engine_worker = None

        # --- Core Components ---
        print("Initializing core components...")
        self.screenshot_manager = ScreenshotManager(SCREENSHOT_CAPTURE_PATH)
        # We don't need a dedicated WebcamManager from image_capture anymore,
        # as the screenshot logic is now different. The webcam will use lc2fen directly.

        self.digital_ocr_manager = OCRManager(mode='digital')
        self.physical_ocr_manager = OCRManager(mode='physical')

        self.engine_manager = EngineManager()  # Singleton, safe to call
        print("Initialization complete.")

        self.realtime_timer = QTimer(self)
        self.realtime_timer.setInterval(REALTIME_ANALYSIS_INTERVAL_MS)

        self.screen_overlay = ScreenOverlay()

        # --- UI Widgets ---
        self._init_ui()
        self._connect_signals()

        self.update_status("Ready. Capture a board to begin.")

    def _init_ui(self):
        """Initializes the main layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        controls_layout = self._create_controls_panel()
        self.board_widget = ChessboardWidget()
        analysis_layout = self._create_analysis_panel()

        main_layout.addLayout(controls_layout, 2)
        main_layout.addWidget(self.board_widget, 5)
        main_layout.addLayout(analysis_layout, 2)

        self.statusBar().showMessage("Welcome to Silverhand!")

    def _create_controls_panel(self):
        """Creates the left panel with capture buttons, ELO slider, and new toggle."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Controls")
        title_label.setObjectName("TitleLabel")

        self.screenshot_button = QPushButton("Capture Digital Board")
        self.webcam_button = QPushButton("Capture Physical Board")
        self.realtime_toggle = QCheckBox("Real-time Analysis (Digital)")
        self.draw_on_screen_toggle = QCheckBox("Draw Highlights on Screen")
        self.draw_on_screen_toggle.setToolTip("Shows move suggestions directly over the chessboard on your screen.")

        settings_label = QLabel("Settings")
        settings_label.setObjectName("GroupLabel")

        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Black"])
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("My Color:"))
        color_layout.addWidget(self.color_combo)

        self.model_combo = QComboBox()
        self.model_combo.addItems([model.capitalize() for model in AVAILABLE_MODELS])
        self.model_combo.setCurrentText(DEFAULT_MODEL.capitalize())
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Engine Model:"))
        model_layout.addWidget(self.model_combo)

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
        layout.addSpacing(10)
        layout.addWidget(self.realtime_toggle)
        layout.addWidget(self.draw_on_screen_toggle)
        layout.addSpacing(20)
        layout.addWidget(settings_label)
        layout.addLayout(color_layout)
        layout.addLayout(model_layout)
        layout.addSpacing(20)
        layout.addWidget(elo_group_label)
        layout.addWidget(self.elo_slider)
        layout.addWidget(self.elo_label)

        return layout

    def _create_analysis_panel(self):
        # This method remains the same
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_label = QLabel("Analysis")
        title_label.setObjectName("TitleLabel")
        self.win_prob_label = QLabel("Win Probability: --%")
        self.win_prob_label.setObjectName("InfoLabel")
        moves_label = QLabel("Top Moves")
        moves_label.setObjectName("GroupLabel")
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
        self.elo_slider.sliderReleased.connect(self.rerun_analysis_if_board_present)
        self.realtime_toggle.toggled.connect(self.handle_realtime_toggle)
        self.realtime_timer.timeout.connect(self.run_realtime_check)
        self.color_combo.currentTextChanged.connect(self.rerun_analysis_if_board_present)
        self.model_combo.currentTextChanged.connect(self.switch_engine_model)
        self.draw_on_screen_toggle.toggled.connect(self.handle_draw_on_screen_toggle)

    def switch_engine_model(self, model_name: str):
        """Tells the engine manager to switch the active model."""
        self.engine_manager.switch_model(model_name.lower())
        self.rerun_analysis_if_board_present()

    def update_status(self, message: str, is_error=False, timeout=5000):
        """Updates the message in the status bar."""
        style = "color: #E74C3C;" if is_error else ""
        self.statusBar().setStyleSheet(style)
        self.statusBar().showMessage(message, timeout)
        print(message)

    def update_elo_label(self, value):
        snapped_value = round(value / ELO_STEP) * ELO_STEP
        self.elo_label.setText(f"{snapped_value} ELO")
        if self.elo_slider.value() != snapped_value:
            self.elo_slider.setValue(snapped_value)

    def capture_screenshot(self):
        """Handles the screenshot capture process for digital boards."""
        self.hide()
        image_path, monitor_geometry = self.screenshot_manager.select_monitor_and_capture()
        self.show()

        if image_path and monitor_geometry:
            # Store the geometry of the captured screen
            self.monitored_screen_geometry = monitor_geometry
            self.start_ocr_process(image_path, ocr_mode='digital')
        else:
            self.update_status("Screenshot capture canceled.")
            # If the user canceled, and real-time was on, turn it off
            if self.realtime_toggle.isChecked():
                self.realtime_toggle.setChecked(False)

    def capture_webcam(self):
        """Handles the webcam capture process for physical boards."""
        # For a real implementation, you'd open a dialog with a live feed.
        # For simplicity, we'll imagine a file dialog is opened to select a photo.
        # This part is a placeholder for actual webcam integration.
        self.update_status("Webcam capture not fully implemented. Using a placeholder image.")
        # In a real scenario, you would capture a frame and save it to WEBCAM_CAPTURE_PATH
        # and then call start_ocr_process with ocr_mode='physical'.
        # For now, let's disable the real-time toggle if webcam is used.
        self.realtime_toggle.setChecked(False)

    def start_ocr_process(self, image_path, ocr_mode: str):
        """Initiates the OCR worker thread without prematurely clearing the UI."""
        manager = self.digital_ocr_manager if ocr_mode == 'digital' else self.physical_ocr_manager

        self.ocr_worker = OCRWorker(image_path, manager)
        self.ocr_worker.progress.connect(lambda msg: self.update_status(msg, timeout=2000))
        self.ocr_worker.error.connect(lambda msg: self.update_status(msg, is_error=True))
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.start()

    def on_ocr_finished(self, bbox, fen, cropped_image_path):
        if bbox:
            monitor_x = self.monitored_screen_geometry.x()
            monitor_y = self.monitored_screen_geometry.y()

            self.board_bbox_on_screen = QRect(
                monitor_x + bbox[0],
                monitor_y + bbox[1],
                bbox[2] - bbox[0],
                bbox[3] - bbox[1]
            )
        else:
            self.board_bbox_on_screen = None
            if self.draw_on_screen_toggle.isChecked():
                self.draw_on_screen_toggle.setChecked(False)

        if fen == self.current_fen:
            self.update_status("Board state is unchanged.", timeout=2000)
            return

        self.clear_analysis_results()
        self.board_widget.clear_highlights()
        self.current_fen = fen
        self.board_widget.set_fen(fen)
        self.rerun_analysis_if_board_present()

    def rerun_analysis_if_board_present(self):
        """Starts engine analysis if a valid FEN is available."""
        if self.current_fen:
            if self.engine_worker and self.engine_worker.isRunning():
                return

            self.clear_analysis_results()
            elo = self.elo_slider.value()
            player_color = self.color_combo.currentText().lower()  # Get color from dropdown

            # Pass the board-only FEN and player color to the worker
            self.engine_worker = EngineWorker(self.current_fen, elo, self.engine_manager, player_color)
            self.engine_worker.progress.connect(lambda msg: self.update_status(msg, timeout=2000))
            self.engine_worker.error.connect(lambda msg: self.update_status(msg, is_error=True))
            self.engine_worker.finished.connect(self.on_engine_finished)
            self.engine_worker.start()

    # on_engine_finished and clear_analysis_results remain the same
    def on_engine_finished(self, predictions):
        move_probs = predictions.get("move_probabilities", {})
        win_prob = predictions.get("win_probability", 0.0)

        self.win_prob_label.setText(f"Win Probability: {win_prob:.1%}")

        self.board_widget.clear_highlights()
        top_moves = list(move_probs.items())

        highlights_to_draw = {}
        for i, label in enumerate(self.top_moves_labels):
            if i < len(top_moves):
                move_uci, prob = top_moves[i]
                label.setText(f"{i + 1}. {move_uci} ({prob:.1%})")

                move = chess.Move.from_uci(move_uci)

                priority = 1 if i == 0 else 0
                color = QColor(SQUARE_COLORS['highlight_best' if priority == 1 else 'highlight_alt'])
                self.board_widget.highlight_move(move, color, priority)

                self.board_widget.highlight_move(move, color, priority)
                highlights_to_draw[move.from_square] = (color, priority)
                highlights_to_draw[move.to_square] = (color, priority)
            else:
                label.setText(f"{i + 1}. --")

        if self.draw_on_screen_toggle.isChecked():
            self.screen_overlay.update_drawing_data(self.board_bbox_on_screen, self.board_widget._highlights)

    def handle_draw_on_screen_toggle(self, checked):
        """Shows or hides the screen overlay."""
        if checked:
            if self.board_bbox_on_screen:
                self.screen_overlay.update_drawing_data(self.board_bbox_on_screen, self.board_widget._highlights)
                self.screen_overlay.show()
            else:
                self.update_status("Capture a board first to enable on-screen drawing.", is_error=True)
                self.draw_on_screen_toggle.setChecked(False)
        else:
            self.screen_overlay.hide()

    def clear_analysis_results(self):
        self.win_prob_label.setText("Win Probability: --%")
        for i, label in enumerate(self.top_moves_labels):
            label.setText(f"{i + 1}. --")

        if self.screen_overlay:
            self.screen_overlay.clear_drawing()

    def handle_realtime_toggle(self, checked):
        """Manages the start and stop of the real-time analysis timer."""
        if checked:
            if self.monitored_screen_geometry is None:
                self.update_status("Please select a monitor to track for real-time analysis.")
                self.capture_screenshot() # This will set the geometry if successful
                return

            self.realtime_timer.start()
            self.update_status("Real-time analysis enabled.", timeout=3000)
            self.screenshot_button.setEnabled(False)
        else:
            self.realtime_timer.stop()
            self.update_status("Real-time analysis disabled.", timeout=3000)
            self.screenshot_button.setEnabled(True)

    def run_realtime_check(self):
        """Function called by the QTimer to re-scan the selected monitor."""
        if self.ocr_worker and self.ocr_worker.isRunning():
            return

        if self.monitored_screen_geometry is None:
            self.realtime_toggle.setChecked(False)  # Safety check
            return

        self.update_status("Checking for board updates...", timeout=1500)
        image_path = self.screenshot_manager.capture_screen_area(self.monitored_screen_geometry)
        if image_path:
            self.start_ocr_process(image_path, ocr_mode='digital')

    def closeEvent(self, event):
        """Ensure the overlay is closed when the main window closes."""
        self.screen_overlay.close()
        super().closeEvent(event)


def _get_stylesheet():
    # Stylesheet remains the same
    return """
        QMainWindow, QWidget { background-color: #2C3E50; color: #ECF0F1; }
        #TitleLabel { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
        #GroupLabel { font-size: 16px; font-weight: bold; margin-top: 15px; color: #BDC3C7; }
        #InfoLabel { font-size: 14px; }
        QPushButton { background-color: #3498DB; color: white; border: none; padding: 10px 15px; border-radius: 5px; font-size: 14px; }
        QPushButton:hover { background-color: #2980B9; }
        QPushButton:pressed { background-color: #1F618D; }
        QPushButton:disabled { background-color: #5D6D7E; }
        QSlider::groove:horizontal { border: 1px solid #bbb; background: #4A6278; height: 8px; border-radius: 4px; }
        QSlider::handle:horizontal { background: #3498DB; border: 1px solid #3498DB; width: 18px; margin: -5px 0; border-radius: 9px; }
        QSlider::add-page:horizontal { background: #4A6278; }
        QSlider::sub-page:horizontal { background: #5DADE2; }
        QStatusBar { background-color: #212F3D; font-size: 12px; }
        QCheckBox { font-size: 14px; spacing: 5px; }
        QCheckBox::indicator { width: 15px; height: 15px; }
    """