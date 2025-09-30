# Silverhand

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![made-with-love](https://img.shields.io/badge/Made%20with-❤️-red.svg)](https://shields.io/)

**Silverhand** is a modern, real-time chess assistant designed to enhance your gameplay and learning. Using state-of-the-art AI, Silverhand analyzes chessboards directly from your screen and provides human-like move suggestions, helping you navigate complex positions with confidence.

 ![Silverhand App](https://github.com/Aieda1l/Silverhand/blob/main/media/app.png)

## Features

-   **Instant Board Recognition**: Capture any digital chessboard on your screen with a single click. Silverhand uses a powerful YOLO-based model (`chess_detector`) to instantly recognize the board and piece positions.
-   **Human-like AI Suggestions**: Powered by **Maia-2**, a neural network trained on millions of human games, Silverhand provides move suggestions that feel natural and instructive, not superhuman.
-   **Adjustable Skill Level**: Tune the engine's playing strength with a simple ELO slider (from 1100 to 2500), allowing you to get advice tailored to your level.
-   **Real-time Analysis Mode**: Enable this mode to have Silverhand continuously monitor a selected screen region, automatically detecting board changes and providing updated move suggestions in real-time.
-   **On-Screen Highlights**: Toggle on-screen drawing to see the top recommended moves highlighted directly over the chessboard on your screen, providing seamless, non-intrusive guidance.
-   **Beautiful & Modern UI**: A clean, professional, and intuitive user interface built with PyQt6.

## Requirements

-   Python 3.9+
-   An internet connection (for first-time model downloads).
-   A CUDA-enabled GPU is recommended for best performance but not required (the application will run on CPU).

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Aieda1l/Silverhand.git
    cd silverhand-chess-bot
    ```

2.  **Create a Virtual Environment:**
    It is highly recommended to use a virtual environment to manage dependencies.

    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Install all required Python packages using the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installation may include large packages like `torch` and `tensorflow`, which might take some time.*

4.  **Download AI Models (Handled Automatically):**
    The first time you run the application, it will automatically download the necessary models for Maia-2 and the OCR engines. Please ensure you have a stable internet connection.

## How to Use

1.  **Launch the Application:**
    Run the `main.py` script from the root of the project directory.

    ```bash
    python main.py
    ```

2.  **Configure Settings (Left Panel):**
    -   **My Color**: Select whether you are playing as White or Black. This tells the engine whose turn it is to move.
    -   **Engine Model**: Choose between "Rapid" and "Blitz" models from Maia-2, trained on different time controls.
    -   **Engine Skill Level (ELO)**: Adjust the slider to set the desired playing strength for move suggestions.

3.  **Capture a Board:**
    -   Click **"Capture Digital Board"**.
    -   An overlay will appear. Click on the monitor that displays the chessboard.
    -   Silverhand will automatically detect the board within that monitor, analyze the position, and display the result.

4.  **Analyze the Results (Right Panel):**
    -   The application will show the top 3 human-like moves predicted by Maia-2.
    -   The best move will be highlighted in **green** and alternate moves in **blue**, both on the in-app preview board and directly on your screen (if enabled).

5.  **Enable Real-time Mode:**
    -   Check the **"Real-time Analysis (Digital)"** box.
    -   If you haven't captured a board yet, you will be prompted to select a monitor to track.
    -   Silverhand will now automatically re-scan the board every few seconds and update its suggestions whenever the position changes.

6.  **Toggle On-Screen Highlights:**
    -   Check the **"Draw Highlights on Screen"** box to see move suggestions as a non-intrusive overlay directly on your game. Uncheck it to hide them.

## Project Structure

The project is organized with a clear separation of concerns:
-   `main.py`: The main entry point of the application.
-   `config.py`: Contains all application settings and paths.
-   `core/`: Contains the core logic wrappers for image capture, OCR, and the chess engines.
-   `ui/`: Contains all GUI-related code, including the main window, chessboard widget, and screen overlay.
-   `workers/`: Manages background threads to keep the UI responsive during intensive tasks.
-   `vendor/`: Contains the third-party libraries `maia2` and `chess_detector`.

## License

This project is licensed under the CC BY-NC License. See the `LICENSE` file for more details.