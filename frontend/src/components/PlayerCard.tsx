"use client";

import { useState } from "react";
import Image from "next/image";
import { PositionColors, PositionType } from "@/types/constants";

// Map FPL team IDs (1-20) to badge filenames (using badge CDN codes)
// FPL API ID -> Badge CDN code -> filename
const TEAM_BADGE_MAP: Record<number, string> = {
  1: "arsenal_3",         // Arsenal
  2: "aston-villa_7",     // Aston Villa
  3: "burnley_90",        // Burnley
  4: "bournemouth_91",    // Bournemouth
  5: "brentford_94",      // Brentford
  6: "brighton_36",       // Brighton
  7: "chelsea_8",         // Chelsea
  8: "crystal-palace_31", // Crystal Palace
  9: "everton_11",        // Everton
  10: "fulham_54",        // Fulham
  11: "leeds_2",          // Leeds
  12: "liverpool_14",     // Liverpool
  13: "man-city_43",      // Man City
  14: "man-utd_1",        // Man Utd
  15: "newcastle_4",      // Newcastle
  16: "nottm-forest_17",  // Nottm Forest
  17: "sunderland_56",    // Sunderland
  18: "tottenham_6",      // Spurs
  19: "west-ham_21",      // West Ham
  20: "wolves_39",        // Wolves
};

interface PlayerCardProps {
  webName: string;
  position: PositionType;
  teamShortName: string | null;
  teamFplId: number | null;
  points: number;
  isPredicted?: boolean;
  isTopScorer?: boolean;
}

export default function PlayerCard({
  webName,
  position,
  teamShortName,
  teamFplId,
  points,
  isPredicted = false,
  isTopScorer = false,
}: PlayerCardProps) {
  const positionColor = PositionColors[position];
  const [imageError, setImageError] = useState(false);

  // Get badge filename from mapping, fallback to ID-based naming
  const badgeFileName = teamFplId ? TEAM_BADGE_MAP[teamFplId] : null;
  const badgeSrc = badgeFileName ? `/badges/${badgeFileName}.png` : null;

  return (
    <div className="player-card flex flex-col items-center">
      {/* Team Badge */}
      <div
        className="relative w-14 h-14 flex items-center justify-center mb-1"
        style={{
          filter: isTopScorer ? "drop-shadow(0 0 8px rgba(255, 215, 0, 0.8))" : "none",
        }}
      >
        {badgeSrc && !imageError ? (
          <Image
            src={badgeSrc}
            alt={teamShortName || "Team badge"}
            width={56}
            height={56}
            className="object-contain"
            onError={() => setImageError(true)}
          />
        ) : (
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center text-xs font-bold"
            style={{
              backgroundColor: positionColor,
              color: position === "GKP" ? "#000" : "#fff",
            }}
          >
            {teamShortName?.slice(0, 3) || "---"}
          </div>
        )}

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
