import sys
import time
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from config import APP_ICON_PATH, SPLASH_IMAGE_PATH


def main():
    """
    The main entry point for the Silverhand application.
    Initializes the application, shows a splash screen, loads the main window,
    and starts the event loop.
    """
    app = QApplication(sys.argv)

    # --- Set Application Icon ---
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    else:
        print(f"Warning: Application icon not found at {APP_ICON_PATH}")

    # --- Create and Show Splash Screen ---
    splash = None
    if SPLASH_IMAGE_PATH.exists():
        splash_pix = QPixmap(str(SPLASH_IMAGE_PATH))

        # --- SOLUTION: Scale splash screen if it's too big ---
        screen_size = app.primaryScreen().size()
        max_height = int(screen_size.height() * 0.6)
        max_width = int(screen_size.width() * 0.6)

        if splash_pix.height() > max_height or splash_pix.width() > max_width:
            splash_pix = splash_pix.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        # --- END SOLUTION ---

        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        app.processEvents()
    else:
        print(f"Warning: Splash image not found at {SPLASH_IMAGE_PATH}")

    # --- Load Main Window ---
    if splash:
        splash.showMessage(
            "Loading AI models...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.white
        )

    start_time = time.time()
    window = MainWindow()
    load_time = time.time() - start_time

    if load_time < 2.5:  # Ensure splash is visible for a bit
        time.sleep(2.5 - load_time)

    window.show()

    if splash:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == '__main__':
    from pathlib import Path

    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))

    main()