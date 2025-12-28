"use client";

import { PositionColors, PositionType } from "@/types/constants";

interface PlayerCardProps {
  webName: string;
  position: PositionType;
  teamShortName: string | null;
  points: number;
  isPredicted?: boolean;
  isTopScorer?: boolean;
}

export default function PlayerCard({
  webName,
  position,
  teamShortName,
  points,
  isPredicted = false,
  isTopScorer = false,
}: PlayerCardProps) {
  const positionColor = PositionColors[position];

  return (
    <div className="player-card flex flex-col items-center">
      {/* Jersey/Avatar */}
      <div
        className="relative w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mb-1"
        style={{
          backgroundColor: positionColor,
          color: position === "GKP" ? "#000" : "#fff",
          boxShadow: isTopScorer ? "0 0 12px 4px rgba(255, 215, 0, 0.6)" : "none",
        }}
      >
        {/* Team badge placeholder */}
        <span className="text-xs">{teamShortName?.slice(0, 3) || "---"}</span>

        {/* Top scorer indicator */}
        {isTopScorer && (
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center">
            <span className="text-xs text-black font-bold">★</span>
          </div>
        )}
      </div>

      {/* Player name */}
      <div
        className="bg-white text-fpl-purple px-2 py-0.5 rounded text-xs font-semibold truncate max-w-[80px] text-center"
        title={webName}
      >
        {webName}
      </div>

      {/* Points */}
      <div
        className={`mt-1 px-3 py-0.5 rounded text-sm font-bold ${
          isPredicted
            ? "bg-fpl-purple-light text-white"
            : "bg-fpl-green text-fpl-purple"
        }`}
      >
        {isPredicted ? points.toFixed(0) : points}
      </div>
    </div>
  );
}
