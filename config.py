import os
from pathlib import Path

from PyQt6.QtGui import QColor

# --- Project Paths ---
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"
RESOURCES_DIR = UI_DIR / "resources"
PIECES_DIR = RESOURCES_DIR / "pieces"
VENDOR_DIR = BASE_DIR / "vendor"
LC2FEN_DIR = VENDOR_DIR / "lc2fen"
MAIA2_MODELS_DIR = VENDOR_DIR / "maia2" / "maia2_models"
LC2FEN_MODELS_DIR = LC2FEN_DIR / "data" / "models"
TEMP_DIR = BASE_DIR / "temp"
CHESS_DETECTOR_DIR = VENDOR_DIR / "chess_detector"
CHESS_DETECTOR_MODELS_DIR = CHESS_DETECTOR_DIR / "models"
DETECTION_MODEL_PATH = CHESS_DETECTOR_MODELS_DIR / "detection_model.pt"
CLASSIFICATION_MODEL_PATH = CHESS_DETECTOR_MODELS_DIR / "classification_model.h5"

# Ensure temporary directory exists
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LC2FEN_MODELS_DIR, exist_ok=True)


# --- Application Settings ---
APP_NAME = "Silverhand Chess Bot"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700


# --- Chess Engine (Maia2) Settings ---
# A single slider will control both the player's and opponent's ELO for simplicity.
# This simulates playing against an opponent of equal skill.
ELO_MIN = 1100
ELO_MAX = 2500
ELO_STEP = 100  # The slider will move in increments of 100 ELO.
ELO_DEFAULT = 1800
AVAILABLE_MODELS = ["rapid", "blitz"]
DEFAULT_MODEL = "rapid"


# --- Chessboard OCR (LiveChess2FEN) Settings ---
# We use the ONNX model for a good balance of speed and accuracy.
# This model will be downloaded automatically if not present.
LC2FEN_MODEL_FILENAME = "MobileNetV2_0p5_all.onnx"
LC2FEN_MODEL_PATH = LC2FEN_MODELS_DIR / LC2FEN_MODEL_FILENAME
LC2FEN_IMG_SIZE = 224

# The position of the 'a1' square in the captured image.
# Common for online chess platforms like lichess.org and chess.com.
# Options: "BL" (Bottom-Left), "BR" (Bottom-Right), "TL" (Top-Left), "TR" (Top-Right)
A1_POSITION = "BL"


# --- Real-time Analysis Settings ---
# The toggle will control this mode. The value is the refresh rate in milliseconds.
REALTIME_ANALYSIS_INTERVAL_MS = 1000 # Check for board changes every 2 seconds.


# --- UI and Chessboard Appearance ---
BOARD_SIZE = 560  # Pixel dimensions of the chessboard widget
SQUARE_COLORS = {
    "light": "#F0D9B5",
    "dark": "#B58863",
    "highlight_best": QColor(20, 255, 20, 155), # Green for best move
    "highlight_alt": QColor(20, 20, 255, 155),   # Blue for alternate moves
    "highlight_last": QColor(255, 255, 0, 155) # Yellow for last move made (by OCR)
}


# --- Resource Paths ---
ICONS_DIR = RESOURCES_DIR / "icons"
APP_ICON_PATH = ICONS_DIR / "app_icon.png"
SPLASH_IMAGE_PATH = ICONS_DIR / "app_splash.png"


# --- File Paths for captured images ---
WEBCAM_CAPTURE_PATH = TEMP_DIR / "webcam_capture.png"
SCREENSHOT_CAPTURE_PATH = TEMP_DIR / "screenshot.png"
CROPPED_BOARD_PATH = TEMP_DIR / "cropped_board.png"