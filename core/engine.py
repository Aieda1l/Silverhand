import sys
import torch

from config import MAIA2_MODELS_DIR

# Add the vendor directory to the Python path to allow importing maia2
sys.path.insert(0, str(MAIA2_MODELS_DIR.parent.parent))

from maia2 import model, inference


class EngineManager:
    """
    A wrapper for the Maia2 chess engine to predict human-like moves.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EngineManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_type="rapid"):
        if not hasattr(self, 'initialized'):  # Ensure __init__ runs only once
            self.model_type = model_type
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Initializing Maia2 engine on device: {self.device}")

            # The from_pretrained function handles model downloading
            self.model = model.from_pretrained(
                type=self.model_type,
                device=self.device,
                save_root=str(MAIA2_MODELS_DIR)
            )

            # Prepare for position-wise inference to avoid re-initializing
            self.prepared_inference = inference.prepare()
            self.initialized = True
            print("Maia2 engine initialized successfully.")

    def get_move_predictions(self, fen: str, elo: int) -> dict | None:
        """
        Gets move predictions for a given board state (FEN) and skill level (ELO).

        Args:
            fen (str): The FEN string representing the current board state.
            elo (int): The desired skill level for the prediction.

        Returns:
            A dictionary of move probabilities (e.g., {'e2e4': 0.45, ...}),
            sorted by probability, or None if an error occurs.
        """
        if not fen:
            return None

        try:
            # Maia2 uses the same ELO for both self and opponent in its training data context
            # for single-agent prediction, so we pass the same value.
            move_probs, win_prob = inference.inference_each(
                model=self.model,
                prepared=self.prepared_inference,
                fen=fen,
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


if __name__ == '__main__':
    # Example usage for testing
    print("Testing Maia2 Engine Manager...")

    try:
        engine = EngineManager()

        # --- Test 1: Starting position ---
        start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        test_elo = 1800
        print(f"\n--- Analyzing starting position (FEN: {start_fen}) at {test_elo} ELO ---")

        predictions = engine.get_move_predictions(start_fen, test_elo)

        if predictions and predictions["move_probabilities"]:
            print(f"Win Probability for White: {predictions['win_probability']:.2%}")
            print("Top 5 predicted moves:")
            top_5 = list(predictions["move_probabilities"].items())[:5]
            for move, prob in top_5:
                print(f"  - Move: {move}, Probability: {prob:.2%}")
        else:
            print("Failed to get predictions for the starting position.")

        # --- Test 2: A mid-game position ---
        mid_game_fen = "r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"  # Sicilian Defense
        test_elo_2 = 1500
        print(f"\n--- Analyzing mid-game position at {test_elo_2} ELO ---")

        predictions_2 = engine.get_move_predictions(mid_game_fen, test_elo_2)

        if predictions_2 and predictions_2["move_probabilities"]:
            print(f"Win Probability for White: {predictions_2['win_probability']:.2%}")
            print("Top 5 predicted moves:")
            top_5_2 = list(predictions_2["move_probabilities"].items())[:5]
            for move, prob in top_5_2:
                print(f"  - Move: {move}, Probability: {prob:.2%}")
        else:
            print("Failed to get predictions for the mid-game position.")

    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")