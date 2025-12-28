"use client";

import PlayerCard from "./PlayerCard";
import { Position, PositionType } from "@/types/constants";
import type { PredictionPlayer, DreamTeamPlayer } from "@/types";

type DisplayPlayer = (PredictionPlayer | DreamTeamPlayer) & {
  points: number;
};

interface PitchViewProps {
  players: DisplayPlayer[];
  isPrediction?: boolean;
  formation?: string;
}

export default function PitchView({
  players,
  isPrediction = false,
  formation = "4-4-2",
}: PitchViewProps) {
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

  const renderRow = (
    rowPlayers: DisplayPlayer[],
    position: PositionType,
    className: string
  ) => (
    <div className={`flex justify-center gap-4 ${className}`}>
      {rowPlayers.map((player) => (
        <PlayerCard
          key={player.player_id}
          webName={player.web_name}
          position={position}
          teamShortName={player.team_short_name}
          teamFplId={player.team_fpl_id}
          points={player.points}
          isPredicted={isPrediction}
          isTopScorer={player.player_id === topScorer?.player_id}
        />
      ))}
    </div>
  );

  return (
    <div className="pitch-container p-6 max-w-3xl mx-auto">
      {/* Goal area (top) */}
      <div className="relative mb-8">
        {/* Goal line */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-white/30 rounded" />
        {/* Penalty area */}
        <div className="absolute top-1 left-1/2 -translate-x-1/2 w-64 h-24 border-2 border-white/30 rounded-b-lg" />
        {/* Goal box */}
        <div className="absolute top-1 left-1/2 -translate-x-1/2 w-32 h-10 border-2 border-white/30 rounded-b" />
      </div>

      {/* Players */}
      <div className="space-y-6 pt-16">
        {/* Goalkeeper */}
        {gkp.length > 0 && renderRow(gkp, Position.GKP, "mb-8")}

        {/* Defenders */}
        {def.length > 0 && renderRow(def, Position.DEF, "mb-6")}

        {/* Midfielders */}
        {mid.length > 0 && renderRow(mid, Position.MID, "mb-6")}

        {/* Forwards */}
        {fwd.length > 0 && renderRow(fwd, Position.FWD, "mb-4")}
      </div>

      {/* Center circle */}
      <div className="absolute bottom-1/3 left-1/2 -translate-x-1/2 w-24 h-24 border-2 border-white/20 rounded-full" />

      {/* Halfway line */}
      <div className="absolute bottom-1/3 left-0 right-0 h-0.5 bg-white/20" />

      {/* Formation label */}
      <div className="absolute bottom-2 right-2 bg-white/10 px-2 py-1 rounded text-xs text-white/60">
        {formation}
      </div>
    </div>
  );
}
