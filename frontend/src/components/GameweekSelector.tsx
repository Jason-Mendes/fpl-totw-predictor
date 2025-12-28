"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface GameweekSelectorProps {
  currentGw: number;
  maxGw: number;
  minGw?: number;
  onSelect: (gw: number) => void;
}

export default function GameweekSelector({
  currentGw,
  maxGw,
  minGw = 1,
  onSelect,
}: GameweekSelectorProps) {
  const canGoBack = currentGw > minGw;
  const canGoForward = currentGw < maxGw;

  return (
    <div className="flex items-center justify-center gap-4">
      {/* Previous button */}
      <button
        onClick={() => canGoBack && onSelect(currentGw - 1)}
        disabled={!canGoBack}
        className={`p-2 rounded-full transition-colors ${
          canGoBack
            ? "bg-fpl-purple-light hover:bg-fpl-purple-light/80 text-white"
            : "bg-gray-600 text-gray-400 cursor-not-allowed"
        }`}
        aria-label="Previous gameweek"
      >
        <ChevronLeftIcon />
      </button>

      {/* Gameweek display */}
      <div className="text-center min-w-[160px]">
        <div className="text-2xl font-bold text-white">Gameweek {currentGw}</div>
      </div>

      {/* Next button */}
      <button
        onClick={() => canGoForward && onSelect(currentGw + 1)}
        disabled={!canGoForward}
        className={`p-2 rounded-full transition-colors ${
          canGoForward
            ? "bg-fpl-purple-light hover:bg-fpl-purple-light/80 text-white"
            : "bg-gray-600 text-gray-400 cursor-not-allowed"
        }`}
        aria-label="Next gameweek"
      >
        <ChevronRightIcon />
      </button>
    </div>
  );
}

// Simple chevron icons (avoiding external dependency)
function ChevronLeftIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}
