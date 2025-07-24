import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Eye, EyeOff, Palette } from 'lucide-react';

interface TrackPosition {
  distance: number;
  x: number;
  y: number;
  speed: number;
  time: number;
}

interface TrackMapData {
  track_layout: {
    x: number[];
    y: number[];
    distance: number[];
  };
  driver_positions: TrackPosition[];
  racing_line?: {
    x: number[];
    y: number[];
  };
  sectors?: {
    sector_1_end: number;
    sector_2_end: number;
    sector_3_end: number;
  };
  corners?: Array<{
    number: number;
    x: number;
    y: number;
    distance: number;
  }>;
}

interface InteractiveTrackMapProps {
  trackData: TrackMapData;
  driverName: string;
  lapNumber: number;
  isPlaying?: boolean;
  onPlayStateChange?: (playing: boolean) => void;
  showRacingLine?: boolean;
  onRacingLineToggle?: (show: boolean) => void;
  colorScheme?: 'speed' | 'time' | 'position';
}

const InteractiveTrackMap: React.FC<InteractiveTrackMapProps> = ({
  trackData,
  driverName,
  lapNumber,
  isPlaying = false,
  onPlayStateChange,
  showRacingLine = true,
  onRacingLineToggle,
  colorScheme = 'speed'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [currentPosition, setCurrentPosition] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationSpeed, setAnimationSpeed] = useState(1);
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  // Calculate SVG viewport dimensions
  const getViewBox = () => {
    if (!trackData?.track_layout) return "0 0 1000 1000";
    
    const { x, y } = trackData.track_layout;
    const minX = Math.min(...x);
    const maxX = Math.max(...x);
    const minY = Math.min(...y);
    const maxY = Math.max(...y);
    
    const padding = 50;
    const width = maxX - minX + (padding * 2);
    const height = maxY - minY + (padding * 2);
    
    return `${minX - padding} ${minY - padding} ${width} ${height}`;
  };

  // Get color based on speed value
  const getSpeedColor = (speed: number, maxSpeed: number) => {
    const normalizedSpeed = speed / maxSpeed;
    
    if (normalizedSpeed < 0.3) return '#EF4444'; // Red - slow
    if (normalizedSpeed < 0.5) return '#F59E0B'; // Orange - medium-slow
    if (normalizedSpeed < 0.7) return '#EAB308'; // Yellow - medium
    if (normalizedSpeed < 0.85) return '#84CC16'; // Light green - fast
    return '#10B981'; // Green - very fast
  };

  // Get color based on position in lap (time-based)
  const getTimeColor = (position: number, totalPositions: number) => {
    const normalizedTime = position / totalPositions;
    
    // Blue to purple gradient for time progression
    const blue = Math.floor(59 + (normalizedTime * 120)); // 59 to 179
    const purple = Math.floor(130 + (normalizedTime * 100)); // 130 to 230
    
    return `rgb(${Math.floor(purple * 0.6)}, ${Math.floor(blue * 0.8)}, ${purple})`;
  };

  // Animation effect
  useEffect(() => {
    if (!isAnimating || !trackData?.driver_positions) return;

    const interval = setInterval(() => {
      setCurrentPosition(prev => {
        const next = prev + (1 * animationSpeed);
        if (next >= trackData.driver_positions.length - 1) {
          setIsAnimating(false);
          if (onPlayStateChange) onPlayStateChange(false);
          return trackData.driver_positions.length - 1;
        }
        return next;
      });
    }, 50); // 50ms interval for smooth animation

    return () => clearInterval(interval);
  }, [isAnimating, animationSpeed, trackData, onPlayStateChange]);

  // Handle play/pause
  const handlePlayPause = () => {
    const newIsAnimating = !isAnimating;
    setIsAnimating(newIsAnimating);
    if (onPlayStateChange) {
      onPlayStateChange(newIsAnimating);
    }
  };

  // Reset to start
  const handleReset = () => {
    setCurrentPosition(0);
    setIsAnimating(false);
    if (onPlayStateChange) onPlayStateChange(false);
  };

  if (!trackData?.track_layout) {
    return (
      <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Interactive Track Map</h3>
        <div className="h-96 bg-gray-700/30 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="text-gray-400 mb-2">Track layout data not available</div>
            <div className="text-sm text-gray-500">Try selecting a different session or driver</div>
          </div>
        </div>
      </div>
    );
  }

  const maxSpeed = Math.max(...trackData.driver_positions.map(p => p.speed));
  const currentPoint = trackData.driver_positions[Math.floor(currentPosition)];

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">
          Interactive Track Map - {driverName}
        </h3>
        <div className="bg-blue-600/20 border border-blue-600/40 rounded-lg px-3 py-1">
          <span className="text-blue-400 font-medium text-sm">
            Lap {lapNumber}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReset}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            title="Reset to start"
          >
            <RotateCcw className="w-4 h-4 text-white" />
          </button>
          
          <button
            onClick={handlePlayPause}
            className="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            title={isAnimating ? "Pause animation" : "Start animation"}
          >
            {isAnimating ? (
              <Pause className="w-4 h-4 text-white" />
            ) : (
              <Play className="w-4 h-4 text-white" />
            )}
          </button>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-300">Speed:</span>
            {[0.5, 1, 2, 3].map(speed => (
              <button
                key={speed}
                onClick={() => setAnimationSpeed(speed)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  animationSpeed === speed
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {onRacingLineToggle && (
            <button
              onClick={() => onRacingLineToggle(!showRacingLine)}
              className={`p-2 rounded-lg transition-colors ${
                showRacingLine 
                  ? 'bg-green-600 hover:bg-green-500' 
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
              title="Toggle racing line"
            >
              {showRacingLine ? (
                <Eye className="w-4 h-4 text-white" />
              ) : (
                <EyeOff className="w-4 h-4 text-white" />
              )}
            </button>
          )}

          <div className="flex items-center space-x-2">
            <Palette className="w-4 h-4 text-gray-400" />
            <select
              value={colorScheme}
              onChange={(e) => {
                // Handle color scheme change if parent provides handler
              }}
              className="bg-gray-700 border border-gray-600 text-white text-sm rounded px-2 py-1"
            >
              <option value="speed">Speed</option>
              <option value="time">Time</option>
              <option value="position">Position</option>
            </select>
          </div>
        </div>
      </div>

      {/* Track Map SVG */}
      <div className="bg-gray-900/50 rounded-lg p-4 h-96">
        <svg
          ref={svgRef}
          viewBox={getViewBox()}
          className="w-full h-full"
          style={{ background: '#1a1a1a' }}
        >
          {/* Track Layout */}
          <path
            d={`M ${trackData.track_layout.x.map((x, i) => 
              `${x},${trackData.track_layout.y[i]}`
            ).join(' L ')}`}
            fill="none"
            stroke="#6B7280"
            strokeWidth="16"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Track center line */}
          <path
            d={`M ${trackData.track_layout.x.map((x, i) => 
              `${x},${trackData.track_layout.y[i]}`
            ).join(' L ')}`}
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="2"
            strokeDasharray="8,4"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.6"
          />

          {/* Racing Line */}
          {showRacingLine && trackData.racing_line && (
            <path
              d={`M ${trackData.racing_line.x.map((x, i) => 
                `${x},${trackData.racing_line.y[i]}`
              ).join(' L ')}`}
              fill="none"
              stroke="#FBBF24"
              strokeWidth="2"
              strokeDasharray="5,5"
              opacity={0.7}
            />
          )}

          {/* Sector Boundaries */}
          {trackData.sectors && trackData.track_layout.distance && (
            <>
              {[trackData.sectors.sector_1_end, trackData.sectors.sector_2_end].map((sectorEnd, index) => {
                const closestIndex = trackData.track_layout.distance.findIndex(d => d >= sectorEnd);
                if (closestIndex === -1) return null;
                
                const x = trackData.track_layout.x[closestIndex];
                const y = trackData.track_layout.y[closestIndex];
                
                return (
                  <g key={`sector-${index}`}>
                    <circle
                      cx={x}
                      cy={y}
                      r="12"
                      fill="#DC2626"
                      stroke="#FFFFFF"
                      strokeWidth="3"
                    />
                    <text
                      x={x}
                      y={y + 5}
                      textAnchor="middle"
                      fill="#FFFFFF"
                      fontSize="10"
                      fontWeight="bold"
                    >
                      S{index + 1}
                    </text>
                    <rect
                      x={x - 20}
                      y={y + 15}
                      width="40"
                      height="16"
                      fill="#000000"
                      opacity="0.8"
                      rx="8"
                    />
                    <text
                      x={x}
                      y={y + 27}
                      textAnchor="middle"
                      fill="#FFFFFF"
                      fontSize="10"
                      fontWeight="bold"
                    >
                      Sector {index + 1}
                    </text>
                  </g>
                );
              })}
            </>
          )}

          {/* Driver Trail (showing path taken so far) */}
          {trackData.driver_positions.slice(0, Math.floor(currentPosition) + 1).map((point, index) => {
            if (index % 3 !== 0) return null; // Sample every 3rd point for better visibility
            
            const color = colorScheme === 'speed' 
              ? getSpeedColor(point.speed, maxSpeed)
              : getTimeColor(index, trackData.driver_positions.length);
            
            const opacity = Math.max(0.4, 1 - (Math.floor(currentPosition) - index) / 80);
            const radius = Math.max(2, 4 - (Math.floor(currentPosition) - index) / 50);
            
            return (
              <circle
                key={`trail-${index}`}
                cx={point.x}
                cy={point.y}
                r={radius}
                fill={color}
                opacity={opacity}
                stroke="#FFFFFF"
                strokeWidth="0.5"
              />
            );
          })}

          {/* Current Car Position - SUPER VISIBLE */}
          {currentPoint && (
            <g>
              {/* Massive outer glow effect */}
              <circle
                cx={currentPoint.x}
                cy={currentPoint.y}
                r="40"
                fill="#FF0000"
                opacity="0.4"
              >
                <animate
                  attributeName="r"
                  values="40;60;40"
                  dur="2s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values="0.4;0.1;0.4"
                  dur="2s"
                  repeatCount="indefinite"
                />
              </circle>
              
              {/* Secondary glow */}
              <circle
                cx={currentPoint.x}
                cy={currentPoint.y}
                r="25"
                fill="#FF4444"
                opacity="0.6"
              >
                <animate
                  attributeName="r"
                  values="25;35;25"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
              
              {/* Main car position - HUGE */}
              <circle
                cx={currentPoint.x}
                cy={currentPoint.y}
                r="20"
                fill="#FF0000"
                stroke="#FFFFFF"
                strokeWidth="6"
              >
                <animate
                  attributeName="r"
                  values="20;28;20"
                  dur="1s"
                  repeatCount="indefinite"
                />
              </circle>
              
              {/* Inner core */}
              <circle
                cx={currentPoint.x}
                cy={currentPoint.y}
                r="12"
                fill="#FFFF00"
                opacity="1"
              >
                <animate
                  attributeName="fill"
                  values="#FFFF00;#FF0000;#FFFF00"
                  dur="0.8s"
                  repeatCount="indefinite"
                />
              </circle>
              
              {/* Center dot */}
              <circle
                cx={currentPoint.x}
                cy={currentPoint.y}
                r="6"
                fill="#FFFFFF"
                opacity="1"
              />
              
              {/* Speed indicator with larger background */}
              <rect
                x={currentPoint.x - 50}
                y={currentPoint.y - 60}
                width="100"
                height="30"
                fill="#000000"
                opacity="0.9"
                rx="15"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={currentPoint.x}
                y={currentPoint.y - 35}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="18"
                fontWeight="bold"
              >
                🏎️ {Math.round(currentPoint.speed)} km/h
              </text>
              
              {/* Arrow pointing to car */}
              <polygon
                points={`${currentPoint.x - 8},${currentPoint.y - 80} ${currentPoint.x + 8},${currentPoint.y - 80} ${currentPoint.x},${currentPoint.y - 65}`}
                fill="#FFFF00"
                stroke="#000000"
                strokeWidth="2"
              >
                <animateTransform
                  attributeName="transform"
                  type="translate"
                  values={`0,-5; 0,5; 0,-5`}
                  dur="1s"
                  repeatCount="indefinite"
                />
              </polygon>
              
              {/* "DRIVER" label */}
              <rect
                x={currentPoint.x - 30}
                y={currentPoint.y + 30}
                width="60"
                height="20"
                fill="#FF0000"
                opacity="0.9"
                rx="10"
                stroke="#FFFFFF"
                strokeWidth="2"
              />
              <text
                x={currentPoint.x}
                y={currentPoint.y + 45}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="12"
                fontWeight="bold"
              >
                DRIVER
              </text>
            </g>
          )}

          {/* Corner Numbers */}
          {trackData.corners?.map((corner, index) => (
            <g key={`corner-${index}`}>
              <circle
                cx={corner.x}
                cy={corner.y}
                r="18"
                fill="rgba(59, 130, 246, 0.4)"
                stroke="#3B82F6"
                strokeWidth="3"
              />
              <circle
                cx={corner.x}
                cy={corner.y}
                r="12"
                fill="#3B82F6"
                opacity="0.8"
              />
              <text
                x={corner.x}
                y={corner.y + 5}
                textAnchor="middle"
                fill="#FFFFFF"
                fontSize="14"
                fontWeight="bold"
              >
                {corner.number}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Progress Information */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="text-center">
          <div className="text-lg font-bold text-blue-400">
            {currentPoint ? Math.round(currentPoint.speed) : 0} km/h
          </div>
          <div className="text-gray-300">Current Speed</div>
        </div>
        
        <div className="text-center">
          <div className="text-lg font-bold text-green-400">
            {currentPoint ? (currentPoint.distance / 1000).toFixed(2) : 0} km
          </div>
          <div className="text-gray-300">Distance</div>
        </div>
        
        <div className="text-center">
          <div className="text-lg font-bold text-yellow-400">
            {currentPoint ? currentPoint.time.toFixed(1) : 0}s
          </div>
          <div className="text-gray-300">Elapsed Time</div>
        </div>
        
        <div className="text-center">
          <div className="text-lg font-bold text-purple-400">
            {((currentPosition / (trackData.driver_positions.length - 1)) * 100).toFixed(1)}%
          </div>
          <div className="text-gray-300">Progress</div>
        </div>
      </div>

      {/* Color Legend */}
      <div className="mt-4 p-3 bg-gray-700/30 rounded-lg">
        <div className="text-sm font-medium text-white mb-2">Color Legend ({colorScheme}):</div>
        <div className="flex items-center space-x-4 text-xs">
          {colorScheme === 'speed' && (
            <>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span className="text-gray-300">Slow</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span className="text-gray-300">Medium</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                <span className="text-gray-300">Fast</span>
              </div>
            </>
          )}
          {colorScheme === 'time' && (
            <>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span className="text-gray-300">Lap Start</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-purple-500 rounded"></div>
                <span className="text-gray-300">Lap End</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default InteractiveTrackMap;