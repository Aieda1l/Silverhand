from PyQt6.QtCore import QThread, pyqtSignal
from core.ocr import OCRManager


class OCRWorker(QThread):
    """
    A dedicated worker thread for running the chessboard OCR process.
    This prevents the GUI from freezing during analysis.
    """
    # Signal arguments: bbox list, FEN string (str), cropped board image path (str)
    finished = pyqtSignal(object, str, str)

    # Signal arguments: error message (str)
    error = pyqtSignal(str)

    # Signal to indicate progress
    progress = pyqtSignal(str)

    def __init__(self, image_path: str, ocr_manager: OCRManager):
        super().__init__()
        if not image_path:
            raise ValueError("Image path cannot be None for OCRWorker.")
        self.image_path = image_path
        self.ocr_manager = ocr_manager

    def run(self):
        """
        The main entry point for the thread's execution.
        """
        try:
            self.progress.emit("Detecting and analyzing board...")

            bbox, fen, cropped_path = self.ocr_manager.analyze_board(self.image_path)

            if fen and cropped_path:
                self.progress.emit(f"Board found. FEN: {fen}")
                self.finished.emit(bbox, fen, cropped_path)
            else:
                self.error.emit("Could not detect a chessboard in the image.")

        except Exception as e:
            error_message = f"An unexpected error occurred during OCR: {e}"
            print(error_message)
            self.error.emit(error_message)