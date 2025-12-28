"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import PitchView from "@/components/PitchView";
import SplitPitchView from "@/components/SplitPitchView";
import GameweekSelector from "@/components/GameweekSelector";
import StatsHeader from "@/components/StatsHeader";
import {
  getGameweeks,
  getCurrentGameweek,
  getPrediction,
  getDreamTeam,
  generatePrediction,
  syncFplData,
} from "@/lib/api";
import type { Gameweek, Prediction, DreamTeam, PredictionPlayer, DreamTeamPlayer } from "@/types";

export default function Home() {
  const [gameweeks, setGameweeks] = useState<Gameweek[]>([]);
  const [selectedGw, setSelectedGw] = useState<number>(1);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [dreamTeam, setDreamTeam] = useState<DreamTeam | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"prediction" | "actual">("prediction");

  // Load gameweeks on mount
  useEffect(() => {
    loadGameweeks();
  }, []);

  // Load prediction and dream team when GW changes
  useEffect(() => {
    if (selectedGw > 0) {
      loadData(selectedGw);
    }
  }, [selectedGw]);

  async function loadGameweeks() {
    try {
      const gws = await getGameweeks();
      setGameweeks(gws);

      // Set to current or last finished gameweek
      const current = gws.find((g) => g.is_current);
      const lastFinished = [...gws].reverse().find((g) => g.finished);

      if (current) {
        setSelectedGw(current.fpl_id);
      } else if (lastFinished) {
        setSelectedGw(lastFinished.fpl_id);
      } else if (gws.length > 0) {
        setSelectedGw(gws[0].fpl_id);
      }
    } catch (e) {
      setError("Failed to load gameweeks. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  async function loadData(gwId: number) {
    setLoading(true);
    setError(null);

    try {
      const [pred, actual] = await Promise.all([
        getPrediction(gwId),
        getDreamTeam(gwId),
      ]);
      setPrediction(pred);
      setDreamTeam(actual);
    } catch (e) {
      console.error("Failed to load data:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setError(null);

    try {
      const result = await syncFplData();
      await loadGameweeks();
      alert(
        `Synced: ${result.teams} teams, ${result.players} players, ${result.player_stats} stats`
      );
    } catch (e) {
      setError("Failed to sync data");
    } finally {
      setSyncing(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    setError(null);

    try {
      const pred = await generatePrediction(selectedGw);
      setPrediction(pred);
    } catch (e) {
      setError("Failed to generate prediction. Need more historical data.");
    } finally {
      setGenerating(false);
    }
  }

  const maxGw = gameweeks.length > 0 ? Math.max(...gameweeks.map((g) => g.fpl_id)) : 38;
  const currentGwData = gameweeks.find((g) => g.fpl_id === selectedGw);

  // Convert prediction players to display format
  const predictionPlayers = prediction?.players.map((p) => ({
    ...p,
    points: Math.round(p.predicted_points),
  })) || [];

  // Convert dream team players to display format
  const dreamTeamPlayers = dreamTeam?.players.map((p) => ({
    ...p,
    points: p.points,
  })) || [];

  const displayPlayers = viewMode === "prediction" ? predictionPlayers : dreamTeamPlayers;
  const totalPoints =
    viewMode === "prediction"
      ? prediction?.total_predicted_points || 0
      : dreamTeam?.total_points || 0;

  const topPlayer = displayPlayers.length > 0
    ? displayPlayers.reduce(
        (max, p) => (p.points > (max?.points || 0) ? p : max),
        displayPlayers[0]
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Team of the Week</h1>
          <p className="text-muted-foreground">
            {viewMode === "prediction" ? "ML-Predicted Dream Team" : "Actual Dream Team"}
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleSync}
            disabled={syncing}
          >
            {syncing ? "Syncing..." : "Sync Data"}
          </Button>
          <Button
            variant="fpl"
            onClick={handleGenerate}
            disabled={generating || !currentGwData}
          >
            {generating ? "Generating..." : "Generate Prediction"}
          </Button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <Card className="bg-destructive/10 border-destructive">
          <CardContent className="py-4">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Gameweek selector */}
      <GameweekSelector
        currentGw={selectedGw}
        maxGw={maxGw}
        minGw={1}
        onSelect={setSelectedGw}
      />

      {/* Stats header */}
      {displayPlayers.length > 0 && topPlayer && (
        <StatsHeader
          totalPoints={totalPoints}
          topScorerName={topPlayer.web_name}
          topScorerPoints={topPlayer.points}
          isPrediction={viewMode === "prediction"}
        />
      )}

      {/* Centered View Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex bg-fpl-purple-light/50 rounded-full p-1">
          <button
            onClick={() => setViewMode("prediction")}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              viewMode === "prediction"
                ? "bg-fpl-green text-fpl-purple"
                : "text-white hover:text-fpl-green"
            }`}
          >
            Prediction
          </button>
          <button
            onClick={() => setViewMode("actual")}
            disabled={!dreamTeam}
            className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
              viewMode === "actual"
                ? "bg-fpl-green text-fpl-purple"
                : "text-white hover:text-fpl-green disabled:opacity-50 disabled:cursor-not-allowed"
            }`}
          >
            Actual
          </button>
        </div>
      </div>

      {/* Pitch View */}
      <div className="relative">
        {/* Loading overlay */}
        {(loading || generating) && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10 rounded-lg">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-12 h-12 text-fpl-green animate-spin" />
              <span className="text-white font-medium">
                {generating ? "Generating prediction..." : "Loading..."}
              </span>
            </div>
          </div>
        )}

        {/* Content */}
        {prediction && dreamTeam ? (
          <SplitPitchView
            predictionPlayers={predictionPlayers}
            actualPlayers={dreamTeamPlayers}
            formation={prediction.formation || "4-4-2"}
            activeView={viewMode}
          />
        ) : prediction ? (
          <PitchView
            players={predictionPlayers}
            isPrediction={true}
            formation={prediction.formation || "4-4-2"}
          />
        ) : dreamTeam ? (
          <PitchView
            players={dreamTeamPlayers}
            isPrediction={false}
            formation="4-4-2"
          />
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">
                No prediction yet. Click "Generate Prediction" to create one.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Comparison stats (if both available) */}
      {prediction && dreamTeam && (
        <Card>
          <CardHeader>
            <CardTitle>Comparison</CardTitle>
            <CardDescription>
              How the prediction compared to the actual Dream Team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-fpl-green">
                  {calculateOverlap(predictionPlayers, dreamTeamPlayers)}/11
                </div>
                <div className="text-sm text-muted-foreground">Players Matched</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-fpl-cyan">
                  {prediction.total_predicted_points}
                </div>
                <div className="text-sm text-muted-foreground">Predicted Points</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-fpl-purple-light">
                  {dreamTeam.total_points}
                </div>
                <div className="text-sm text-muted-foreground">Actual Points</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function calculateOverlap(
  predicted: Array<{ player_id: number }>,
  actual: Array<{ player_id: number }>
): number {
  const predictedIds = new Set(predicted.map((p) => p.player_id));
  return actual.filter((p) => predictedIds.has(p.player_id)).length;
}
