"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getBacktestSummary, runBacktest } from "@/lib/api";
import type { BacktestSummary, BacktestResult } from "@/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export default function BacktestPage() {
  const [summary, setSummary] = useState<BacktestSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSummary();
  }, []);

  async function loadSummary() {
    try {
      const data = await getBacktestSummary();
      setSummary(data);
    } catch (e) {
      setError("Failed to load backtest results. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  async function handleRunBacktest() {
    setRunning(true);
    setError(null);

    try {
      const data = await runBacktest(6); // Start from GW 6
      setSummary(data);
    } catch (e) {
      setError("Failed to run backtest. Make sure data is synced first.");
    } finally {
      setRunning(false);
    }
  }

  const chartData = summary?.results.map((r) => ({
    gw: `GW${r.gameweek_fpl_id}`,
    overlap: r.player_overlap,
    pointsRatio: Math.round(r.points_ratio * 100),
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Backtest Results</h1>
          <p className="text-muted-foreground">
            Historical accuracy of predictions vs actual Dream Teams
          </p>
        </div>

        <Button
          variant="fpl"
          onClick={handleRunBacktest}
          disabled={running}
        >
          {running ? "Running..." : "Run Backtest"}
        </Button>
      </div>

      {/* Error message */}
      {error && (
        <Card className="bg-destructive/10 border-destructive">
          <CardContent className="py-4">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Loading backtest results...</p>
          </CardContent>
        </Card>
      ) : summary && summary.total_gameweeks > 0 ? (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-fpl-green">
                  {summary.avg_overlap.toFixed(1)}/11
                </div>
                <p className="text-sm text-muted-foreground">Avg Overlap</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-fpl-cyan">
                  {(summary.avg_points_ratio * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-muted-foreground">Avg Points Ratio</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-fpl-purple-light">
                  {summary.weeks_above_9}/{summary.total_gameweeks}
                </div>
                <p className="text-sm text-muted-foreground">Weeks with 9+ Overlap</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-white">
                  {summary.total_gameweeks}
                </div>
                <p className="text-sm text-muted-foreground">Total Gameweeks</p>
              </CardContent>
            </Card>
          </div>

          {/* Overlap chart */}
          <Card>
            <CardHeader>
              <CardTitle>Player Overlap by Gameweek</CardTitle>
              <CardDescription>
                Number of correctly predicted players (out of 11)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="gw" stroke="#888" fontSize={12} />
                    <YAxis domain={[0, 11]} stroke="#888" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#37003c",
                        border: "1px solid #963cff",
                        borderRadius: "8px",
                      }}
                    />
                    <ReferenceLine
                      y={9}
                      stroke="#00ff87"
                      strokeDasharray="5 5"
                      label={{ value: "Target (9)", fill: "#00ff87", fontSize: 12 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="overlap"
                      stroke="#05f0ff"
                      strokeWidth={2}
                      dot={{ fill: "#05f0ff", r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Points ratio chart */}
          <Card>
            <CardHeader>
              <CardTitle>Points Ratio by Gameweek</CardTitle>
              <CardDescription>
                Predicted points as percentage of actual Dream Team points
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="gw" stroke="#888" fontSize={12} />
                    <YAxis domain={[0, 120]} stroke="#888" fontSize={12} unit="%" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#37003c",
                        border: "1px solid #963cff",
                        borderRadius: "8px",
                      }}
                      formatter={(value: number) => [`${value}%`, "Points Ratio"]}
                    />
                    <ReferenceLine
                      y={85}
                      stroke="#00ff87"
                      strokeDasharray="5 5"
                      label={{ value: "Target (85%)", fill: "#00ff87", fontSize: 12 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="pointsRatio"
                      stroke="#963cff"
                      strokeWidth={2}
                      dot={{ fill: "#963cff", r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Results table */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-4">GW</th>
                      <th className="text-center py-2 px-4">Overlap</th>
                      <th className="text-center py-2 px-4">Points Ratio</th>
                      <th className="text-center py-2 px-4">Predicted</th>
                      <th className="text-center py-2 px-4">Actual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.results.map((r) => (
                      <tr
                        key={r.gameweek_fpl_id}
                        className="border-b border-border/50 hover:bg-muted/50"
                      >
                        <td className="py-2 px-4 font-medium">
                          GW {r.gameweek_fpl_id}
                        </td>
                        <td className="py-2 px-4 text-center">
                          <span
                            className={`font-bold ${
                              r.player_overlap >= 9
                                ? "text-fpl-green"
                                : r.player_overlap >= 7
                                ? "text-fpl-cyan"
                                : "text-fpl-pink"
                            }`}
                          >
                            {r.player_overlap}/11
                          </span>
                        </td>
                        <td className="py-2 px-4 text-center">
                          <span
                            className={`font-bold ${
                              r.points_ratio >= 0.85
                                ? "text-fpl-green"
                                : r.points_ratio >= 0.7
                                ? "text-fpl-cyan"
                                : "text-fpl-pink"
                            }`}
                          >
                            {(r.points_ratio * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2 px-4 text-center">
                          {r.predicted_total}
                        </td>
                        <td className="py-2 px-4 text-center">
                          {r.actual_total}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              No backtest results yet. Click "Run Backtest" to evaluate prediction accuracy.
            </p>
            <p className="text-sm text-muted-foreground">
              Make sure you have synced FPL data first.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
