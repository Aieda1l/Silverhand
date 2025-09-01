# ml_handler.py

import logging
from typing import List, Tuple, Dict, Any

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image
from tqdm import tqdm

# Import the utility functions we created earlier
from . import utils

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# --- Constants ---
# The TF Hub URL for the feature extractor
MOBILENET_URL = "https://tfhub.dev/google/imagenet/mobilenet_v3_small_100_224/feature_vector/5"
MOBILENET_INPUT_SIZE = 224


class MLHandler:
    """
    A class to encapsulate the piece classification model loading and inference.
    Detection logic has been moved out to leverage the Ultralytics library directly.
    """

    def __init__(self, classification_model_path: str):
        """
        Initializes the handler by loading the piece classification model.

        Args:
            classification_model_path: Path to the saved Keras classification model (.h5 file).
        """
        classification_model = self._load_classification_model(classification_model_path)

        # Instantiate the helper, passing the loaded classification model
        self.classification = self.ClassificationHelper(
            classification_model=classification_model
        )
        logging.info("MLHandler for classification is initialized and ready.")

    def _load_classification_model(self, model_path: str) -> tf.keras.Model:
        """Loads the Keras piece classification model."""
        logging.info(f"Loading piece classification model from '{model_path}'...")
        try:
            model = tf.keras.models.load_model(model_path, custom_objects={'KerasLayer': hub.KerasLayer})
            logging.info("Classification model loaded successfully.")
            return model
        except Exception as e:
            logging.error(f"Error loading classification model: {e}")
            raise IOError(f"Failed to load the Keras model from '{model_path}'. Check path and model integrity.") from e

    class ClassificationHelper:
        """
        Handles classification of pieces on a detected chessboard.
        This class now manages its own feature extractor.
        """
        CHESS_PIECES_LOOKUP = {
            0: "p", 1: "r", 2: "n", 3: "b", 4: "q", 5: "k",  # Black
            6: "P", 7: "R", 8: "N", 9: "B", 10: "Q", 11: "K",  # White
            12: "s"  # Empty square
        }

        def __init__(self, classification_model: tf.keras.Model):
            self.classification_model = classification_model
            # Lazily load the feature extractor on first use
            self._feature_extractor = None

        @property
        def feature_extractor(self) -> hub.KerasLayer:
            """
            Lazily loads the MobileNetV3 model from TensorFlow Hub on first access.
            This avoids loading the model until it's actually needed.
            """
            if self._feature_extractor is None:
                logging.info(f"Loading MobileNet feature extractor from TF Hub: {MOBILENET_URL}")
                self._feature_extractor = hub.KerasLayer(
                    MOBILENET_URL,
                    input_shape=(MOBILENET_INPUT_SIZE, MOBILENET_INPUT_SIZE, 3),
                    trainable=False
                )
                logging.info("✅ MobileNet feature extractor is ready.")
            return self._feature_extractor

        def _extract_tile_features(self, board_image: Image.Image) -> List[np.ndarray]:
            """
            Crops a board into 64 tiles, preprocesses them, and extracts features for each.
            """
            tile_width = board_image.width / 8
            tile_height = board_image.height / 8

            tile_images = []

            # First, crop all 64 tiles from the board image
            for i in range(64):
                row = i // 8
                col = i % 8

                x1 = col * tile_width
                y1 = row * tile_height
                x2 = x1 + tile_width
                y2 = y1 + tile_height

                # Crop and resize the tile
                tile_image = board_image.crop((x1, y1, x2, y2))
                tile_image = tile_image.resize((MOBILENET_INPUT_SIZE, MOBILENET_INPUT_SIZE))
                tile_images.append(np.array(tile_image))

            # Convert list of images to a NumPy array and normalize
            image_batch = np.array(tile_images) / 255.0

            # Use the feature extractor to get features for all tiles in one batch
            # A KerasLayer is called like a function, not with .predict()
            features_batch = self.feature_extractor(image_batch)  # <-- The fix is on this line

            return features_batch

        def _classify_tiles(self, tile_features: np.ndarray) -> List[str]:
            """Predicts the piece on each tile based on its features using a batch prediction."""
            # Run batch prediction on all features at once for performance
            predictions = self.classification_model.predict(tile_features, verbose=0)

            # Find the piece with the max probability for each tile
            predicted_indices = np.argmax(predictions, axis=1)

            fen_array = [self.CHESS_PIECES_LOOKUP.get(index, 's') for index in predicted_indices]

            return fen_array

        def classify_board(self, board_image: Image.Image) -> Tuple[str, str]:
            """
            Classifies a single cropped chessboard image and returns the FEN strings.
            This is the main public method of this helper class.
            """
            print("Classifying pieces on the detected board...")

            # Ensure the image is in RGB format
            board_image_rgb = board_image.convert("RGB")

            tile_features = self._extract_tile_features(board_image_rgb)
            fen_array = self._classify_tiles(tile_features)

            # Use the utility function to convert the array to FEN strings
            regular_fen, reversed_fen = utils.parse_fen_from_array(fen_array)

            print("Classification complete.")
            return regular_fen, reversed_fen