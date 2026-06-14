export type ChinesePokerPhase = "placing" | "done";

export type ChinesePokerAction = { type: "place"; column: number };

export type ChinesePokerPlayer = {
  seat: number;
  columns: string[][];
  last_action: ChinesePokerAction | null;
};

export type ChinesePokerState = {
  tick: number;
  phase: ChinesePokerPhase;
  deck: string[];
  action_on: number | null;
  players: ChinesePokerPlayer[];
  history: {
    seat: number;
    action: ChinesePokerAction;
  }[];
  placement: number[];
  winner: number | null;
  showdown_hands: Record<string, string[]> | null;
  winning_columns: Record<string, number[]> | null;
  current_drawn_card: string | null;
};
