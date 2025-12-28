/**
 * API client for the FPL TOTW backend.
 */

import type {
  BacktestSummary,
  DreamTeam,
  Gameweek,
  Prediction,
  SyncResult,
} from "@/types";

/**
 * Get the API base URL based on execution context.
 * - Server-side (SSR): Use API_URL for Docker inter-container networking
 * - Client-side (browser): Use NEXT_PUBLIC_API_URL for host access
 */
function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    // Server-side: use internal Docker URL
    return process.env.API_URL || "http://localhost:8000";
  }
  // Client-side: use public URL (browser needs to access via exposed port)
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

const API_BASE_URL = getApiBaseUrl();

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
}

// Gameweeks
export async function getGameweeks(): Promise<Gameweek[]> {
  return fetchApi<Gameweek[]>("/api/gameweeks");
}

export async function getCurrentGameweek(): Promise<Gameweek | null> {
  return fetchApi<Gameweek | null>("/api/gameweeks/current");
}

export async function getNextGameweek(): Promise<Gameweek | null> {
  return fetchApi<Gameweek | null>("/api/gameweeks/next");
}

export async function getGameweek(gwId: number): Promise<Gameweek> {
  return fetchApi<Gameweek>(`/api/gameweeks/${gwId}`);
}

// Predictions
export async function getPrediction(gwId: number): Promise<Prediction | null> {
  return fetchApi<Prediction | null>(`/api/predictions/${gwId}`);
}

export async function generatePrediction(gwId: number): Promise<Prediction> {
  return fetchApi<Prediction>(`/api/predictions/generate/${gwId}`, {
    method: "POST",
  });
}

// Dream Team (actual)
export async function getDreamTeam(gwId: number): Promise<DreamTeam | null> {
  return fetchApi<DreamTeam | null>(`/api/predictions/dream-team/${gwId}`);
}

// Backtest
export async function getBacktestSummary(): Promise<BacktestSummary> {
  return fetchApi<BacktestSummary>("/api/backtest/summary");
}

export async function runBacktest(
  startGw?: number,
  endGw?: number
): Promise<BacktestSummary> {
  const params = new URLSearchParams();
  if (startGw) params.append("start_gw", startGw.toString());
  if (endGw) params.append("end_gw", endGw.toString());

  return fetchApi<BacktestSummary>(`/api/backtest/run?${params}`, {
    method: "POST",
  });
}

// Sync
export async function syncFplData(): Promise<SyncResult> {
  return fetchApi<SyncResult>("/api/sync/fpl", {
    method: "POST",
  });
}

// Health
export async function checkHealth(): Promise<{ status: string; version: string }> {
  return fetchApi<{ status: string; version: string }>("/api/health");
}
