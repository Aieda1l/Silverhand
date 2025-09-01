# __init__.py

# Set the version of the library
__version__ = "0.2.0" # Bumped version for the new architecture

# Import the main class from the detector module to make it directly
# accessible when the package is imported. This allows users to write
# `from chess_detector import ChessboardDetector` instead of the more
# verbose `from chess_detector.detector import ChessboardDetector`.
from .detector import ChessboardDetector

# You can also expose other useful components if desired, for example:
# from .ml_handler import MLHandler
# from .utils import parse_fen_from_array