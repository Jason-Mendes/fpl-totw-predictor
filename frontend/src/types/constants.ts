/**
 * FPL Constants - Auto-generated from shared/constants.json
 * DO NOT EDIT MANUALLY - Run `npm run generate:constants` to regenerate
 *
 * This file is kept in sync with the backend Python constants.
 * If you see TypeScript errors here, the constants may have changed.
 */

import constants from "../../../shared/constants.json";

// Re-export the raw constants
export const SHARED_CONSTANTS = constants;

// Typed exports for better DX
export const Position = constants.positions as {
  readonly GKP: "GKP";
  readonly DEF: "DEF";
  readonly MID: "MID";
  readonly FWD: "FWD";
};

export type PositionType = (typeof Position)[keyof typeof Position];

export const PlayerStatus = constants.playerStatus as {
  readonly AVAILABLE: "a";
  readonly DOUBTFUL: "d";
  readonly INJURED: "i";
  readonly NOT_AVAILABLE: "n";
  readonly SUSPENDED: "s";
  readonly UNAVAILABLE: "u";
};

export type PlayerStatusType = (typeof PlayerStatus)[keyof typeof PlayerStatus];

export const Formations = constants.formations as readonly string[];

export type FormationType = (typeof Formations)[number];

export const FormationConstraints = constants.formationConstraints as {
  readonly minGkp: number;
  readonly maxGkp: number;
  readonly minDef: number;
  readonly maxDef: number;
  readonly minMid: number;
  readonly maxMid: number;
  readonly minFwd: number;
  readonly maxFwd: number;
  readonly totalPlayers: number;
};

export const PointsSystem = constants.pointsSystem as {
  readonly minutes1To59: number;
  readonly minutes60Plus: number;
  readonly goalGkp: number;
  readonly goalDef: number;
  readonly goalMid: number;
  readonly goalFwd: number;
  readonly assist: number;
  readonly cleanSheetGkp: number;
  readonly cleanSheetDef: number;
  readonly cleanSheetMid: number;
  readonly cleanSheetFwd: number;
  readonly goalsConcededGkp: number;
  readonly goalsConcededDef: number;
  readonly savesBonus: number;
  readonly penaltySaved: number;
  readonly penaltyMissed: number;
  readonly yellowCard: number;
  readonly redCard: number;
  readonly ownGoal: number;
  readonly maxBonus: number;
};

export const RollingWindows = constants.rollingWindows as readonly number[];

export const MinGameweeksForPrediction = constants.minGameweeksForPrediction;

export const FplApiBaseUrl = constants.fplApiBaseUrl;

// Position display names for UI
export const PositionDisplayNames: Record<PositionType, string> = {
  GKP: "Goalkeeper",
  DEF: "Defender",
  MID: "Midfielder",
  FWD: "Forward",
};

// Position colors for UI (matching FPL theme)
export const PositionColors: Record<PositionType, string> = {
  GKP: "#ebff00", // Yellow
  DEF: "#00ff87", // Green
  MID: "#05f0ff", // Cyan
  FWD: "#e90052", // Pink/Red
};

// Helper to get goal points for a position
export function getGoalPoints(position: PositionType): number {
  const mapping: Record<PositionType, number> = {
    GKP: PointsSystem.goalGkp,
    DEF: PointsSystem.goalDef,
    MID: PointsSystem.goalMid,
    FWD: PointsSystem.goalFwd,
  };
  return mapping[position];
}

// Helper to get clean sheet points for a position
export function getCleanSheetPoints(position: PositionType): number {
  const mapping: Record<PositionType, number> = {
    GKP: PointsSystem.cleanSheetGkp,
    DEF: PointsSystem.cleanSheetDef,
    MID: PointsSystem.cleanSheetMid,
    FWD: PointsSystem.cleanSheetFwd,
  };
  return mapping[position];
}
