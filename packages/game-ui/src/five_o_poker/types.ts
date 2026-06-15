export type FiveOPokerPhase = "placing" | "done";

export type FiveOPokerAction = { type: "place"; column: number };

export type FiveOPokerPlayer = {
  seat: number;
  columns: string[][];
  last_action: FiveOPokerAction | null;
};

export type FiveOPokerState = {
  tick: number;
  phase: FiveOPokerPhase;
  deck: string[];
  action_on: number | null;
  players: FiveOPokerPlayer[];
  history: {
    seat: number;
    action: FiveOPokerAction;
  }[];
  placement: number[];
  winner: number | null;
  showdown_hands: Record<string, string[]> | null;
  winning_columns: Record<string, number[]> | null;
  current_drawn_card: string | null;
};
