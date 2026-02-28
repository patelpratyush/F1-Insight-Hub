import React from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Line,
    LineChart,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

interface SectorData {
  sector_1?: number;
  sector_2?: number;
  sector_3?: number;
}

interface SectorBoundaries {
  sector_1_end: number;
  sector_2_end: number;
  sector_3_end: number;
}

interface DriverSectorData {
  driver: string;
  team: string;
  lapTime: number;
  sectorTimes: SectorData;
  sectorBoundaries: SectorBoundaries;
  color: string;
}

interface SectorAnalysisProps {
  driver1: DriverSectorData;
  driver2: DriverSectorData;
}

const SectorAnalysis: React.FC<SectorAnalysisProps> = ({
  driver1,
  driver2,
}) => {
  const formatTime = (seconds: number | undefined) => {
    if (!seconds) return "N/A";
    return seconds.toFixed(3) + "s";
  };

  const formatDelta = (delta: number) => {
    const sign = delta > 0 ? "+" : "";
    return `${sign}${delta.toFixed(3)}s`;
  };

  // Calculate sector deltas (Driver2 - Driver1, so positive means Driver2 is slower)
  const sectorDeltas = {
    sector_1:
      (driver2.sectorTimes.sector_1 || 0) - (driver1.sectorTimes.sector_1 || 0),
    sector_2:
      (driver2.sectorTimes.sector_2 || 0) - (driver1.sectorTimes.sector_2 || 0),
    sector_3:
      (driver2.sectorTimes.sector_3 || 0) - (driver1.sectorTimes.sector_3 || 0),
  };

  // Create data for sector time comparison chart
  const sectorComparisonData = [
    {
      sector: "S1",
      [driver1.driver]: driver1.sectorTimes.sector_1 || 0,
      [driver2.driver]: driver2.sectorTimes.sector_1 || 0,
      delta: sectorDeltas.sector_1,
    },
    {
      sector: "S2",
      [driver1.driver]: driver1.sectorTimes.sector_2 || 0,
      [driver2.driver]: driver2.sectorTimes.sector_2 || 0,
      delta: sectorDeltas.sector_2,
    },
    {
      sector: "S3",
      [driver1.driver]: driver1.sectorTimes.sector_3 || 0,
      [driver2.driver]: driver2.sectorTimes.sector_3 || 0,
      delta: sectorDeltas.sector_3,
    },
  ];

  // Create data for delta visualization
  const deltaData = [
    {
      sector: "S1",
      delta: sectorDeltas.sector_1,
      winner: sectorDeltas.sector_1 < 0 ? driver1.driver : driver2.driver,
    },
    {
      sector: "S2",
      delta: sectorDeltas.sector_2,
      winner: sectorDeltas.sector_2 < 0 ? driver1.driver : driver2.driver,
    },
    {
      sector: "S3",
      delta: sectorDeltas.sector_3,
      winner: sectorDeltas.sector_3 < 0 ? driver1.driver : driver2.driver,
    },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#111111] border border-white/10 rounded-[16px] p-4 shadow-2xl">
          <p className="text-white font-medium">{`Sector ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.dataKey}: ${formatTime(entry.value)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const DeltaTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#111111] border border-white/10 rounded-[16px] p-4 shadow-2xl">
          <p className="text-white font-medium">{`Sector ${label}`}</p>
          <p className="text-yellow-400">{`Delta: ${formatDelta(data.delta)}`}</p>
          <p className="text-green-400">{`Faster: ${data.winner}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Sector Times Header */}
      <div className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 rounded-[40px] shadow-2xl">
        <h3 className="text-xl font-bold text-white mb-4">
          Sector-by-Sector Breakdown
        </h3>

        {/* Sector Times Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="text-left text-gray-300 py-2">Driver</th>
                <th className="text-center text-gray-300 py-2">S1</th>
                <th className="text-center text-gray-300 py-2">S2</th>
                <th className="text-center text-gray-300 py-2">S3</th>
                <th className="text-center text-gray-300 py-2">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-700">
                <td className="py-2">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: driver1.color }}
                    />
                    <span className="text-white font-medium">
                      {driver1.driver}
                    </span>
                  </div>
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver1.sectorTimes.sector_1)}
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver1.sectorTimes.sector_2)}
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver1.sectorTimes.sector_3)}
                </td>
                <td className="text-center text-green-400 font-bold py-2">
                  {formatTime(driver1.lapTime)}
                </td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-2">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: driver2.color }}
                    />
                    <span className="text-white font-medium">
                      {driver2.driver}
                    </span>
                  </div>
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver2.sectorTimes.sector_1)}
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver2.sectorTimes.sector_2)}
                </td>
                <td className="text-center text-white py-2">
                  {formatTime(driver2.sectorTimes.sector_3)}
                </td>
                <td className="text-center text-green-400 font-bold py-2">
                  {formatTime(driver2.lapTime)}
                </td>
              </tr>
              <tr>
                <td className="py-2 text-gray-400 font-medium">Delta</td>
                <td
                  className={`text-center py-2 font-bold ${Math.abs(sectorDeltas.sector_1) < 0.001 ? "text-gray-400" : sectorDeltas.sector_1 < 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {formatDelta(sectorDeltas.sector_1)}
                </td>
                <td
                  className={`text-center py-2 font-bold ${Math.abs(sectorDeltas.sector_2) < 0.001 ? "text-gray-400" : sectorDeltas.sector_2 < 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {formatDelta(sectorDeltas.sector_2)}
                </td>
                <td
                  className={`text-center py-2 font-bold ${Math.abs(sectorDeltas.sector_3) < 0.001 ? "text-gray-400" : sectorDeltas.sector_3 < 0 ? "text-green-400" : "text-red-400"}`}
                >
                  {formatDelta(sectorDeltas.sector_3)}
                </td>
                <td
                  className={`text-center py-2 font-bold ${driver1.lapTime < driver2.lapTime ? "text-green-400" : "text-red-400"}`}
                >
                  {formatDelta(driver2.lapTime - driver1.lapTime)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Sector Time Comparison Chart */}
      <div className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 rounded-[40px] shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-4">
          Sector Time Comparison
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sectorComparisonData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="sector"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                tickFormatter={(value) => `${value.toFixed(1)}s`}
                label={{
                  value: "Time (s)",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle", fill: "#9CA3AF" },
                }}
              />

              <Bar
                dataKey={driver1.driver}
                fill={driver1.color}
                name={driver1.driver}
                opacity={0.8}
              />

              <Bar
                dataKey={driver2.driver}
                fill={driver2.color}
                name={driver2.driver}
                opacity={0.8}
              />

              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                height={36}
                iconType="rect"
                wrapperStyle={{
                  paddingBottom: "20px",
                  fontSize: "12px",
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Time Gain/Loss Chart */}
      <div className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 rounded-[40px] shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-4">
          Time Gain/Loss by Sector
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={deltaData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="sector"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
                tickFormatter={(value) =>
                  `${value > 0 ? "+" : ""}${value.toFixed(3)}s`
                }
                label={{
                  value: "Time Delta (s)",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle", fill: "#9CA3AF" },
                }}
              />

              {/* Zero reference line */}
              <ReferenceLine y={0} stroke="#9CA3AF" strokeDasharray="2 2" />

              <Bar dataKey="delta" name="Time Delta">
                {deltaData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.delta < 0 ? driver1.color : driver2.color}
                    opacity={0.8}
                  />
                ))}
              </Bar>

              <Tooltip content={<DeltaTooltip />} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-sm text-gray-400">
          Positive values indicate {driver2.driver} is slower, negative values
          indicate {driver1.driver} is slower.
        </div>
      </div>

      {/* Sector Analysis Summary */}
      <div className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-6 rounded-[40px] shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-4">
          Sector Analysis Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {["sector_1", "sector_2", "sector_3"].map((sector, index) => {
            const sectorNum = index + 1;
            const delta = sectorDeltas[sector as keyof typeof sectorDeltas];
            const winner = delta < 0 ? driver1 : driver2;
            const advantage = Math.abs(delta);

            return (
              <div key={sector} className="p-4 bg-white/5 rounded-[24px]">
                <div className="text-center">
                  <div className="text-lg font-bold text-white mb-2">
                    Sector {sectorNum}
                  </div>
                  <div
                    className="text-sm font-medium mb-1"
                    style={{ color: winner.color }}
                  >
                    {winner.driver} faster
                  </div>
                  <div className="text-xl font-bold text-yellow-400">
                    {advantage < 0.001 ? "TIED" : `${advantage.toFixed(3)}s`}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">Advantage</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SectorAnalysis;
