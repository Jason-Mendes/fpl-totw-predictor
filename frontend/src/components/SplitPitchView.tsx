"use client";

import PlayerCard from "./PlayerCard";
import { Position, PositionType } from "@/types/constants";
import type { PredictionPlayer, DreamTeamPlayer } from "@/types";

type DisplayPlayer = (PredictionPlayer | DreamTeamPlayer) & {
  points: number;
};

interface SplitPitchViewProps {
  predictionPlayers: DisplayPlayer[];
  actualPlayers: DisplayPlayer[];
  formation?: string;
  activeView: "prediction" | "actual";
}

export default function SplitPitchView({
  predictionPlayers,
  actualPlayers,
  formation = "4-4-2",
  activeView,
}: SplitPitchViewProps) {
  // Find matched players (in both teams)
  const predictionIds = new Set(predictionPlayers.map((p) => p.player_id));
  const actualIds = new Set(actualPlayers.map((p) => p.player_id));
  const matchedIds = new Set(
    Array.from(predictionIds).filter((id) => actualIds.has(id))
  );

  const renderHalf = (
    players: DisplayPlayer[],
    isPrediction: boolean,
    side: "left" | "right"
  ) => {
    // Group players by position
    const gkp = players.filter((p) => p.position === Position.GKP);
    const def = players.filter((p) => p.position === Position.DEF);
    const mid = players.filter((p) => p.position === Position.MID);
    const fwd = players.filter((p) => p.position === Position.FWD);

    // Find top scorer
    const topScorer = players.reduce(
      (max, p) => (p.points > (max?.points || 0) ? p : max),
      players[0]
    );

    const isActive = isPrediction
      ? activeView === "prediction"
      : activeView === "actual";

    const renderRow = (
      rowPlayers: DisplayPlayer[],
      position: PositionType,
      className: string
    ) => (
      <div className={`flex justify-center gap-1 sm:gap-2 ${className}`}>
        {rowPlayers.map((player) => {
          const isMatched = matchedIds.has(player.player_id);
          return (
            <div
              key={player.player_id}
              className={`transition-all duration-200 ${
                isMatched ? "ring-2 ring-fpl-green ring-offset-1 ring-offset-transparent rounded-lg" : ""
              }`}
            >
              <PlayerCard
                webName={player.web_name}
                position={position}
                teamShortName={player.team_short_name}
                teamFplId={player.team_fpl_id}
                points={player.points}
                isPredicted={isPrediction}
                isTopScorer={player.player_id === topScorer?.player_id}
              />
            </div>
          );
        })}
      </div>
    );

    return (
      <div
        className={`flex-1 px-2 py-4 transition-opacity duration-200 ${
          isActive ? "opacity-100" : "opacity-60"
        } ${side === "left" ? "border-r border-white/20" : ""}`}
      >
        {/* Label */}
        <div className={`text-center mb-4 ${isActive ? "text-white" : "text-white/60"}`}>
          <span className="text-sm font-semibold uppercase tracking-wide">
            {isPrediction ? "Prediction" : "Actual"}
          </span>
        </div>

        {/* Players */}
        <div className="space-y-4">
          {/* Goalkeeper */}
          {gkp.length > 0 && renderRow(gkp, Position.GKP, "mb-6")}

          {/* Defenders */}
          {def.length > 0 && renderRow(def, Position.DEF, "mb-4")}

          {/* Midfielders */}
          {mid.length > 0 && renderRow(mid, Position.MID, "mb-4")}

          {/* Forwards */}
          {fwd.length > 0 && renderRow(fwd, Position.FWD, "")}
        </div>
      </div>
    );
  };

  const hasBothTeams = predictionPlayers.length > 0 && actualPlayers.length > 0;

  if (!hasBothTeams) {
    // Fallback to single view if only one team available
    const players = predictionPlayers.length > 0 ? predictionPlayers : actualPlayers;
    const isPrediction = predictionPlayers.length > 0;

    return (
      <div className="pitch-container p-6 max-w-3xl mx-auto">
        {renderHalf(players, isPrediction, "left")}
        <div className="absolute bottom-2 right-2 bg-white/10 px-2 py-1 rounded text-xs text-white/60">
          {formation}
        </div>
      </div>
    );
  }

  return (
    <div className="pitch-container p-4 max-w-5xl mx-auto">
      {/* Split pitch with both teams */}
      <div className="flex">
        {/* Left side - Prediction */}
        {renderHalf(predictionPlayers, true, "left")}

        {/* Right side - Actual */}
        {renderHalf(actualPlayers, false, "right")}
      </div>

      {/* Matched players count */}
      <div className="mt-4 text-center">
        <span className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full text-sm">
          <span className="w-3 h-3 bg-fpl-green rounded-full" />
          <span className="text-white">
            {matchedIds.size}/11 players matched
          </span>
        </span>
      </div>

      {/* Formation label */}
      <div className="absolute bottom-2 right-2 bg-white/10 px-2 py-1 rounded text-xs text-white/60">
        {formation}
      </div>
    </div>
  );
}
