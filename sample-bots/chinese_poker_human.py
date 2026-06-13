"""Human-interactive bot for Chinese Poker (Five-O)."""

from __future__ import annotations

import sys

from vibewarz import (
    ChinesePokerBot,
    ChinesePokerCheckAction,
    ChinesePokerCallAction,
    ChinesePokerFoldAction,
    ChinesePokerPlaceAction,
    ChinesePokerRaiseAction,
    ChinesePokerState,
)


class ChinesePokerHumanBot(ChinesePokerBot):
    display_name = "Human"

    def act(self, state: ChinesePokerState):
        legal = self.legal_actions(state)
        if not legal:
            return ChinesePokerCheckAction()  # safety fallback
            
        print("\n" + "="*40)
        print(f"--- Hand {state.hand_number} | Phase: {state.phase} | Pot: {state.pot} ---")
        
        my_player = state.player(self.seat)
        print("Your board:")
        for i, col in enumerate(my_player.columns):
            print(f"  Col {i}: {col}")
            
        if state.phase == "placing":
            print(f"\nDrawn Card: {state.current_drawn_card}")
            
        print("\nLegal Actions:")
        for i, action in enumerate(legal):
            print(f"  [{i}] {action}")
            
        while True:
            try:
                choice = input(f"Choose an action (0-{len(legal)-1}): ")
                idx = int(choice.strip())
                if 0 <= idx < len(legal):
                    action_dict = legal[idx]
                    
                    if action_dict["type"] == "place":
                        return ChinesePokerPlaceAction(column=action_dict["column"])
                    elif action_dict["type"] == "check":
                        return ChinesePokerCheckAction()
                    elif action_dict["type"] == "call":
                        return ChinesePokerCallAction()
                    elif action_dict["type"] == "fold":
                        return ChinesePokerFoldAction()
                    elif action_dict["type"] == "raise":
                        # If the action has 'max_raise' and 'min_raise', we might want to prompt
                        min_r = action_dict.get("min_raise", state.min_raise)
                        max_r = action_dict.get("max_raise", my_player.stack)
                        amt = input(f"Raise amount ({min_r} - {max_r}) [default {min_r}]: ")
                        if not amt.strip():
                            amt_val = min_r
                        else:
                            amt_val = int(amt.strip())
                        return ChinesePokerRaiseAction(to=amt_val)
                    
                    # Fallback if something else
                    return action_dict
            except Exception as e:
                print(f"Invalid input: {e}")

