# utils.py

import logging
from typing import List, Tuple


def is_number(value: any) -> bool:
    """
    Checks if a given value can be interpreted as a number.
    Equivalent to the isNumber function in utils.ts.
    """
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, str):
        return value.isdigit()
    return False


def normalize_fen_string(fen: str) -> List[str]:
    """
    Replaces numbers in a FEN string with a series of '1's, representing
    empty squares, and returns a flat list of 64 characters.

    Example:
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR" ->
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r', 'p', 'p', '1', 'p', 'p', 'p', 'p', 'p', ...]
    """
    normalized_list = []
    # Process each part of the FEN string separated by '/'
    for part in fen.split('/'):
        for char in part:
            if char.isdigit():
                # Expand the number into a corresponding count of '1's
                normalized_list.extend(['1'] * int(char))
            else:
                # Add the piece character directly
                normalized_list.append(char)

    if len(normalized_list) != 64:
        logging.warning(
            f"Normalized FEN string resulted in {len(normalized_list)} squares, not 64. "
            f"FEN: '{fen}'"
        )

    return normalized_list


def parse_fen_from_array(fen_array: List[str]) -> Tuple[str, str]:
    """
    Parses a "normalized" 64-element array back to a regular FEN string
    and its 180-degree rotated equivalent.

    Example (for a single row):
        ["1","1","1","r","Q","1","1","1"] -> "3rQ3"
    """
    if len(fen_array) != 64:
        raise ValueError("Input FEN array must contain exactly 64 elements.")

    fen_rows = []
    # Process the flat list in chunks of 8 (for each row)
    for i in range(8):
        row_slice = fen_array[i * 8: (i + 1) * 8]
        row_fen_str = ""
        empty_squares = 0

        for piece in row_slice:
            # In the TS code, 's', ' ', or any number represents an empty square.
            # Here, we'll primarily look for '1' as per normalize_fen_string.
            if piece == '1' or piece == 's' or piece == ' ':
                empty_squares += 1
            else:
                if empty_squares > 0:
                    row_fen_str += str(empty_squares)
                    empty_squares = 0
                row_fen_str += piece

        # Append any remaining count of empty squares at the end of the row
        if empty_squares > 0:
            row_fen_str += str(empty_squares)

        fen_rows.append(row_fen_str)

    # Join all row strings with '/' to form the complete FEN
    regular_fen = "/".join(fen_rows)

    # Create the reversed FEN for the black perspective (180-degree rotation)
    # This is done by reversing the order of rows, and then reversing each row
    reversed_rows = [row[::-1] for row in reversed(fen_rows)]
    reversed_fen = "/".join(reversed_rows)

    return regular_fen, reversed_fen