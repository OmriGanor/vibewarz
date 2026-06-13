import { useState, useEffect } from "react";
import { ChinesePokerBoard } from "@vibewarz/game-ui";
import type { ChinesePokerState, ChinesePokerAction } from "@vibewarz/game-ui/dist/types";

export function LiveApp() {
  const [state, setState] = useState<ChinesePokerState | null>(null);

  useEffect(() => {
    // Poll /state every 500ms
    const interval = setInterval(() => {
      fetch("/state")
        .then(r => r.json())
        .then(data => {
          if (data) setState(data);
        })
        .catch(console.error);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const handleAction = (action: ChinesePokerAction) => {
    fetch("/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action),
    }).catch(console.error);
  };

  if (!state) {
    return <div className="vw-app__error">Waiting for game to start...</div>;
  }

  // Assuming human is always seat 0 in play_ui.py
  const humanSeat = 0;
  
  const seatInfo = [
    { seat: 0, handle: "You", is_bot: false, bot_label: null },
    { seat: 1, handle: "Bot", is_bot: true, bot_label: "Bot" },
  ];

  return (
    <>
      <p className="vw-app__title">
        <strong>Live Play</strong> · chinese_poker
      </p>
      <div style={{ height: "600px" }}>
        <ChinesePokerBoard 
          state={state} 
          seatInfo={seatInfo} 
          onAction={handleAction} 
          humanSeat={humanSeat} 
        />
      </div>
    </>
  );
}
