import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Stint {
  compound: 'soft' | 'medium' | 'hard' | 'intermediate' | 'wet';
  startLap: number;
  endLap: number;
  estimatedTime: number; // seconds
}

interface StrategyTimelineProps {
  stints: Stint[];
  totalTime: number;
  driver: string;
  position?: number;
}

const compoundColors = {
  soft: 'bg-red-500',
  medium: 'bg-yellow-500', 
  hard: 'bg-gray-300',
  intermediate: 'bg-green-500',
  wet: 'bg-blue-500'
};

const compoundLabels = {
  soft: 'S',
  medium: 'M',
  hard: 'H',
  intermediate: 'I',
  wet: 'W'
};

export const StrategyTimeline = ({ stints, totalTime, driver, position }: StrategyTimelineProps) => {
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${minutes}:${secs.padStart(6, '0')}`;
  };

  const totalLaps = stints.reduce((sum, stint) => sum + (stint.endLap - stint.startLap + 1), 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Strategy Timeline - {driver}</span>
          {position && <Badge variant="outline">P{position}</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Stats */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
          <div>
            <p className="text-sm text-muted-foreground">Total Race Time</p>
            <p className="text-lg font-bold">{formatTime(totalTime)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Laps</p>
            <p className="text-lg font-bold">{totalLaps}</p>
          </div>
        </div>

        {/* Timeline Visualization */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Stint Breakdown</h4>
          <div className="space-y-2">
            {stints.map((stint, index) => {
              const stintLaps = stint.endLap - stint.startLap + 1;
              const widthPercentage = (stintLaps / totalLaps) * 100;
              
              return (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span>Stint {index + 1}</span>
                    <span className="text-muted-foreground">
                      Laps {stint.startLap}-{stint.endLap} ({stintLaps} laps)
                    </span>
                  </div>
                  
                  <div className="relative h-8 bg-muted rounded-md overflow-hidden">
                    <div 
                      className={`h-full ${compoundColors[stint.compound]} flex items-center justify-center text-white font-bold text-sm`}
                      style={{ width: `${widthPercentage}%` }}
                    >
                      {compoundLabels[stint.compound]}
                    </div>
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                      {formatTime(stint.estimatedTime)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Pit Stops */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Pit Stops</h4>
          <div className="space-y-1">
            {stints.slice(0, -1).map((_, index) => (
              <div key={index} className="flex justify-between items-center p-2 bg-muted/50 rounded text-sm">
                <span>Pit Stop {index + 1}</span>
                <span className="text-muted-foreground">
                  After Lap {stints[index].endLap}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Tire Compound Legend */}
        <div className="flex flex-wrap gap-2 pt-2 border-t">
          {Object.entries(compoundColors).map(([compound, color]) => (
            <div key={compound} className="flex items-center gap-1 text-xs">
              <div className={`w-3 h-3 rounded ${color}`}></div>
              <span className="capitalize">{compound}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export type { Stint };