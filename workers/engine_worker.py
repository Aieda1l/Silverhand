from PyQt6.QtCore import QThread, pyqtSignal
from core.engine import EngineManager


class EngineWorker(QThread):
    """
    A worker thread for running the Maia2 chess engine inference.
    Prevents the GUI from freezing while the engine is "thinking".
    """
    # Signal arguments: dictionary of predictions
    finished = pyqtSignal(dict)

    # Signal arguments: error message (str)
    error = pyqtSignal(str)

    # Signal to indicate progress
    progress = pyqtSignal(str)

    def __init__(self, fen: str, elo: int, engine_manager: EngineManager):
        super().__init__()
        if not fen:
            raise ValueError("FEN string cannot be None for EngineWorker.")
        self.fen = fen
        self.elo = elo
        self.engine_manager = engine_manager

    def run(self):
        """
        The main entry point for the thread's execution.
        """
        try:
            self.progress.emit(f"Analyzing position at {self.elo} ELO...")

            predictions = self.engine_manager.get_move_predictions(self.fen, self.elo)

            if predictions and predictions.get("move_probabilities"):
                self.progress.emit("Analysis complete. Found best moves.")
                self.finished.emit(predictions)
            else:
                self.error.emit("Engine could not find a valid move for the position.")

        except Exception as e:
            error_message = f"An unexpected error occurred during engine analysis: {e}"
            print(error_message)
            self.error.emit(error_message)