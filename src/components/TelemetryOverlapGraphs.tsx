import React, { useState, useRef, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush
} from 'recharts';
import { Eye, EyeOff, ZoomIn, ZoomOut, RotateCcw, Settings2 } from 'lucide-react';

interface TelemetryData {
  distance: number[];
  time: number[];
  speed: number[];
  throttle: number[];
  brake: number[];
  gear: number[];
  rpm?: number[];
  drs?: number[];
}

interface TelemetryVariable {
  key: keyof TelemetryData;
  label: string;
  color: string;
  yAxisId: string;
  unit: string;
  enabled: boolean;
}

interface TelemetryOverlapGraphsProps {
  telemetryData: TelemetryData;
  driverName: string;
  lapNumber: number;
  viewMode?: 'distance' | 'time';
  onViewModeChange?: (mode: 'distance' | 'time') => void;
  corners?: Array<{
    number: number;
    distance: number;
  }>;
}

const TelemetryOverlapGraphs: React.FC<TelemetryOverlapGraphsProps> = ({
  telemetryData,
  driverName,
  lapNumber,
  viewMode = 'distance',
  onViewModeChange,
  corners = []
}) => {
  const chartRef = useRef<any>(null);
  
  // Default telemetry variables configuration
  const [variables, setVariables] = useState<TelemetryVariable[]>([
    { key: 'speed', label: 'Speed', color: '#3B82F6', yAxisId: 'speed', unit: 'km/h', enabled: true },
    { key: 'throttle', label: 'Throttle', color: '#10B981', yAxisId: 'percentage', unit: '%', enabled: true },
    { key: 'brake', label: 'Brake', color: '#EF4444', yAxisId: 'percentage', unit: '%', enabled: true },
    { key: 'gear', label: 'Gear', color: '#F59E0B', yAxisId: 'gear', unit: '', enabled: false },
    { key: 'rpm', label: 'RPM', color: '#8B5CF6', yAxisId: 'rpm', unit: 'RPM', enabled: false },
    { key: 'drs', label: 'DRS', color: '#EC4899', yAxisId: 'drs', unit: '', enabled: false }
  ]);

  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState(0);
  const [showBrush, setShowBrush] = useState(false);
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

  // Toggle variable visibility
  const toggleVariable = (key: keyof TelemetryData) => {
    setVariables(prev => prev.map(v => 
      v.key === key ? { ...v, enabled: !v.enabled } : v
    ));
  };

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!telemetryData || !telemetryData.distance || !telemetryData.time) {
      return [];
    }

    const xAxisKey = viewMode === 'distance' ? 'distance' : 'time';
    const xValues = telemetryData[xAxisKey];
    
    return xValues.map((x, index) => {
      const dataPoint: any = {
        [xAxisKey]: x,
        index: index
      };

      // Add all telemetry variables
      variables.forEach(variable => {
        const data = telemetryData[variable.key];
        if (data && data[index] !== undefined) {
          dataPoint[variable.key] = data[index];
        }
      });

      return dataPoint;
    });
  }, [telemetryData, viewMode, variables]);

  // Get enabled variables
  const enabledVariables = variables.filter(v => v.enabled);

  // Group variables by Y-axis
  const yAxisGroups = useMemo(() => {
    const groups: { [key: string]: TelemetryVariable[] } = {};
    enabledVariables.forEach(variable => {
      if (!groups[variable.yAxisId]) {
        groups[variable.yAxisId] = [];
      }
      groups[variable.yAxisId].push(variable);
    });
    return groups;
  }, [enabledVariables]);

  const xAxisKey = viewMode === 'distance' ? 'distance' : 'time';
  const xAxisLabel = viewMode === 'distance' ? 'Distance (m)' : 'Time (s)';

  // Reset zoom and pan
  const resetView = () => {
    setZoomLevel(1);
    setPanOffset(0);
    setShowBrush(false);
    setZoomDomain(null);
  };

  // Handle brush change for zooming
  const handleBrushChange = (domain: any) => {
    if (domain && domain.startIndex !== undefined && domain.endIndex !== undefined) {
      const xAxisKey = viewMode === 'distance' ? 'distance' : 'time';
      const startValue = chartData[domain.startIndex]?.[xAxisKey];
      const endValue = chartData[domain.endIndex]?.[xAxisKey];
      
      if (startValue !== undefined && endValue !== undefined) {
        setZoomDomain([startValue, endValue]);
      }
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium mb-2">
            {viewMode === 'distance' ? `Distance: ${label}m` : `Time: ${label}s`}
          </p>
          {payload.map((entry: any, index: number) => {
            const variable = variables.find(v => v.key === entry.dataKey);
            if (!variable) return null;
            
            return (
              <p key={index} style={{ color: entry.color }} className="text-sm">
                {`${variable.label}: ${entry.value?.toFixed(1)}${variable.unit}`}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white mb-2">
              Telemetry Overlap Analysis - {driverName}
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <span>Lap {lapNumber}</span>
              <span>•</span>
              <span>{enabledVariables.length} variables active</span>
            </div>
          </div>

          {/* View Mode Toggle */}
          {onViewModeChange && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-300">X-Axis:</span>
              <div className="flex bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => onViewModeChange('distance')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === 'distance'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Distance
                </button>
                <button
                  onClick={() => onViewModeChange('time')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === 'time'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Time
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Variable Toggle Controls */}
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-300">Telemetry Variables</h4>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowBrush(!showBrush)}
                className={`p-2 rounded-lg transition-colors ${
                  showBrush ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
                title="Toggle zoom brush"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={resetView}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-gray-300"
                title="Reset view"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {variables.map((variable) => {
              const hasData = telemetryData[variable.key] && telemetryData[variable.key]!.length > 0;
              
              return (
                <button
                  key={variable.key}
                  onClick={() => toggleVariable(variable.key)}
                  disabled={!hasData}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg border transition-all ${
                    variable.enabled && hasData
                      ? 'bg-gray-700 border-gray-500 text-white'
                      : hasData
                      ? 'bg-gray-800 border-gray-600 text-gray-400 hover:bg-gray-700'
                      : 'bg-gray-900 border-gray-700 text-gray-600 cursor-not-allowed opacity-50'
                  }`}
                >
                  {variable.enabled && hasData ? (
                    <Eye className="w-4 h-4" style={{ color: variable.color }} />
                  ) : (
                    <EyeOff className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium">{variable.label}</span>
                  {hasData && (
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: variable.color }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Overlap Chart */}
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart 
              data={chartData} 
              ref={chartRef}
              margin={{ top: 20, right: 60, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              
              {/* X-Axis */}
              <XAxis 
                dataKey={xAxisKey}
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                label={{ 
                  value: xAxisLabel, 
                  position: 'insideBottom', 
                  offset: -10, 
                  style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                }}
                domain={zoomDomain || ['dataMin', 'dataMax']}
              />

              {/* Multiple Y-Axes for different variable types */}
              {Object.entries(yAxisGroups).map(([yAxisId, groupVariables], index) => {
                const isLeft = index % 2 === 0;
                const yAxisProps: any = {
                  yAxisId,
                  axisLine: false,
                  tickLine: false,
                  tick: { fill: '#9CA3AF', fontSize: 12 },
                  orientation: isLeft ? 'left' : 'right',
                };

                // Set domain and label based on variable type
                if (yAxisId === 'percentage') {
                  yAxisProps.domain = [0, 100];
                  yAxisProps.label = { 
                    value: 'Percentage (%)', 
                    angle: -90, 
                    position: isLeft ? 'insideLeft' : 'insideRight',
                    style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                  };
                } else if (yAxisId === 'gear') {
                  yAxisProps.domain = [1, 8];
                  yAxisProps.label = { 
                    value: 'Gear', 
                    angle: -90, 
                    position: isLeft ? 'insideLeft' : 'insideRight',
                    style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                  };
                } else if (yAxisId === 'speed') {
                  yAxisProps.label = { 
                    value: 'Speed (km/h)', 
                    angle: -90, 
                    position: isLeft ? 'insideLeft' : 'insideRight',
                    style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                  };
                } else if (yAxisId === 'rpm') {
                  yAxisProps.label = { 
                    value: 'RPM', 
                    angle: -90, 
                    position: isLeft ? 'insideLeft' : 'insideRight',
                    style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                  };
                } else if (yAxisId === 'drs') {
                  yAxisProps.domain = [0, 1];
                  yAxisProps.label = { 
                    value: 'DRS', 
                    angle: -90, 
                    position: isLeft ? 'insideLeft' : 'insideRight',
                    style: { textAnchor: 'middle', fill: '#9CA3AF' } 
                  };
                }

                return <YAxis key={yAxisId} {...yAxisProps} />;
              })}

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

              {/* Telemetry Lines */}
              {enabledVariables.map((variable) => (
                <Line
                  key={variable.key}
                  type="monotone"
                  dataKey={variable.key}
                  stroke={variable.color}
                  strokeWidth={2}
                  dot={false}
                  name={variable.label}
                  yAxisId={variable.yAxisId}
                  connectNulls={false}
                />
              ))}

              {/* Zoom Brush */}
              {showBrush && (
                <Brush
                  dataKey={xAxisKey}
                  height={30}
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.1}
                  onChange={handleBrushChange}
                />
              )}

              <Tooltip content={<CustomTooltip />} />
              <Legend 
                verticalAlign="top" 
                height={50}
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

      {/* Variable Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {enabledVariables.map((variable) => {
          const data = telemetryData[variable.key];
          if (!data || data.length === 0) return null;

          const values = data.filter(v => v !== undefined && v !== null) as number[];
          const max = Math.max(...values);
          const min = Math.min(...values);
          const avg = values.reduce((a, b) => a + b, 0) / values.length;

          return (
            <div key={variable.key} className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center space-x-2 mb-3">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: variable.color }}
                />
                <h4 className="font-medium text-white">{variable.label}</h4>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Max:</span>
                  <span className="text-white font-medium">
                    {max.toFixed(1)}{variable.unit}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Min:</span>
                  <span className="text-white font-medium">
                    {min.toFixed(1)}{variable.unit}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg:</span>
                  <span className="text-white font-medium">
                    {avg.toFixed(1)}{variable.unit}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TelemetryOverlapGraphs;