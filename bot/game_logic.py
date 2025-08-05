# /bot/game_logic.py (Final, Perfected Version)

import random
from typing import Dict, List, Any

# --- Constants for Board Layout ---
# Using constants makes the code cleaner and easier to modify.
HOME_YARD = -1  # Represents a token in the home yard (not on the board)
HOME_STRETCH_START = 52 # The first position in any home stretch
HOME_POSITION = 58 # The final position indicating a token is home and cannot move

# Entry points for each of the 4 players (Red, Green, Yellow, Blue)
START_POSITIONS = [0, 13, 26, 39]
# The board position just before a token enters its home stretch
HOME_ENTRY_POSITIONS = [50, 11, 24, 37]

# Safe zones on the main board path
SAFE_ZONES = [0, 8, 13, 21, 26, 34, 39, 47]


class LudoGame:
    """
    Manages the state and rules of a single Ludo game.
    This class is self-contained and does not interact with the Telegram API directly.
    """

    def __init__(self, players: List[int], win_condition: int):
        # We assign players to colors based on their order in the list.
        player_colors = ['🔴', '🟢', '🟡', '🔵']
        self.players: Dict[int, Dict[str, Any]] = {
            player_id: {
                'tokens': [HOME_YARD] * 4,  # All 4 tokens start in the yard
                'color': player_colors[i],
                'player_index': i
            } for i, player_id in enumerate(players)
        }
        
        self.win_condition = win_condition
        self.player_order = players
        self.current_player_index = 0
        self.dice_roll = 0
        self.consecutive_sixes = 0

    def get_current_player_id(self) -> int:
        """Returns the Telegram ID of the player whose turn it is."""
        return self.player_order[self.current_player_index]

    def roll_dice(self) -> int:
        """
        Rolls a standard 1-6 die and handles the logic for extra turns
        and losing a turn after three consecutive sixes.
        """
        self.dice_roll = random.randint(1, 6)
        
        if self.dice_roll == 6:
            self.consecutive_sixes += 1
            if self.consecutive_sixes == 3:
                self.consecutive_sixes = 0
                self.dice_roll = 0 # Reset dice roll
                # This indicates a lost turn. The next player should be selected.
                return -1
        else:
            self.consecutive_sixes = 0
            
        return self.dice_roll

    def get_movable_tokens(self, player_id: int) -> List[int]:
        """
        Determines which of a player's tokens can legally move based on the current dice roll.
        Returns a list of token indices (0-3).
        """
        if self.dice_roll == 0:
            return []

        player_data = self.players[player_id]
        movable = []
        
        for i, pos in enumerate(player_data['tokens']):
            # A token can leave the yard only on a roll of 6.
            if pos == HOME_YARD and self.dice_roll == 6:
                movable.append(i)
                continue

            # A token cannot move if it's already home.
            if pos == HOME_POSITION:
                continue

            # A token in the home stretch can only move with an exact roll.
            if pos >= HOME_STRETCH_START:
                if pos + self.dice_roll <= HOME_POSITION:
                    movable.append(i)
                continue
            
            # For tokens on the main path, any move is potentially valid.
            if pos != HOME_YARD:
                movable.append(i)
                
        return movable

    def move_token(self, player_id: int, token_index: int) -> str:
        """
        Executes the move for a given token, handles entering the board,
        moving along the path, entering the home stretch, and knocking out opponents.
        """
        player_data = self.players[player_id]
        current_pos = player_data['tokens'][token_index]
        player_idx = player_data['player_index']

        # --- Rule 1: Entering a token from the yard ---
        if current_pos == HOME_YARD and self.dice_roll == 6:
            start_pos = START_POSITIONS[player_idx]
            self._knock_out_opponents_at(start_pos, player_id)
            player_data['tokens'][token_index] = start_pos
            return "entered"

        # --- Rule 2: Moving into the home stretch ---
        home_entry = HOME_ENTRY_POSITIONS[player_idx]
        if current_pos <= home_entry < current_pos + self.dice_roll:
            # The token passes its home entry point, so it moves into the home stretch.
            steps_past_entry = (current_pos + self.dice_roll) - home_entry
            new_pos = HOME_STRETCH_START + steps_past_entry - 1
            player_data['tokens'][token_index] = new_pos
            return "homeward"

        # --- Rule 3: Moving within the home stretch or reaching home ---
        if current_pos >= HOME_STRETCH_START:
            new_pos = current_pos + self.dice_roll
            player_data['tokens'][token_index] = new_pos
            if new_po