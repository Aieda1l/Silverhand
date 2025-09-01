import sys
import os
import requests
from tqdm import tqdm
import shutil
from pathlib import Path

# Add the vendor directory to the Python path to allow importing lc2fen
from config import LC2FEN_DIR, LC2FEN_MODEL_PATH, LC2FEN_IMG_SIZE, A1_POSITION, CROPPED_BOARD_PATH

sys.path.insert(0, str(LC2FEN_DIR.parent))

# Need to import keras preprocessor before predict_board to avoid tensorflow init issues
from keras.applications.mobilenet_v2 import preprocess_input as prein_mobilenet
from lc2fen.predict_board import predict_board_onnx


class OCRManager:
    """
    A wrapper for the LiveChess2FEN library to perform chessboard OCR.
    """
    _ONNX_MODEL_URL = "https://github.com/davidmallasen/LiveChess2FEN/releases/download/v1.0.0-models/MobileNetV2_0p5_all.onnx"

    def __init__(self):
        self._ensure_model_exists()

    def _ensure_model_exists(self):
        """
        Checks if the ONNX model file exists. If not, it downloads the model.
        """
        if not LC2FEN_MODEL_PATH.exists():
            print(f"LiveChess2FEN model not found. Downloading to {LC2FEN_MODEL_PATH}...")
            try:
                response = requests.get(self._ONNX_MODEL_URL, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))

                with open(LC2FEN_MODEL_PATH, 'wb') as f, tqdm(
                        desc=LC2FEN_MODEL_PATH.name,
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        bar.update(size)
                print("Model downloaded successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Error downloading model: {e}")
                if LC2FEN_MODEL_PATH.exists():
                    os.remove(LC2FEN_MODEL_PATH)
                raise ConnectionError("Failed to download the required OCR model.")

    def analyze_board(self, image_path: str) -> tuple[str | None, str | None]:
        """
        Analyzes the given image to detect the chessboard and predict its FEN.

        Args:
            image_path (str): The path to the image of the chessboard.

        Returns:
            A tuple containing:
            - The predicted FEN string, or None if detection fails.
            - The path to the cropped and saved board image, or None if detection fails.
        """
        try:
            # The library creates a 'tmp' folder in the same directory as the input image.
            image_dir = Path(image_path).parent
            tmp_dir = image_dir / "tmp"

            # predict_board_onnx returns a tuple (fen, board_corners) or (fen, bool_board_found)
            # The second element seems to be inconsistent, but we only need the FEN.
            result = predict_board_onnx(
                model_path=str(LC2FEN_MODEL_PATH),
                img_size=LC2FEN_IMG_SIZE,
                pre_input=prein_mobilenet,
                path=image_path,
                a1_pos=A1_POSITION,
                previous_fen=None,
            )

            predicted_fen = result[0] if isinstance(result, tuple) else None

            final_cropped_path = None
            if predicted_fen:
                # Find the cropped image inside the library's temp folder
                if tmp_dir.exists():
                    image_filename = Path(image_path).name
                    source_cropped_path = tmp_dir / image_filename
                    if source_cropped_path.exists():
                        # Copy it to our app's temp folder for the UI to use
                        shutil.copy(source_cropped_path, CROPPED_BOARD_PATH)
                        final_cropped_path = str(CROPPED_BOARD_PATH)
                    else:
                        print(f"Warning: lc2fen did not save a cropped board image at {source_cropped_path}")

            return predicted_fen, final_cropped_path

        except Exception as e:
            print(f"An error occurred during OCR processing: {e}")
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