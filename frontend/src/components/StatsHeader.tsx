"use client";

interface StatsHeaderProps {
  totalPoints: number;
  topScorerName: string;
  topScorerPoints: number;
  isPrediction?: boolean;
}

export default function StatsHeader({
  totalPoints,
  topScorerName,
  topScorerPoints,
  isPrediction = false,
}: StatsHeaderProps) {
  return (
    <div className="flex justify-center gap-12 mb-6">
      {/* Total Points */}
      <div className="text-center">
        <div className="text-white/70 text-sm mb-1">
          {isPrediction ? "Predicted Points" : "Total Points"}
        </div>
        <div className="bg-gradient-to-br from-fpl-cyan to-fpl-green w-20 h-20 rounded-lg flex items-center justify-center shadow-lg">
          <span className="text-fpl-purple text-3xl font-bold">{totalPoints}</span>
        </div>
        <div className="text-white/50 text-xs mt-1">
          {isPrediction ? "Est." : "Actual"} →
        </div>
      </div>

      {/* Player of the Week */}
      <div className="text-center">
        <div className="text-white/70 text-sm mb-1">
          {isPrediction ? "Predicted Star" : "Player of the Week"}
        </div>
        <div className="bg-fpl-purple-light/50 rounded-lg p-3 border border-fpl-purple-light/30">
          <div className="w-14 h-14 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center mx-auto mb-1">
            <span className="text-2xl">⭐</span>
          </div>
          <div className="text-white font-semibold">{topScorerName}</div>
          <div className="text-fpl-green text-sm font-bold">
            {isPrediction ? "~" : ""}
            {topScorerPoints}pts
          </div>
        </div>
      </div>
    </div>
  );
}
