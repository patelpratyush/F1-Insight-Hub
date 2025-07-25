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
  ReferenceLine,
  ComposedChart,
  Bar,
  ReferenceArea
} from 'recharts';
import GraphCustomizationPanel from './GraphCustomizationPanel';
import useGraphCustomization from '@/hooks/useGraphCustomization';

interface TelemetryData {
  distance: number[];
  speed: number[];
  throttle: number[];
  brake: number[];
  gear: number[];
  drs?: number[];
}

interface LapInfo {
  driver: string;
  lap_time: number;
  lap_number: number;
  compound: string;
}

interface Corner {
  number: number;
  letter?: string;
  distance: number;
}

interface SpeedTraceProps {
  telemetryData: TelemetryData;
  lapInfo: LapInfo;
  analysis: {
    max_speed: number;
    avg_speed: number;
    braking_zones: number;
    full_throttle_pct: number;
  };
  corners?: Corner[];
}

const TelemetrySpeedTrace: React.FC<SpeedTraceProps> = ({
  telemetryData,
  lapInfo,
  analysis,
  corners = []
}) => {
  // Use graph customization hook
  const {
    customization,
    updateCustomization,
    presetNames,
    savePreset,
    loadPreset,
    getVariableColor
  } = useGraphCustomization();
  // Helper function to safely convert to number
  const safeNumber = (value: any, defaultValue: number = 0): number => {
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? defaultValue : num;
  };

  // Combine all telemetry data into chart-friendly format
  const chartData = telemetryData.distance.map((distance, index) => {
    const speed = safeNumber(telemetryData.speed[index]);
    const throttle = safeNumber(telemetryData.throttle[index]);
    const brake = safeNumber(telemetryData.brake[index]);
    const gear = safeNumber(telemetryData.gear[index]);
    const drs = safeNumber(telemetryData.drs?.[index]);
    
    return {
      distance: Math.round(safeNumber(distance)),
      speed,
      throttle,
      brake,
      gear,
      drs,
      // Combined throttle/brake for overlay visualization
      throttle_normalized: throttle * 3, // Scale for visibility
      brake_negative: -brake * 3, // Negative for visual separation
    };
  });

  const formatLapTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(3);
    return `${minutes}:${remainingSeconds.padStart(6, '0')}`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium">{`Distance: ${label}m`}</p>
          <p className="text-blue-400">{`Speed: ${typeof data.speed === 'number' ? data.speed.toFixed(1) : data.speed || 0} km/h`}</p>
          <p className="text-green-400">{`Throttle: ${typeof data.throttle === 'number' ? data.throttle.toFixed(0) : data.throttle || 0}%`}</p>
          <p className="text-red-400">{`Brake: ${typeof data.brake === 'number' ? data.brake.toFixed(0) : data.brake || 0}%`}</p>
          <p className="text-purple-400">{`Gear: ${data.gear || 'N/A'}`}</p>
          {data.drs && data.drs > 0 && <p className="text-yellow-400">DRS: Active</p>}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Graph Customization Panel */}
      <GraphCustomizationPanel
        customization={customization}
        onCustomizationChange={updateCustomization}
        onSavePreset={savePreset}
        onLoadPreset={loadPreset}
        presetNames={presetNames}
      />

      {/* Lap Information Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Driver</div>
          <div className="text-lg font-bold text-white">{lapInfo.driver}</div>
        </div>
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Lap Time</div>
          <div className="text-lg font-bold text-green-400">
            {formatLapTime(lapInfo.lap_time)}
          </div>
        </div>
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Max Speed</div>
          <div className="text-lg font-bold text-blue-400">
            {analysis.max_speed.toFixed(1)} km/h
          </div>
        </div>
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Tire Compound</div>
          <div className="text-lg font-bold text-purple-400">{lapInfo.compound}</div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Average Speed</div>
          <div className="text-xl font-bold text-blue-400">
            {analysis.avg_speed.toFixed(1)} km/h
          </div>
        </div>
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Full Throttle</div>
          <div className="text-xl font-bold text-green-400">
            {analysis.full_throttle_pct.toFixed(1)}%
          </div>
        </div>
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <div className="text-sm text-gray-400">Braking Zones</div>
          <div className="text-xl font-bold text-red-400">
            {analysis.braking_zones}
          </div>
        </div>
      </div>

      {/* Main Speed Trace with Throttle/Brake Overlay */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">
          Speed Trace with Throttle/Brake Inputs
        </h3>
        <div className="h-[450px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="distance" 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                yAxisId="speed"
                domain={[0, 'dataMax']}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Speed (km/h)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                yAxisId="inputs"
                orientation="right"
                domain={[-300, 300]}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Throttle/Brake (%)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
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
              
              {/* Throttle area (positive) */}
              <Area
                yAxisId="inputs"
                type="monotone"
                dataKey="throttle_normalized"
                stackId="1"
                stroke="#10B981"
                fill="#10B981"
                fillOpacity={0.6}
                name="Throttle"
              />
              
              {/* Brake area (negative) */}
              <Area
                yAxisId="inputs"
                type="monotone"
                dataKey="brake_negative"
                stackId="2"
                stroke="#EF4444"
                fill="#EF4444"
                fillOpacity={0.6}
                name="Brake"
              />
              
              {/* Reference line at zero for throttle/brake */}
              <ReferenceLine yAxisId="inputs" y={0} stroke="#6B7280" strokeDasharray="2 2" />
              
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

      {/* Gear Usage Chart */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">Gear Usage Throughout Lap</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="distance"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
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
                dataKey="gear"
                stroke="#8B5CF6"
                strokeWidth={3}
                dot={false}
                name="Gear"
              />
              <Tooltip content={<CustomTooltip />} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Throttle vs Brake Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">Throttle Application</h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="distance"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF', fontSize: '10px' } }}
                />
                <YAxis 
                  domain={[0, 100]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  label={{ value: 'Throttle (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF', fontSize: '10px' } }}
                />
                <Area
                  type="monotone"
                  dataKey="throttle"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.6}
                />
                <Tooltip content={<CustomTooltip />} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">Brake Pressure</h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="distance"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF', fontSize: '10px' } }}
                />
                <YAxis 
                  domain={[0, 100]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#9CA3AF', fontSize: 10 }}
                  label={{ value: 'Brake (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF', fontSize: '10px' } }}
                />
                <Area
                  type="monotone"
                  dataKey="brake"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.6}
                />
                <Tooltip content={<CustomTooltip />} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Corner-Annotated Speed Trace */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">
          Speed Trace with Corner Annotations
        </h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="distance" 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Distance (m)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              <YAxis 
                domain={['dataMin - 40', 'dataMax + 20']}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ value: 'Speed (km/h)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#9CA3AF' } }}
              />
              
              {/* Speed line */}
              <Line
                type="monotone"
                dataKey="speed"
                stroke="#3B82F6"
                strokeWidth={3}
                dot={false}
                name="Speed"
              />
              
              {/* Corner reference lines */}
              {corners.map((corner, index) => (
                <ReferenceLine 
                  key={`corner-${index}`}
                  x={corner.distance}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  strokeOpacity={0.6}
                />
              ))}
              
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    // Find if we're near a corner
                    const currentDistance = parseFloat(label);
                    const nearbyCorner = corners.find(corner => 
                      Math.abs(corner.distance - currentDistance) < 100
                    );
                    
                    return (
                      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
                        <p className="text-white font-medium">{`Distance: ${label}m`}</p>
                        <p className="text-blue-400">{`Speed: ${payload[0]?.value?.toFixed(1)} km/h`}</p>
                        {nearbyCorner && (
                          <p className="text-yellow-400">{`Corner ${nearbyCorner.number}${nearbyCorner.letter || ''}`}</p>
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
                iconType="line"
                wrapperStyle={{ 
                  paddingBottom: '20px',
                  fontSize: '12px'
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Corner legend */}
        {corners.length > 0 && (
          <div className="mt-4 p-4 bg-gray-700/30 rounded-lg">
            <h4 className="text-sm font-bold text-white mb-2">Track Corners</h4>
            <div className="grid grid-cols-6 md:grid-cols-12 gap-2 text-xs">
              {corners.map((corner, index) => (
                <div key={index} className="text-center">
                  <div className="text-yellow-400 font-bold">
                    {corner.number}{corner.letter || ''}
                  </div>
                  <div className="text-gray-400">
                    {Math.round(corner.distance)}m
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="mt-4 text-sm text-gray-400">
          Dotted vertical lines indicate corner locations. Speed typically drops before corners and increases on exit.
        </div>
      </div>
    </div>
  );
};

export default TelemetrySpeedTrace;