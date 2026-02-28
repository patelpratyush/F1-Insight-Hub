import { Pause, Play, RotateCcw, SkipBack, SkipForward } from "lucide-react";
import React, { useEffect, useState } from "react";

interface LapSelectorProps {
  availableLaps: number[];
  selectedLap: number;
  onLapChange: (lapNumber: number) => void;
  isPlaying?: boolean;
  onPlayStateChange?: (playing: boolean) => void;
  playbackSpeed?: number;
  onSpeedChange?: (speed: number) => void;
}

const LapSelector: React.FC<LapSelectorProps> = ({
  availableLaps,
  selectedLap,
  onLapChange,
  isPlaying = false,
  onPlayStateChange,
  playbackSpeed = 1,
  onSpeedChange,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Find current index when selectedLap changes
  useEffect(() => {
    const index = availableLaps.findIndex((lap) => lap === selectedLap);
    if (index !== -1) {
      setCurrentIndex(index);
    }
  }, [selectedLap, availableLaps]);

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying || !onPlayStateChange) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => {
        const nextIndex = prevIndex + 1;
        if (nextIndex >= availableLaps.length) {
          onPlayStateChange(false); // Stop at end
          return prevIndex;
        }
        onLapChange(availableLaps[nextIndex]);
        return nextIndex;
      });
    }, 2000 / playbackSpeed); // Base interval of 2 seconds

    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, availableLaps, onLapChange, onPlayStateChange]);

  const handlePrevious = () => {
    const newIndex = Math.max(0, currentIndex - 1);
    setCurrentIndex(newIndex);
    onLapChange(availableLaps[newIndex]);
  };

  const handleNext = () => {
    const newIndex = Math.min(availableLaps.length - 1, currentIndex + 1);
    setCurrentIndex(newIndex);
    onLapChange(availableLaps[newIndex]);
  };

  const handlePlay = () => {
    if (onPlayStateChange) {
      onPlayStateChange(!isPlaying);
    }
  };

  const handleReset = () => {
    setCurrentIndex(0);
    onLapChange(availableLaps[0]);
    if (onPlayStateChange) {
      onPlayStateChange(false);
    }
  };

  const speedOptions = [0.5, 1, 1.5, 2, 3];

  return (
    <div className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent p-8 rounded-[40px] shadow-2xl">
      <h3 className="text-lg font-bold text-white mb-4">
        Lap Selector & Playback
      </h3>

      {/* Lap Selection Slider */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-300">Lap Number</span>
          <span className="text-lg font-bold text-white">
            Lap {selectedLap} / {availableLaps[availableLaps.length - 1]}
          </span>
        </div>

        <div className="relative">
          <input
            type="range"
            min={0}
            max={availableLaps.length - 1}
            value={currentIndex}
            onChange={(e) => {
              const newIndex = parseInt(e.target.value);
              setCurrentIndex(newIndex);
              onLapChange(availableLaps[newIndex]);
            }}
            className="w-full h-2 bg-white/10 rounded-full appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${(currentIndex / (availableLaps.length - 1)) * 100}%, #374151 ${(currentIndex / (availableLaps.length - 1)) * 100}%, #374151 100%)`,
            }}
          />

          {/* Lap markers */}
          <div className="flex justify-between mt-2 text-xs text-gray-400">
            <span>Lap {availableLaps[0]}</span>
            <span>
              Lap {availableLaps[Math.floor(availableLaps.length / 2)]}
            </span>
            <span>Lap {availableLaps[availableLaps.length - 1]}</span>
          </div>
        </div>
      </div>

      {/* Playback Controls */}
      {onPlayStateChange && (
        <div className="space-y-4">
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={handleReset}
              className="p-3 bg-white/5 hover:bg-white/10 rounded-full transition-colors font-semibold"
              title="Reset to first lap"
            >
              <RotateCcw className="w-5 h-5 text-white" />
            </button>

            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="p-3 bg-white/5 hover:bg-white/10 disabled:bg-transparent disabled:text-white/20 disabled:border disabled:border-white/5 rounded-full transition-colors"
              title="Previous lap"
            >
              <SkipBack className="w-5 h-5 text-white" />
            </button>

            <button
              onClick={handlePlay}
              className="p-3 bg-blue-600 hover:bg-blue-500 rounded-full transition-colors"
              title={isPlaying ? "Pause playback" : "Start playback"}
            >
              {isPlaying ? (
                <Pause className="w-6 h-6 text-white" />
              ) : (
                <Play className="w-6 h-6 text-white" />
              )}
            </button>

            <button
              onClick={handleNext}
              disabled={currentIndex === availableLaps.length - 1}
              className="p-3 bg-white/5 hover:bg-white/10 disabled:bg-transparent disabled:text-white/20 disabled:border disabled:border-white/5 rounded-full transition-colors"
              title="Next lap"
            >
              <SkipForward className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Speed Control */}
          {onSpeedChange && (
            <div className="flex items-center justify-center space-x-4">
              <span className="text-sm text-gray-300">Speed:</span>
              <div className="flex space-x-2">
                {speedOptions.map((speed) => (
                  <button
                    key={speed}
                    onClick={() => onSpeedChange(speed)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      playbackSpeed === speed
                        ? "bg-blue-600 text-white"
                        : "bg-white/5 hover:bg-white/10 text-white/50 hover:text-white"
                    }`}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-400">Progress</span>
              <span className="text-xs text-gray-400">
                {currentIndex + 1} of {availableLaps.length}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-1">
              <div
                className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                style={{
                  width: `${((currentIndex + 1) / availableLaps.length) * 100}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Quick Lap Selection */}
      <div className="mt-6">
        <div className="text-sm text-gray-300 mb-2">Quick Select:</div>
        <div className="flex flex-wrap gap-2">
          {availableLaps.slice(0, 10).map((lap) => (
            <button
              key={lap}
              onClick={() => onLapChange(lap)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedLap === lap
                  ? "bg-blue-600 text-white"
                  : "bg-white/5 hover:bg-white/10 text-white/50 hover:text-white"
              }`}
            >
              L{lap}
            </button>
          ))}
          {availableLaps.length > 10 && (
            <span className="px-3 py-1 text-sm text-gray-400">
              +{availableLaps.length - 10} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LapSelector;
