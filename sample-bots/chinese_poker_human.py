"""Human-interactive bot for Chinese Poker (Five-O)."""

from __future__ import annotations

from vibewarz import (
    ChinesePokerBot,
    ChinesePokerPlaceAction,
    ChinesePokerState,
)


class ChinesePokerHumanBot(ChinesePokerBot):
    display_name = "Human"

    def act(self, state: ChinesePokerState):
        legal = self.legal_actions(state)
        if not legal:
            return ChinesePokerPlaceAction(column=0)  # shouldn't be reached

        print("\n" + "=" * 40)
        print(f"--- Phase: {state.phase} ---")

        my_player = state.player(self.seat)
        print("Your board:")
        for i, col in enumerate(my_player.columns):
            print(f"  Col {i}: {col}")
        print(f"\nDrawn card: {state.current_drawn_card}")

        legal_columns = [a["column"] for a in legal]
        print(f"Place it in one of columns: {legal_columns}")

        while True:
            try:
                choice = input(f"Choose a column {legal_columns}: ").strip()
                column = int(choice)
                if column in legal_columns:
                    return ChinesePokerPlaceAction(column=column)
                print("That column is not currently legal.")
            except (ValueError, EOFError) as e:
                print(f"Invalid input: {e}")
