import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
    AlertTriangle,
    Crown,
    Minus,
    TrendingDown,
    TrendingUp,
} from "lucide-react";
import React from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface DriverStanding {
  position: number;
  driver: string;
  points: number;
  team: string;
}

interface ChampionshipPressureProps {
  standings: DriverStanding[];
  remainingRaces: number;
  currentRound: number;
  totalRounds: number;
}

interface PressureData {
  driver: string;
  team: string;
  points: number;
  position: number;
  gapToLeader: number;
  pressureScore: number;
  pressureLevel: "Low" | "Medium" | "High" | "Critical";
  mathematicallyPossible: boolean;
  championshipOdds: number;
  pointsPerRaceNeeded: number;
}

const ChampionshipPressureChart: React.FC<ChampionshipPressureProps> = ({
  standings,
  remainingRaces,
  currentRound,
  totalRounds,
}) => {
  // Championship pressure calculation formula
  const calculateChampionshipPressure = (
    standings: DriverStanding[],
  ): PressureData[] => {
    const maxPointsPerRace = 26; // 25 for win + 1 for fastest lap
    const safeRemainingRaces = Math.max(1, remainingRaces || 1); // Prevent division by zero
    const maxRemainingPoints = safeRemainingRaces * maxPointsPerRace;
    const leaderPoints = standings[0]?.points || 0;

    return standings.map((driver, index) => {
      const gapToLeader = leaderPoints - driver.points;
      const pointsPerRaceNeeded =
        gapToLeader > 0 ? gapToLeader / safeRemainingRaces : 0;

      // Mathematical possibility check
      const mathematicallyPossible =
        driver.points + maxRemainingPoints > leaderPoints ||
        driver.position === 1;

      // Pressure score calculation (0-100)
      let pressureScore = 0;

      if (driver.position === 1) {
        // Leader pressure: based on gap to 2nd place and remaining races
        const gapToSecond = standings[1]
          ? driver.points - standings[1].points
          : 50;
        const defenseScore = Math.max(
          0,
          100 - (gapToSecond / maxRemainingPoints) * 100,
        );
        const raceProgress =
          ((currentRound || 0) / Math.max(1, totalRounds || 24)) * 100;
        pressureScore = defenseScore * 0.6 + raceProgress * 0.4;
      } else {
        // Challenger pressure: based on gap to leader and mathematical possibility
        if (!mathematicallyPossible) {
          pressureScore = Math.max(0, 20 - index * 2); // Minimal pressure for impossible positions
        } else {
          const gapRatio = gapToLeader / maxRemainingPoints;
          const positionPenalty = Math.min(index * 5, 30);
          const urgencyMultiplier = Math.min(safeRemainingRaces / 10, 1);

          pressureScore =
            Math.max(0, 100 - gapRatio * 100 - positionPenalty) *
            urgencyMultiplier;
        }
      }

      // Championship odds calculation
      let championshipOdds = 0;
      if (mathematicallyPossible) {
        if (driver.position === 1) {
          championshipOdds = Math.min(
            95,
            50 + (driver.points - (standings[1]?.points || 0)) / 10,
          );
        } else {
          const baseOdds = Math.max(1, 50 - gapToLeader / 10);
          const positionPenalty = Math.min(index * 8, 40);
          championshipOdds = Math.max(1, baseOdds - positionPenalty);
        }
      }

      // Pressure level categorization
      let pressureLevel: "Low" | "Medium" | "High" | "Critical";
      if (pressureScore >= 80) pressureLevel = "Critical";
      else if (pressureScore >= 60) pressureLevel = "High";
      else if (pressureScore >= 40) pressureLevel = "Medium";
      else pressureLevel = "Low";

      return {
        driver: driver.driver,
        team: driver.team,
        points: driver.points || 0,
        position: driver.position || index + 1,
        gapToLeader: isFinite(gapToLeader) ? gapToLeader : 0,
        pressureScore: isFinite(pressureScore) ? Math.round(pressureScore) : 0,
        pressureLevel,
        mathematicallyPossible,
        championshipOdds: isFinite(championshipOdds)
          ? Math.round(championshipOdds)
          : 0,
        pointsPerRaceNeeded: isFinite(pointsPerRaceNeeded)
          ? Math.round(pointsPerRaceNeeded * 10) / 10
          : 0,
      };
    });
  };

  const pressureData = calculateChampionshipPressure(standings);
  const mathematicalContenders = pressureData.filter(
    (d) => d.mathematicallyPossible,
  );

  // Color schemes for pressure levels
  const getPressureColor = (level: string, position: number) => {
    if (position === 1) return "#FFD700"; // Gold for leader

    switch (level) {
      case "Critical":
        return "#EF4444"; // Red
      case "High":
        return "#F97316"; // Orange
      case "Medium":
        return "#EAB308"; // Yellow
      case "Low":
        return "#22C55E"; // Green
      default:
        return "#6B7280"; // Gray
    }
  };

  const getPressureIcon = (level: string, position: number) => {
    if (position === 1) return <Crown className="h-4 w-4" />;

    switch (level) {
      case "Critical":
        return <AlertTriangle className="h-4 w-4" />;
      case "High":
        return <TrendingUp className="h-4 w-4" />;
      case "Medium":
        return <Minus className="h-4 w-4" />;
      case "Low":
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  // Chart data preparation
  const chartData = pressureData.slice(0, 6).map((d) => ({
    name: d.driver,
    pressure: d.pressureScore,
    points: d.points,
    position: d.position,
    level: d.pressureLevel,
  }));

  const oddsData = mathematicalContenders.slice(0, 8).map((d) => ({
    name: d.driver,
    value: d.championshipOdds,
    position: d.position,
  }));

  return (
    <div className="space-y-6">
      {/* Championship Status Overview */}
      <Card className="bg-transparent bg-gradient-to-br from-white/[0.02] to-transparent shadow-none border-t border-l border-white/5 rounded-[40px] overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white flex items-center space-x-2">
            <Crown className="h-5 w-5 text-yellow-500" />
            <span>Championship Pressure Analysis</span>
          </CardTitle>
          <CardDescription className="text-gray-400">
            Real-time championship pressure based on current standings and
            remaining races
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-lg border border-blue-600/20">
              <div className="text-2xl font-bold text-blue-400">
                {Math.max(0, remainingRaces || 0)}
              </div>
              <div className="text-sm text-gray-300">Races Remaining</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-lg border border-green-600/20">
              <div className="text-2xl font-bold text-green-400">
                {mathematicalContenders.length}
              </div>
              <div className="text-sm text-gray-300">In Championship Hunt</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-lg border border-purple-600/20">
              <div className="text-2xl font-bold text-purple-400">
                {Math.max(0, (remainingRaces || 0) * 26)}
              </div>
              <div className="text-sm text-gray-300">Max Points Available</div>
            </div>
            <div className="text-center p-4 bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 rounded-lg border border-yellow-600/20">
              <div className="text-2xl font-bold text-yellow-400">
                {Math.round(
                  ((currentRound || 0) / Math.max(1, totalRounds || 24)) * 100,
                )}
                %
              </div>
              <div className="text-sm text-gray-300">Season Complete</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pressure Bar Chart */}
      <Card className="bg-transparent bg-gradient-to-br from-white/[0.02] to-transparent shadow-none border-t border-l border-white/5 rounded-[40px] overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white">
            Championship Pressure Levels
          </CardTitle>
          <CardDescription className="text-gray-400">
            Pressure intensity from 0-100 based on position, points gap, and
            remaining races
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="name"
                  stroke="#9CA3AF"
                  fontSize={12}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-[#111111] border border-white/10 rounded-[16px] p-4 shadow-2xl">
                          <p className="text-white font-medium">{label}</p>
                          <p className="text-blue-400">
                            Position: P{data.position}
                          </p>
                          <p className="text-green-400">
                            Points: {data.points}
                          </p>
                          <p className="text-purple-400">
                            Pressure: {data.pressure}/100
                          </p>
                          <p className="text-yellow-400">Level: {data.level}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="pressure" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={getPressureColor(entry.level, entry.position)}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Driver Analysis */}
      <Card className="bg-transparent bg-gradient-to-br from-white/[0.02] to-transparent shadow-none border-t border-l border-white/5 rounded-[40px] overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white">
            Driver-by-Driver Analysis
          </CardTitle>
          <CardDescription className="text-gray-400">
            Detailed championship pressure breakdown for each driver
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {pressureData.slice(0, 6).map((driver, index) => (
              <div
                key={driver.driver}
                className="p-4 bg-white/5 rounded-[24px]"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                        driver.position === 1
                          ? "bg-yellow-500"
                          : driver.position === 2
                            ? "bg-gray-400"
                            : driver.position === 3
                              ? "bg-amber-600"
                              : "bg-gray-600"
                      }`}
                    >
                      {driver.position}
                    </div>
                    <div>
                      <div className="font-semibold text-white">
                        {driver.driver}
                      </div>
                      <div className="text-sm text-gray-400">{driver.team}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge
                      variant="outline"
                      className={`${
                        driver.pressureLevel === "Critical"
                          ? "text-red-400 border-red-400"
                          : driver.pressureLevel === "High"
                            ? "text-orange-400 border-orange-400"
                            : driver.pressureLevel === "Medium"
                              ? "text-yellow-400 border-yellow-400"
                              : "text-green-400 border-green-400"
                      }`}
                    >
                      <span className="mr-1">
                        {getPressureIcon(driver.pressureLevel, driver.position)}
                      </span>
                      {driver.pressureLevel}
                    </Badge>
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">
                        {driver.points} pts
                      </div>
                      {driver.gapToLeader > 0 && (
                        <div className="text-sm text-red-400">
                          -{driver.gapToLeader}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Pressure Score:</span>
                    <div className="flex items-center space-x-2 mt-1">
                      <Progress
                        value={driver.pressureScore}
                        className="flex-1 h-2"
                      />
                      <span className="text-white font-medium w-12">
                        {driver.pressureScore}/100
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Championship Odds:</span>
                    <div className="text-white font-medium mt-1">
                      {driver.championshipOdds}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Points/Race Needed:</span>
                    <div className="text-white font-medium mt-1">
                      {driver.pointsPerRaceNeeded > 0 &&
                      isFinite(driver.pointsPerRaceNeeded)
                        ? driver.pointsPerRaceNeeded
                        : "0"}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-400">Mathematical Chance:</span>
                    <div
                      className={`font-medium mt-1 ${driver.mathematicallyPossible ? "text-green-400" : "text-red-400"}`}
                    >
                      {driver.mathematicallyPossible ? "Yes" : "No"}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Championship Odds Pie Chart */}
      <Card className="bg-transparent bg-gradient-to-br from-white/[0.02] to-transparent shadow-none border-t border-l border-white/5 rounded-[40px] overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white">
            Championship Odds Distribution
          </CardTitle>
          <CardDescription className="text-gray-400">
            Percentage likelihood of winning the championship
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={oddsData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                  labelLine={false}
                >
                  {oddsData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={getPressureColor("Medium", entry.position)}
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-[#111111] border border-white/10 rounded-[16px] p-4 shadow-2xl">
                          <p className="text-white font-medium">{data.name}</p>
                          <p className="text-green-400">
                            Championship Odds: {data.value}%
                          </p>
                          <p className="text-blue-400">
                            Current Position: P{data.position}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChampionshipPressureChart;
