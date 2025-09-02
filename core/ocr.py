import shutil
import sys
import os
from pathlib import Path

import requests
from tqdm import tqdm
from PIL import Image

# --- Add vendor directories to Python path ---
from config import (
    LC2FEN_DIR, LC2FEN_MODEL_PATH, LC2FEN_IMG_SIZE, A1_POSITION, CROPPED_BOARD_PATH,
    CHESS_DETECTOR_DIR, DETECTION_MODEL_PATH, CLASSIFICATION_MODEL_PATH
)

sys.path.insert(0, str(LC2FEN_DIR.parent))
sys.path.insert(0, str(CHESS_DETECTOR_DIR.parent))

# --- Conditional Imports ---
# Import lc2fen components for physical board OCR
from lc2fen.predict_board import predict_board_onnx
from keras.applications.mobilenet_v2 import preprocess_input as prein_mobilenet

# Import chess_detector for digital board OCR
from chess_detector import ChessboardDetector


class OCRManager:
    """
    A unified manager for chessboard OCR that can use different libraries
    for digital (screenshots) and physical (webcam) chessboards.
    """
    _ONNX_MODEL_URL = "https://github.com/davidmallasen/LiveChess2FEN/releases/download/v1.0.0-models/MobileNetV2_0p5_all.onnx"

    def __init__(self, mode: str):
        """
        Initializes the OCR manager in a specific mode.

        Args:
            mode (str): The operating mode, either 'digital' or 'physical'.
        """
        if mode not in ['digital', 'physical']:
            raise ValueError("Mode must be either 'digital' or 'physical'.")

        self.mode = mode
        self.detector = None

        print(f"Initializing OCRManager in '{self.mode}' mode...")
        if self.mode == 'digital':
            # TODO: Add logic to download chess_detector models if they don't exist
            # For now, we assume they are present as per the user's setup.
            if not (DETECTION_MODEL_PATH.exists() and CLASSIFICATION_MODEL_PATH.exists()):
                raise FileNotFoundError(
                    "Digital OCR models not found. Please place 'detection_model.pt' and "
                    "'classification_model.h5' in the 'vendor/chess_detector/models/' directory."
                )
            self.detector = ChessboardDetector(
                detection_model_path=str(DETECTION_MODEL_PATH),
                classification_model_path=str(CLASSIFICATION_MODEL_PATH)
            )
        elif self.mode == 'physical':
            self._ensure_lc2fen_model_exists()
        print("OCRManager initialized successfully.")

    def _ensure_lc2fen_model_exists(self):
        """
        Checks if the lc2fen ONNX model file exists. If not, downloads it.
        (Used for 'physical' mode).
        """
        if not LC2FEN_MODEL_PATH.exists():
            print(f"LiveChess2FEN model not found. Downloading to {LC2FEN_MODEL_PATH}...")
            try:
                # (Downloading logic remains the same as before)
                response = requests.get(self._ONNX_MODEL_URL, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                with open(LC2FEN_MODEL_PATH, 'wb') as f, tqdm(...) as bar:
                    # ... (omitted for brevity, same as before)
                    pass
                print("Model downloaded successfully.")
            except Exception as e:
                # ... (error handling remains the same)
                raise ConnectionError("Failed to download the required lc2fen model.")

    def analyze_board(self, image_path: str) -> tuple[list, str | None, str | None]:
        """
        Analyzes the given image using the configured OCR engine.

        Args:
            image_path (str): The path to the image of the chessboard.

        Returns:
            A tuple containing:
            - The predicted FEN string (White's perspective), or None on failure.
            - The path to the cropped board image, or None on failure.
        """
        if self.mode == 'digital':
            return self._analyze_digital(image_path)
        else:  # self.mode == 'physical'
            return self._analyze_physical(image_path)

    def _analyze_digital(self, image_path: str) -> tuple[list, str | None, str | None]:
        """Uses the chess_detector library for digital boards."""
        try:
            results = self.detector.process_image(image_path, confidence_threshold=0.6)
            if not results:
                return None, None

            # Assume the highest confidence board is the correct one
            best_board = max(results, key=lambda x: x['score'])
            fen = best_board['fen']['white_perspective']

            # Crop and save the detected board for UI preview
            image = Image.open(image_path)
            box = best_board['box']
            cropped_image = image.crop(box)
            cropped_image.save(CROPPED_BOARD_PATH)

            return box, fen, str(CROPPED_BOARD_PATH)

        except Exception as e:
            print(f"An error occurred during digital OCR processing: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def _analyze_physical(self, image_path: str) -> tuple[str | None, str | None, str | None]:
        """Uses the lc2fen library for physical boards."""
        try:
            predicted_fen, board_found = predict_board_onnx(
                model_path=str(LC2FEN_MODEL_PATH),
                img_size=LC2FEN_IMG_SIZE,
                preprocess_input=prein_mobilenet,
                path=image_path,
                a1_pos=A1_POSITION,
                previous_fen=None,
                output_path=str(CROPPED_BOARD_PATH.parent)
            )

            if board_found and predicted_fen:
                return None, predicted_fen, str(CROPPED_BOARD_PATH)
            else:
                return None, None, None

        except Exception as e:
            print(f"An error occurred during physical OCR processing: {e}")
            import traceback
            traceback.print_exc()
            return None, None

        finally:
            # Clean up the temporary directory created by lc2fen
            image_dir = Path(image_path).parent
            tmp_dir = image_dir / "tmp"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)


if __name__ == '__main__':
    # Example usage for testing
    # You need a test image named 'test_board.png' in the root directory
    test_image_path = "../../test_board.png"  # You'll need to provide an image for this test

    if not os.path.exists(test_image_path):
        print(f"Test image not found at {test_image_path}. Skipping OCR test.")
    else:
        print("Initializing OCR Manager...")
        ocr_manager = OCRManager()
        print("Analyzing test board image...")
        fen, cropped_path = ocr_manager.analyze_board(test_image_path)

        if fen:
            print(f"Successfully predicted FEN: {fen}")
            print(f"Cropped board saved to: {cropped_path}")
        else:
            print("Failed to predict FEN from the image.")