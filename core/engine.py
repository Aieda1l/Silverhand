import sys
import torch
import chess

from config import MAIA2_MODELS_DIR, AVAILABLE_MODELS, DEFAULT_MODEL

sys.path.insert(0, str(MAIA2_MODELS_DIR.parent.parent))

from maia2 import model, inference


class EngineManager:
    """
    A wrapper for the Maia2 chess engine that can load and switch between
    different models (e.g., rapid, blitz).
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing Maia2 engine manager on device: {self.device}")

        self.models = {}
        self.prepared_inferences = {}
        self.current_model_type = None

        # Pre-load the default model
        self.load_model(DEFAULT_MODEL)
        self.switch_model(DEFAULT_MODEL)

    def load_model(self, model_type: str):
        """Loads a specific Maia2 model if it hasn't been loaded yet."""
        if model_type not in AVAILABLE_MODELS:
            raise ValueError(f"Model type '{model_type}' is not available.")

        if model_type not in self.models:
            print(f"Loading Maia2 '{model_type}' model...")
            loaded_model = model.from_pretrained(
                type=model_type,
                device=self.device,
                save_root=str(MAIA2_MODELS_DIR)
            )
            self.models[model_type] = loaded_model
            self.prepared_inferences[model_type] = inference.prepare()
            print(f"Model '{model_type}' loaded successfully.")

    def switch_model(self, model_type: str):
        """Switches the active model for inference."""
        if model_type not in self.models:
            self.load_model(model_type)  # Load if not already in memory

        self.current_model_type = model_type
        print(f"Switched active engine to '{model_type}' model.")

    def get_move_predictions(self, board_fen: str, elo: int, player_color: str) -> dict | None:
        """
        Gets move predictions for a board state, skill level, and player color.

        Args:
            board_fen (str): The FEN string for the board position only.
            elo (int): The desired skill level for the prediction.
            player_color (str): The active player's color ('white' or 'black').

        Returns:
            A dictionary of move probabilities or None on failure.
        """
        if not board_fen:
            return None

        active_color_char = 'w' if player_color == 'white' else 'b'
        full_fen = f"{board_fen} {active_color_char} KQkq - 0 1"

        try:
            # Validate the constructed FEN
            chess.Board(full_fen)
        except ValueError:
            print(f"Error: Constructed FEN '{full_fen}' is invalid.")
            return None

        try:
            active_model = self.models[self.current_model_type]
            prepared = self.prepared_inferences[self.current_model_type]

            move_probs, win_prob = inference.inference_each(
                model=active_model,
                prepared=prepared,
                fen=full_fen,
                elo_self=elo,
                elo_oppo=elo
            )

            if not move_probs:
                return None

            return {
                "move_probabilities": move_probs,
                "win_probability": win_prob
            }

        except Exception as e:
            print(f"An error occurred during Maia2 inference: {e}")
            import traceback
            traceback.print_exc()
            return None