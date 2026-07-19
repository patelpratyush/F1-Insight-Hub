import LapSelector from "@/components/LapSelector";
import { Activity, Gauge, Users, Zap } from "lucide-react";
import {
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface OverviewTabProps {
  telemetryData: any;
  selectedDriver: string;
  selectedSession: string;
  availableLaps: number[];
  selectedLap: number;
  setSelectedLap: (lap: number) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  playbackSpeed: number;
  setPlaybackSpeed: (speed: number) => void;
  getLapSpecificData: () => any;
  formatLapTime: (seconds: number) => string;
}

const OverviewTab = ({
  telemetryData,
  selectedDriver,
  selectedSession,
  availableLaps,
  selectedLap,
  setSelectedLap,
  isPlaying,
  setIsPlaying,
  playbackSpeed,
  setPlaybackSpeed,
  getLapSpecificData,
  formatLapTime,
}: OverviewTabProps) => {
  if (!telemetryData) return null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-6 bg-white/5 rounded-[24px]">
          <Activity className="h-6 w-6 text-blue-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-blue-400">
            {telemetryData.session_info?.event_name}
          </div>
          <div className="text-sm text-gray-300">Event</div>
        </div>

        <div className="text-center p-6 bg-white/5 rounded-[24px]">
          <Gauge className="h-6 w-6 text-green-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-green-400">
            {telemetryData.session_info?.track_name}
          </div>
          <div className="text-sm text-gray-300">Track</div>
        </div>

        <div className="text-center p-6 bg-white/5 rounded-[24px]">
          <Zap className="h-6 w-6 text-purple-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-purple-400">
            {telemetryData.session_info?.weather?.air_temp?.toFixed(
              1,
            ) || "N/A"}
            °C
          </div>
          <div className="text-sm text-gray-300">
            Air Temp
          </div>
        </div>

        <div className="text-center p-6 bg-white/5 rounded-[24px]">
          <Users className="h-6 w-6 text-red-400 mx-auto mb-2" />
          <div className="text-lg font-bold text-red-400">
            {
              Object.keys(
                telemetryData.performance_metrics || {},
              ).length
            }
          </div>
          <div className="text-sm text-gray-300">
            Drivers Analyzed
          </div>
        </div>
      </div>

      {/* Lap Selector with Playback */}
      {selectedDriver && availableLaps.length > 0 && (
        <LapSelector
          availableLaps={availableLaps}
          selectedLap={selectedLap}
          onLapChange={setSelectedLap}
          isPlaying={isPlaying}
          onPlayStateChange={setIsPlaying}
          playbackSpeed={playbackSpeed}
          onSpeedChange={setPlaybackSpeed}
        />
      )}

      {/* Lap-Specific Information */}
      {selectedDriver &&
        availableLaps.length > 0 &&
        (() => {
          const lapData = getLapSpecificData();
          return lapData ? (
            <div className="bg-[#111] border border-white/5 rounded-[32px] p-6">
              <h3 className="text-lg font-bold text-white mb-4">
                Lap {selectedLap} Details - {selectedDriver}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">
                    {(() => {
                      const minutes = Math.floor(
                        lapData.lap_time / 60,
                      );
                      const seconds = (
                        lapData.lap_time % 60
                      ).toFixed(3);
                      return `${minutes}:${seconds.padStart(6, "0")}`;
                    })()}
                  </div>
                  <div className="text-sm text-gray-300">
                    Lap Time
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {lapData.position || "N/A"}
                  </div>
                  <div className="text-sm text-gray-300">
                    Position
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">
                    {lapData.compound || "Unknown"}
                  </div>
                  <div className="text-sm text-gray-300">
                    Tire Compound
                  </div>
                </div>

                <div className="text-center">
                  <div
                    className={`text-2xl font-bold ${
                      lapData.lap_number ===
                      telemetryData.performance_metrics[
                        selectedDriver
                      ].lap_times?.fastest_lap_number
                        ? "text-purple-400"
                        : "text-gray-400"
                    }`}
                  >
                    {lapData.lap_number ===
                    telemetryData.performance_metrics[
                      selectedDriver
                    ].lap_times?.fastest_lap_number
                      ? "🏆 FASTEST"
                      : "REGULAR"}
                  </div>
                  <div className="text-sm text-gray-300">
                    Lap Type
                  </div>
                </div>
              </div>
            </div>
          ) : null;
        })()}

      {/* Performance metrics display */}
      {selectedDriver &&
        telemetryData.performance_metrics?.[
          selectedDriver
        ] && (
          <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] relative group">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">
                {selectedDriver} Performance Metrics
              </h3>
              {availableLaps.length > 0 && (
                <div className="bg-white/10 px-4 py-1.5 rounded-full">
                  <span className="text-blue-400 font-medium text-sm">
                    Viewing: Lap {selectedLap}
                  </span>
                </div>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].speed_stats?.max_speed?.toFixed(1) ||
                    "N/A"}
                </div>
                <div className="text-sm text-gray-300">
                  Max Speed (km/h)
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].lap_times?.fastest_lap?.toFixed(3) ||
                    "N/A"}
                </div>
                <div className="text-sm text-gray-300">
                  Fastest Lap (s)
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].throttle_stats?.avg_throttle?.toFixed(
                    1,
                  ) || "N/A"}
                  %
                </div>
                <div className="text-sm text-gray-300">
                  Avg Throttle
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].brake_stats?.brake_zones?.length || 0}
                </div>
                <div className="text-sm text-gray-300">
                  Brake Zones
                </div>
              </div>
            </div>
          </div>
        )}

      {/* Driver Laptimes Scatterplot */}
      {selectedDriver &&
        telemetryData.performance_metrics?.[
          selectedDriver
        ] && (
          <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] relative group">
            <h3 className="text-xl font-bold text-white mb-4">
              {selectedDriver} Session Lap Times
            </h3>
            <div className="h-96">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <ScatterChart>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#374151"
                  />
                  <XAxis
                    type="number"
                    dataKey="lap_number"
                    domain={["dataMin", "dataMax"]}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                    label={{
                      value: "Lap Number",
                      position: "insideBottom",
                      offset: -5,
                      style: {
                        textAnchor: "middle",
                        fill: "#9CA3AF",
                      },
                    }}
                  />
                  <YAxis
                    type="number"
                    dataKey="lap_time"
                    domain={["dataMin - 1", "dataMax + 1"]}
                    reversed={true}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                    tickFormatter={(value) =>
                      `${Math.floor(value / 60)}:${(value % 60).toFixed(1).padStart(4, "0")}`
                    }
                    label={{
                      value: "Lap Time",
                      angle: -90,
                      position: "insideLeft",
                      style: {
                        textAnchor: "middle",
                        fill: "#9CA3AF",
                      },
                    }}
                  />

                  {/* Compound-based scatter points */}
                  {(() => {
                    const allLaps =
                      telemetryData.performance_metrics[
                        selectedDriver
                      ]?.lap_times?.all_laps || [];
                    const compoundColors = {
                      SOFT: "#EF4444", // Red
                      MEDIUM: "#EAB308", // Yellow
                      HARD: "#E5E7EB", // White/Gray
                      INTERMEDIATE: "#10B981", // Green
                      WET: "#3B82F6", // Blue
                      UNKNOWN: "#9CA3AF", // Gray
                    };

                    const compounds = [
                      ...new Set(
                        allLaps.map((lap) => lap.compound),
                      ),
                    ].filter((c) => c !== "UNKNOWN");

                    return compounds.map((compound) => (
                      <Scatter
                        key={compound}
                        name={
                          compound === "SOFT"
                            ? "🔴 SOFT"
                            : compound === "MEDIUM"
                              ? "🟡 MEDIUM"
                              : compound === "HARD"
                                ? "⚪ HARD"
                                : compound
                        }
                        data={allLaps.filter(
                          (lap) =>
                            lap.compound === compound,
                        )}
                        fill={
                          compoundColors[compound] ||
                          "#9CA3AF"
                        }
                        fillOpacity={0.8}
                      />
                    ));
                  })()}

                  {/* Fastest lap highlight with special styling */}
                  <Scatter
                    name="🏆 Fastest Lap"
                    data={
                      telemetryData.performance_metrics[
                        selectedDriver
                      ]?.lap_times?.all_laps?.filter(
                        (lap) =>
                          lap.lap_number ===
                          telemetryData.performance_metrics[
                            selectedDriver
                          ]?.lap_times?.fastest_lap_number,
                      ) || []
                    }
                    fill="#FF0000"
                    stroke="#FFFFFF"
                    strokeWidth={2}
                    fillOpacity={1}
                  />

                  {/* Currently selected lap highlight */}
                  <Scatter
                    name={`🎯 Selected Lap ${selectedLap}`}
                    data={
                      telemetryData.performance_metrics[
                        selectedDriver
                      ]?.lap_times?.all_laps?.filter(
                        (lap) =>
                          lap.lap_number === selectedLap,
                      ) || []
                    }
                    fill="#3B82F6"
                    stroke="#FFFFFF"
                    strokeWidth={3}
                    fillOpacity={1}
                    shape="star"
                  />

                  <Tooltip
                    content={({ active, payload }) => {
                      if (
                        active &&
                        payload &&
                        payload.length
                      ) {
                        const data = payload[0].payload;
                        const isFastest =
                          data.lap_number ===
                          telemetryData.performance_metrics[
                            selectedDriver
                          ].lap_times?.fastest_lap_number;
                        return (
                          <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                            <p className="text-white font-medium">{`Lap ${data.lap_number}`}</p>
                            <p className="text-green-400">{`Time: ${formatLapTime(data.lap_time)}`}</p>
                            {data.compound &&
                              data.compound !==
                                "Unknown" && (
                                <p className="text-purple-400">{`Tire: ${data.compound}`}</p>
                              )}
                            {data.sector_1 && (
                              <div className="text-sm text-gray-400 mt-1">
                                <p>{`S1: ${formatLapTime(data.sector_1)}`}</p>
                                {data.sector_2 && (
                                  <p>{`S2: ${formatLapTime(data.sector_2)}`}</p>
                                )}
                                {data.sector_3 && (
                                  <p>{`S3: ${formatLapTime(data.sector_3)}`}</p>
                                )}
                              </div>
                            )}
                            {isFastest && (
                              <p className="text-red-400 font-bold">
                                🏆 Fastest Lap
                              </p>
                            )}
                            {!data.is_valid && (
                              <p className="text-yellow-400">
                                ⚠️ Invalid/Outlap
                              </p>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    iconType="circle"
                    wrapperStyle={{
                      paddingBottom: "20px",
                      fontSize: "12px",
                      lineHeight: "14px",
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-green-400 font-bold">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].lap_times?.consistency?.toFixed(3) ||
                    "N/A"}
                  s
                </div>
                <div className="text-gray-400">
                  Consistency (StdDev)
                </div>
              </div>
              <div className="text-center">
                <div className="text-blue-400 font-bold">
                  {formatLapTime(
                    telemetryData.performance_metrics[
                      selectedDriver
                    ].lap_times?.average_lap || 0,
                  )}
                </div>
                <div className="text-gray-400">
                  Average Lap
                </div>
              </div>
              <div className="text-center">
                <div className="text-purple-400 font-bold">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].lap_times?.improvement_rate?.toFixed(
                    3,
                  ) || "N/A"}
                  s/lap
                </div>
                <div className="text-gray-400">
                  Improvement Rate
                </div>
              </div>
              <div className="text-center">
                <div className="text-yellow-400 font-bold">
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].lap_times?.total_laps || 0}
                </div>
                <div className="text-gray-400">
                  Total Laps
                </div>
              </div>
            </div>

            {/* Session Type Specific Insights */}
            <div className="mt-4 text-sm text-gray-400">
              <div className="flex items-center justify-between">
                <span>Session Analysis:</span>
                <span className="text-white">
                  {selectedSession === "Practice 2"
                    ? "Practice 2 - Representative pace & tire testing"
                    : selectedSession === "Practice 3"
                      ? "Practice 3 - Final setup confirmation"
                      : selectedSession ===
                          "Sprint Qualifying"
                        ? "Sprint Qualifying - Short format pole position"
                        : selectedSession === "Qualifying"
                          ? "Qualifying - Peak performance for race grid"
                          : selectedSession === "Sprint"
                            ? "Sprint - Short race with points"
                            : "Race - Full distance competition & strategy"}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span>Fastest Lap:</span>
                <span className="text-red-400 font-medium">
                  Lap{" "}
                  {telemetryData.performance_metrics[
                    selectedDriver
                  ].lap_times?.fastest_lap_number || "N/A"}
                </span>
              </div>
            </div>
          </div>
        )}
    </div>
  );
};

export default OverviewTab;
