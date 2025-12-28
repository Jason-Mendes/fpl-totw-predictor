/**
 * Type definitions for FPL TOTW Predictor.
 *
 * These types mirror the backend Pydantic schemas.
 * For API types, see api.generated.ts (generated from OpenAPI schema).
 */

export interface Team {
  id: number;
  fpl_id: number;
  name: string;
  short_name: string | null;
}

export interface Player {
  id: number;
  fpl_id: number;
  web_name: string;
  first_name: string | null;
  second_name: string | null;
  position: "GKP" | "DEF" | "MID" | "FWD";
  team_id: number | null;
  team_name: string | null;
  team_short_name: string | null;
  now_cost: number | null;
}

export interface Gameweek {
  id: number;
  fpl_id: number;
  name: string | null;
  deadline: string | null;
  finished: boolean;
  is_current: boolean;
  is_next: boolean;
}

export interface PredictionPlayer {
  player_id: number;
  player_fpl_id: number;
  web_name: string;
  position: "GKP" | "DEF" | "MID" | "FWD";
  team_short_name: string | null;
  position_slot: number;
  predicted_points: number;
  predicted_minutes: number | null;
  start_probability: number | null;
  confidence: number | null;
}

export interface Prediction {
  id: number;
  gameweek_id: number;
  gameweek_fpl_id: number;
  model_version: string | null;
  created_at: string;
  total_predicted_points: number | null;
  formation: string | null;
  players: PredictionPlayer[];
}

export interface DreamTeamPlayer {
  player_id: number;
  player_fpl_id: number;
  web_name: string;
  position: "GKP" | "DEF" | "MID" | "FWD";
  team_short_name: string | null;
  position_slot: number;
  points: number;
}

export interface DreamTeam {
  gameweek_id: number;
  gameweek_fpl_id: number;
  total_points: number;
  players: DreamTeamPlayer[];
}

export interface BacktestResult {
  gameweek_id: number;
  gameweek_fpl_id: number;
  player_overlap: number;
  points_ratio: number;
  actual_total: number;
  predicted_total: number;
  created_at: string;
}

export interface BacktestSummary {
  total_gameweeks: number;
  avg_overlap: number;
  avg_points_ratio: number;
  min_overlap: number;
  max_overlap: number;
  weeks_above_9: number;
  weeks_above_8: number;
  results: BacktestResult[];
}

export interface SyncResult {
  teams: number;
  gameweeks: number;
  players: number;
  fixtures: number;
  player_stats: number;
  dream_teams: number;
}
