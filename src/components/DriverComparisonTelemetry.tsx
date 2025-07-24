import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  ReferenceLine
} from 'recharts';
import SectorAnalysis from './SectorAnalysis';

interface DriverTelemetryData {
  distance: number[];
  time: number[];
  speed: number[];
  throttle: number[];
  brake: number[];
  gear: number[];
  drs?: number[];
  rpm?: number[];
  ers?: {
    deployment: number[];
    harvest: number[];
  };
}

interface DriverData {
  driver: string;
  team: string;
  lapTime: number;
  sectorTimes: {
    sector_1?: number;
    sector_2?: number;
    sector_3?: number;
  };
  sectorBoundaries: {
    sector_1_end: number;
    sector_2_end: number;
    sector_3_end: number;
  };
  telemetry: DriverTelemetryData;
  color: string;
}

interface DriverComparisonProps {
  driver1: DriverData;
  driver2: DriverData;
  viewMode: 'distance' | 'time';
  corners?: Array<{
    number: number;
    letter?: string;
    distance: number;
  }>;
}

const DriverComparisonTelemetry: React.FC<DriverComparisonProps> = ({
  driver1,
  driver2,
  viewMode = 'distance',
  corners = []
}) => {
  // Helper function to safely convert to number
  const safeNumber = (value: any, defaultValue: number = 0): number => {
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? defaultValue : num;
  };

  // Interpolate data to align drivers on the same x-axis points
  const interpolateData = (xValues: number[], yValues: number[], targetX: number[]) => {
    return targetX.map(x => {
      // Find the two closest points
      let leftIndex = 0;
      let rightIndex = xValues.length - 1;
      
      for (let i = 0; i < xValues.length - 1; i++) {
        if (xValues[i] <= x && xValues[i + 1] >= x) {
          leftIndex = i;
          rightIndex = i + 1;
          break;
        }
      }
      
      if (leftIndex === rightIndex) {
        return safeNumber(yValues[leftIndex]);
      }
      
      // Linear interpolation
      const x1 = xValues[leftIndex];
      const x2 = xValues[rightIndex];
      const y1 = yValues[leftIndex];
      const y2 = yValues[rightIndex];
      
      if (x2 === x1) return safeNumber(y1);
      
      const interpolatedY = y1 + (y2 - y1) * (x - x1) / (x2 - x1);
      return safeNumber(interpolatedY);
    });
  };

  // Combine telemetry data for both drivers with delta calculations
  const getChartData = () => {
    const xAxisKey = viewMode === 'distance' ? 'distance' : 'time';
    
    // Create a common x-axis by merging both drivers' x-values
    const allXValues = [
      ...driver1.telemetry[xAxisKey],
      ...driver2.telemetry[xAxisKey]
    ].sort((a, b) => a - b);
    
    // Remove duplicates and create evenly spaced points
    const uniqueXValues = [...new Set(allXValues.map(x => Math.round(x)))];
    const minX = Math.min(...uniqueXValues);
    const maxX = Math.max(...uniqueXValues);
    
    // Create aligned x-axis points (sample every few points to avoid too much data)
    const step = Math.max(1, Math.floor((maxX - minX) / 500)); // Max 500 points
    const alignedXValues = [];
    for (let x = minX; x <= maxX; x += step) {
      alignedXValues.push(x);
    }

    // Interpolate both drivers' data to the aligned x-axis
    const driver1Speed = interpolateData(driver1.telemetry[xAxisKey], driver1.telemetry.speed, alignedXValues);
    const driver2Speed = interpolateData(driver2.telemetry[xAxisKey], driver2.telemetry.speed, alignedXValues);
    const driver1Throttle = interpolateData(driver1.telemetry[xAxisKey], driver1.telemetry.throttle, alignedXValues);
    const driver2Throttle = interpolateData(driver2.telemetry[xAxisKey], driver2.telemetry.throttle, alignedXValues);
    const driver1Brake = interpolateData(driver1.telemetry[xAxisKey], driver1.telemetry.brake, alignedXValues);
    const driver2Brake = interpolateData(driver2.telemetry[xAxisKey], driver2.telemetry.brake, alignedXValues);
    const driver1Gear = interpolateData(driver1.telemetry[xAxisKey], driver1.telemetry.gear, alignedXValues);
    const driver2Gear = interpolateData(driver2.telemetry[xAxisKey], driver2.telemetry.gear, alignedXValues);
    const driver1RPM = driver1.telemetry.rpm ? interpolateData(driver1.telemetry[xAxisKey], driver1.telemetry.rpm, alignedXValues) : [];
    const driver2RPM = driver2.telemetry.rpm ? interpolateData(driver2.telemetry[xAxisKey], driver2.telemetry.rpm, alignedXValues) : [];

    // Create combined data with deltas
    const combinedData = alignedXValues.map((x, i) => {
      const speedDelta = driver1Speed[i] - driver2Speed[i];
      const throttleDelta = driver1Throttle[i] - driver2Throttle[i];
      const brakeDelta = driver1Brake[i] - driver2Brake[i];
      
      return {
        [xAxisKey]: x,
        [`${driver1.driver}_speed`]: driver1Speed[i],
        [`${driver2.driver}_speed`]: driver2Speed[i],
        [`${driver1.driver}_throttle`]: driver1Throttle[i],
        [`${driver2.driver}_throttle`]: driver2Throttle[i],
        [`${driver1.driver}_brake`]: driver1Brake[i],
        [`${driver2.driver}_brake`]: driver2Brake[i],
        [`${driver1.driver}_gear`]: driver1Gear[i],
        [`${driver2.driver}_gear`]: driver2Gear[i],
        [`${driver1.driver}_rpm`]: driver1RPM[i] || 0,
        [`${driver2.driver}_rpm`]: driver2RPM[i] || 0,
        // Delta calculations (Driver1 - Driver2)
        speed_delta: speedDelta,
        throttle_delta: throttleDelta,
        brake_delta: brakeDelta,
        // Separate positive and negative deltas for area charts
        speed_delta_positive: speedDelta > 0 ? speedDelta : 0,
        speed_delta_negative: speedDelta < 0 ? speedDelta : 0,
        throttle_delta_positive: throttleDelta > 0 ? throttleDelta : 0,
        throttle_delta_negative: throttleDelta < 0 ? throttleDelta : 0,
      };
    });

    return combinedData;
  };

  const chartData = getChartData();
  const xAxisKey = viewMode === 'distance' ? 'distance' : 'time';
  const xAxisLabel = viewMode === 'distance' ? 'Distance (m)' : 'Time (s)';

  const formatLapTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(3);
    return `${minutes}:${remainingSeconds.padStart(6, '0')}`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium">
            {viewMode === 'distance' ? `Distance: ${label}m` : `Time: ${label}s`}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value?.toFixed(1)}${entry.name.includes('speed') ? ' km/h' : 
                entry.name.includes('throttle') || entry.name.includes('brake') ? '%' : 
                entry.name.includes('gear') ? '' : ''}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header with driver comparison info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center space-x-3">
            <div 
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: driver1.color }}
            />
            <div>
              <div className="text-lg font-bold text-white">{driver1.driver}</div>
              <div className="text-sm text-gray-400">{driver1.team}</div>
              <div className="text-sm text-green-400">{formatLapTime(driver1.lapTime)}</div>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700 text-center">
          <div className="text-lg font-bold text-white">VS</div>
          <div className="text-sm text-gray-400">
            Gap: {Math.abs(driver1.lapTime - driver2.lapTime).toFixed(3)}s
          </div>
          <div className="text-xs text-gray-500">
            {driver1.lapTime < driver2.lapTime ? driver1.driver : driver2.driver} faster
          </div>
        </div>

        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center space-x-3">
            <div 
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: driver2.color }}
            />
            <div>
              <div className="text-lg font-bold text-white">{driver2.driver}</div>
              <div className="text-sm text-gray-400">{driver2.team}</div>
              <div className="text-sm text-green-400">{formatLapTime(driver2.lapTime)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Delta Speed Chart */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">
          Speed Delta - {driver1.driver} vs {driver2.driver}
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={xAxisKey}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: xAxisLabel, position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Speed Delta (km/h)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              
              {/* Zero reference line */}
              <ReferenceLine y={0} stroke="#9CA3AF" strokeDasharray="2 2" />
              
              {/* Speed delta line */}
              <Line
                type="monotone"
                dataKey="speed_delta"
                stroke="#FBBF24"
                strokeWidth={3}
                dot={false}
                name="Speed Delta"
              />
              
              {/* Positive delta area (Driver1 faster) */}
              <Area
                type="monotone"
                dataKey="speed_delta_positive"
                stroke={driver1.color}
                fill={driver1.color}
                fillOpacity={0.3}
                strokeWidth={0}
                name={`${driver1.driver} faster`}
                connectNulls={false}
              />
              
              {/* Negative delta area (Driver2 faster) */}
              <Area
                type="monotone"
                dataKey="speed_delta_negative"
                stroke={driver2.color}
                fill={driver2.color}
                fillOpacity={0.3}
                strokeWidth={0}
                name={`${driver2.driver} faster`}
                connectNulls={false}
              />

              {/* Corner reference lines */}
              {viewMode === 'distance' && corners.map((corner, index) => (
                <ReferenceLine 
                  key={`corner-${index}`}
                  x={corner.distance}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
              ))}
              
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const delta = chartData.find(d => d[xAxisKey] === label)?.speed_delta || 0;
                    const fasterDriver = delta > 0 ? driver1.driver : driver2.driver;
                    return (
                      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
                        <p className="text-white font-medium">
                          {viewMode === 'distance' ? `Distance: ${label}m` : `Time: ${label}s`}
                        </p>
                        <p className="text-yellow-400">
                          {`Delta: ${Math.abs(delta).toFixed(1)} km/h`}
                        </p>
                        <p className="text-green-400">
                          {`${fasterDriver} faster`}
                        </p>
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
                  paddingBottom: '20px',
                  fontSize: '12px'
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-sm text-gray-400">
          Positive values indicate {driver1.driver} is faster, negative values indicate {driver2.driver} is faster.
        </div>
      </div>

      {/* Sector-by-Sector Analysis */}
      <SectorAnalysis driver1={driver1} driver2={driver2} />

      {/* Speed Comparison */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">Speed Comparison</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={xAxisKey}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: xAxisLabel, position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Speed (km/h)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              
              <Line
                type="monotone"
                dataKey={`${driver1.driver}_speed`}
                stroke={driver1.color}
                strokeWidth={2}
                dot={false}
                name={`${driver1.driver} Speed`}
              />
              
              <Line
                type="monotone"
                dataKey={`${driver2.driver}_speed`}
                stroke={driver2.color}
                strokeWidth={2}
                dot={false}
                name={`${driver2.driver} Speed`}
              />

              {/* Corner reference lines (only for distance mode) */}
              {viewMode === 'distance' && corners.map((corner, index) => (
                <ReferenceLine 
                  key={`corner-${index}`}
                  x={corner.distance}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
              ))}
              
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                verticalAlign="top" 
                height={36}
                iconType="line"
                wrapperStyle={{ 
                  paddingBottom: '20px',
                  fontSize: '12px'
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Throttle vs Brake Comparison */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">Throttle & Brake Comparison</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={xAxisKey}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: xAxisLabel, position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                domain={[0, 100]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Input (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              
              {/* Throttle areas */}
              <Area
                type="monotone"
                dataKey={`${driver1.driver}_throttle`}
                stackId="1"
                stroke={driver1.color}
                fill={driver1.color}
                fillOpacity={0.3}
                name={`${driver1.driver} Throttle`}
              />
              
              <Area
                type="monotone"
                dataKey={`${driver2.driver}_throttle`}
                stackId="2"
                stroke={driver2.color}
                fill={driver2.color}
                fillOpacity={0.3}
                name={`${driver2.driver} Throttle`}
              />

              {/* Brake lines */}
              <Line
                type="monotone"
                dataKey={`${driver1.driver}_brake`}
                stroke={driver1.color}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name={`${driver1.driver} Brake`}
              />
              
              <Line
                type="monotone"
                dataKey={`${driver2.driver}_brake`}
                stroke={driver2.color}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name={`${driver2.driver} Brake`}
              />

              {/* Corner reference lines */}
              {viewMode === 'distance' && corners.map((corner, index) => (
                <ReferenceLine 
                  key={`corner-${index}`}
                  x={corner.distance}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
              ))}
              
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                verticalAlign="top" 
                height={36}
                iconType="line"
                wrapperStyle={{ 
                  paddingBottom: '20px',
                  fontSize: '12px'
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gear Comparison */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">Gear Usage Comparison</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey={xAxisKey}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: xAxisLabel, position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                domain={[1, 8]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Gear', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              
              <Line
                type="stepAfter"
                dataKey={`${driver1.driver}_gear`}
                stroke={driver1.color}
                strokeWidth={3}
                dot={false}
                name={`${driver1.driver} Gear`}
              />
              
              <Line
                type="stepAfter"
                dataKey={`${driver2.driver}_gear`}
                stroke={driver2.color}
                strokeWidth={3}
                dot={false}
                name={`${driver2.driver} Gear`}
              />

              {/* Corner reference lines */}
              {viewMode === 'distance' && corners.map((corner, index) => (
                <ReferenceLine 
                  key={`corner-${index}`}
                  x={corner.distance}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
              ))}
              
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                verticalAlign="top" 
                height={36}
                iconType="line"
                wrapperStyle={{ 
                  paddingBottom: '20px',
                  fontSize: '12px'
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* RPM Comparison */}
      {(driver1.telemetry.rpm?.length || driver2.telemetry.rpm?.length) && (
        <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">RPM Comparison</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey={xAxisKey}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  label={{ value: xAxisLabel, position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
                />
                <YAxis 
                  domain={[0, 'dataMax']}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  label={{ value: 'RPM', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
                />
                
                <Line
                  type="monotone"
                  dataKey={`${driver1.driver}_rpm`}
                  stroke={driver1.color}
                  strokeWidth={2}
                  dot={false}
                  name={`${driver1.driver} RPM`}
                />
                
                <Line
                  type="monotone"
                  dataKey={`${driver2.driver}_rpm`}
                  stroke={driver2.color}
                  strokeWidth={2}
                  dot={false}
                  name={`${driver2.driver} RPM`}
                />

                {/* Corner reference lines */}
                {viewMode === 'distance' && corners.map((corner, index) => (
                  <ReferenceLine 
                    key={`corner-${index}`}
                    x={corner.distance}
                    stroke="#9CA3AF"
                    strokeDasharray="3 3"
                    strokeOpacity={0.4}
                  />
                ))}
                
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  verticalAlign="top" 
                  height={36}
                  iconType="line"
                  wrapperStyle={{ 
                    paddingBottom: '20px',
                    fontSize: '12px'
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Performance Analysis Summary */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">Performance Analysis</h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {Math.max(...driver1.telemetry.speed).toFixed(1)} km/h
            </div>
            <div className="text-sm text-gray-300">{driver1.driver} Max Speed</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {Math.max(...driver2.telemetry.speed).toFixed(1)} km/h
            </div>
            <div className="text-sm text-gray-300">{driver2.driver} Max Speed</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {((driver1.telemetry.throttle.filter(t => t === 100).length / driver1.telemetry.throttle.length) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-300">{driver1.driver} Full Throttle</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {((driver2.telemetry.throttle.filter(t => t === 100).length / driver2.telemetry.throttle.length) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-300">{driver2.driver} Full Throttle</div>
          </div>
          
          {driver1.telemetry.rpm && driver1.telemetry.rpm.length > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {Math.max(...driver1.telemetry.rpm).toFixed(0)} RPM
              </div>
              <div className="text-sm text-gray-300">{driver1.driver} Max RPM</div>
            </div>
          )}
          
          {driver2.telemetry.rpm && driver2.telemetry.rpm.length > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {Math.max(...driver2.telemetry.rpm).toFixed(0)} RPM
              </div>
              <div className="text-sm text-gray-300">{driver2.driver} Max RPM</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverComparisonTelemetry;