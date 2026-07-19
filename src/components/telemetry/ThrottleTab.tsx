import { Activity, Zap } from "lucide-react";
import {
    Area,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface ThrottleTabProps {
  speedTraceData: any;
  selectedDriver: string;
  selectedLap: number;
}

const ThrottleTab = ({ speedTraceData, selectedDriver, selectedLap }: ThrottleTabProps) => {
  if (!speedTraceData || speedTraceData.error) {
    return (
      <div className="h-80 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
        <div className="text-center">
          <Zap className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <div className="text-gray-400">
            Throttle Analysis
          </div>
          <div className="text-sm text-gray-500">
            Click "Speed Trace" to load throttle and brake
            data
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Throttle Tab Header */}
      <div className="bg-[#111] border border-white/5 rounded-[32px] p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">
            Throttle & Brake Analysis - {selectedDriver}
          </h3>
          <div className="bg-white/10 px-4 py-1.5 rounded-full">
            <span className="text-yellow-400 font-medium text-sm">
              Lap {selectedLap} Data
            </span>
          </div>
        </div>
      </div>

      {/* Throttle vs Brake Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <Zap className="h-5 w-5 text-green-500 mr-2" />
            Throttle Application
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-400">
                Max Throttle:
              </span>
              <span className="text-green-400 font-bold">
                100%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">
                Avg Throttle:
              </span>
              <span className="text-green-400 font-bold">
                {speedTraceData.analysis.full_throttle_pct?.toFixed(
                  1,
                )}
                %
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">
                Full Throttle Time:
              </span>
              <span className="text-green-400 font-bold">
                {speedTraceData.analysis.full_throttle_pct?.toFixed(
                  1,
                )}
                %
              </span>
            </div>
          </div>
        </div>

        <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <Activity className="h-5 w-5 text-red-500 mr-2" />
            Braking Analysis
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-400">
                Brake Zones:
              </span>
              <span className="text-red-400 font-bold">
                {speedTraceData.analysis.braking_zones}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">
                Data Type:
              </span>
              <span className="text-gray-400">
                On/Off Signal
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Note: FastF1 brake data for this session is
              boolean (on/off) rather than pressure
              percentage.
            </div>
          </div>
        </div>
      </div>

      {/* Input Comparison Chart */}
      <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
        <h3 className="text-lg font-bold text-white mb-4">
          Throttle Application vs Speed
        </h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={speedTraceData.telemetry.distance.map(
                (distance, index) => ({
                  distance: Math.round(distance),
                  speed:
                    speedTraceData.telemetry.speed[index] ||
                    0,
                  throttle:
                    speedTraceData.telemetry.throttle[
                      index
                    ] || 0,
                }),
              )}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#374151"
              />
              <XAxis
                dataKey="distance"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                label={{
                  value: "Distance (m)",
                  position: "insideBottom",
                  offset: -5,
                  style: {
                    textAnchor: "middle",
                    fill: "#9CA3AF",
                  },
                }}
              />
              <YAxis
                yAxisId="speed"
                domain={[0, "dataMax"]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                label={{
                  value: "Speed (km/h)",
                  angle: -90,
                  position: "insideLeft",
                  style: {
                    textAnchor: "middle",
                    fill: "#9CA3AF",
                  },
                }}
              />
              <YAxis
                yAxisId="throttle"
                orientation="right"
                domain={[0, 100]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                label={{
                  value: "Throttle (%)",
                  angle: 90,
                  position: "insideRight",
                  style: {
                    textAnchor: "middle",
                    fill: "#9CA3AF",
                  },
                }}
              />

              {/* Speed line */}
              <Line
                yAxisId="speed"
                type="monotone"
                dataKey="speed"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                name="Speed"
              />

              {/* Throttle area */}
              <Area
                yAxisId="throttle"
                type="monotone"
                dataKey="throttle"
                stroke="#10B981"
                fill="#10B981"
                fillOpacity={0.3}
                strokeWidth={2}
                name="Throttle"
              />

              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                        <p className="text-white font-medium">{`Distance: ${label}m`}</p>
                        <p className="text-blue-400">{`Speed: ${payload.find((p) => p.dataKey === "speed")?.value?.toFixed(1)} km/h`}</p>
                        <p className="text-green-400">{`Throttle: ${payload.find((p) => p.dataKey === "throttle")?.value?.toFixed(0)}%`}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                verticalAlign="top"
                height={36}
                iconType="line"
                wrapperStyle={{
                  paddingBottom: "20px",
                  fontSize: "12px",
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Throttle vs Speed Correlation */}
      <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
        <h3 className="text-lg font-bold text-white mb-4">
          Throttle vs Speed Correlation
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={(() => {
                // Group data by throttle percentage and average the speeds
                const grouped = {};
                speedTraceData.telemetry.throttle.forEach(
                  (throttle, index) => {
                    const throttleVal = Math.round(
                      throttle || 0,
                    );
                    const speed =
                      speedTraceData.telemetry.speed[
                        index
                      ] || 0;
                    if (throttleVal > 0) {
                      if (!grouped[throttleVal]) {
                        grouped[throttleVal] = [];
                      }
                      grouped[throttleVal].push(speed);
                    }
                  },
                );

                // Calculate average speed for each throttle percentage
                return Object.keys(grouped)
                  .map((throttle) => ({
                    throttle: parseInt(throttle),
                    speed:
                      grouped[throttle].reduce(
                        (sum, speed) => sum + speed,
                        0,
                      ) / grouped[throttle].length,
                  }))
                  .sort((a, b) => a.throttle - b.throttle);
              })()}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#374151"
              />
              <XAxis
                dataKey="throttle"
                type="number"
                domain={[0, 100]}
                ticks={[0, 20, 40, 60, 80, 100]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                label={{
                  value: "Throttle (%)",
                  position: "insideBottom",
                  offset: -5,
                  style: {
                    textAnchor: "middle",
                    fill: "#9CA3AF",
                  },
                }}
              />
              <YAxis
                dataKey="speed"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                label={{
                  value: "Speed (km/h)",
                  angle: -90,
                  position: "insideLeft",
                  style: {
                    textAnchor: "middle",
                    fill: "#9CA3AF",
                  },
                }}
              />

              <Line
                type="monotone"
                dataKey="speed"
                stroke="#8B5CF6"
                strokeWidth={2}
                dot={{
                  fill: "#8B5CF6",
                  strokeWidth: 0,
                  r: 1,
                }}
                name="Speed Response"
              />

              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                        <p className="text-white font-medium">{`Throttle: ${label}%`}</p>
                        <p className="text-purple-400">{`Speed: ${payload[0]?.value?.toFixed(1)} km/h`}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                verticalAlign="top"
                height={36}
                iconType="line"
                wrapperStyle={{
                  paddingBottom: "20px",
                  fontSize: "12px",
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-sm text-gray-400">
          This chart shows how speed responds to throttle
          input. Higher correlation indicates more
          predictable acceleration.
        </div>
      </div>
    </div>
  );
};

export default ThrottleTab;
