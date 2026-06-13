export type ChinesePokerPhase =
  | "placing"
  | "betting"
  | "showdown"
  | "hand_complete"
  | "done";

export type ChinesePokerAction =
  | { type: "place"; column: number }
  | { type: "fold" }
  | { type: "check" }
  | { type: "call" }
  | { type: "raise"; to: number }
  | { type: "ready" };

export type ChinesePokerPlayer = {
  seat: number;
  stack: number;
  in_tournament: boolean;
  in_hand: boolean;
  columns: string[][];
  folded: boolean;
  all_in: boolean;
  committed_round: number;
  committed_hand: number;
  last_action: ChinesePokerAction | null;
};

export type ChinesePokerState = {
  tick: number;
  hand_number: number;
  phase: ChinesePokerPhase;
  button: number;
  deck: string[];
  pot: number;
  current_bet: number;
  min_raise: number;
  action_on: number | null;
  acted_this_round: number[];
  players: ChinesePokerPlayer[];
  history: {
    hand: number;
    phase: string;
    seat: number;
    action: ChinesePokerAction;
  }[];
  placement: number[];
  pot_distribution: { seat: number; amount: number }[] | null;
  showdown_hands: Record<string, string[]> | null;
  winning_columns: Record<string, number[]> | null;
  current_drawn_card: string | null;
};
