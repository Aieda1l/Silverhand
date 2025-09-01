# detector.py

import logging
from typing import List, Dict, Any, Union

from PIL import Image
from ultralytics import YOLO

# Import the handler that contains the piece classification logic
from .ml_handler import MLHandler


class ChessboardDetector:
    """
    A user-friendly facade for detecting and analyzing chessboards in images.

    This class uses a YOLO model from the Ultralytics library for board detection
    and a custom-trained Keras model for piece classification.
    """

    def __init__(
            self,
            detection_model_path: str,
            classification_model_path: str
    ):
        """
        Initializes the detector by loading all necessary machine learning models.

        Args:
            detection_model_path: Path to the trained YOLO detection model
                                  (e.g., 'best.pt' or a TensorFlow SavedModel
                                  directory exported from YOLO).
            classification_model_path: Path to the Keras .h5 model file for
                                       piece classification.
        """
        logging.info("Initializing Chessboard Detector...")

        # 1. Load the YOLO detection model using the Ultralytics library.
        # The library handles loading different formats (.pt, .onnx, saved_model) automatically.
        try:
            logging.info(f"Loading detection model from: {detection_model_path}")
            self._detection_model = YOLO(detection_model_path)
            logging.info("✅ Detection model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load YOLO detection model: {e}")
            raise IOError(f"Could not load the detection model from '{detection_model_path}'.")

        # 2. Instantiate the ML handler for piece classification.
        # This will load the Keras model and prepare the TF Hub feature extractor.
        self._ml_handler = MLHandler(
            classification_model_path=classification_model_path
        )

        logging.info("✅ ChessboardDetector is ready.")

    def process_image(self, image_source: Union[str, Image.Image], confidence_threshold: float = 0.5) -> List[
        Dict[str, Any]]:
        """
        Detects all chessboards in an image and generates FEN strings for each.

        This is the main method of the library.

        Args:
            image_source: The source of the image. This can be either a file
                          path (string) or a pre-loaded Pillow Image object.
            confidence_threshold: The minimum confidence score for a detected
                                  chessboard to be processed (0.0 to 1.0).

        Returns:
            A list of dictionaries, where each dictionary represents one
            detected chessboard.
        """
        try:
            if isinstance(image_source, str):
                image = Image.open(image_source).convert("RGB")
            elif isinstance(image_source, Image.Image):
                image = image_source.convert("RGB")
            else:
                raise TypeError("image_source must be a file path (str) or a Pillow Image object.")
        except FileNotFoundError:
            logging.error(f"Error: The file '{image_source}' was not found.")
            return []
        except Exception as e:
            logging.error(f"Error: Could not open or process the image. Reason: {e}")
            return []

        # 1. Detect chessboards using the YOLO model.
        # The `predict` method returns a list of Results objects.
        logging.info("Detecting chessboards in the image...")
        yolo_results = self._detection_model.predict(image, conf=confidence_threshold, verbose=False)

        # We expect only one image was processed, so we take the first result.
        detected_boards = yolo_results[0].boxes

        if len(detected_boards) == 0:
            logging.info("No chessboards detected.")
            return []

        logging.info(f"Found {len(detected_boards)} potential chessboard(s).")
        final_results = []

        # 2. For each detected board, crop it and classify the pieces.
        for i, board in enumerate(detected_boards):
            logging.info(f"--- Processing board {i + 1} ---")

            # Extract bounding box coordinates and score
            box_coords = board.xyxy[0].cpu().numpy().astype(int)
            score = board.conf[0].cpu().numpy()

            # Crop the detected board from the main image
            cropped_board_image = image.crop(box_coords)

            # Classify the pieces on the cropped board to get the FEN strings
            regular_fen, reversed_fen = self._ml_handler.classification.classify_board(
                cropped_board_image
            )

            # Assemble the final result dictionary
            result = {
                "box": box_coords.tolist(),
                "score": float(score),
                "fen": {
                    "white_perspective": regular_fen,
                    "black_perspective": reversed_fen
                }
            }
            final_results.append(result)

        return final_results