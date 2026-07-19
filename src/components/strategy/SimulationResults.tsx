import StaggeredAnimation from "@/components/StaggeredAnimation";
import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Clock, Gauge, Target, Timer, TrendingUp } from "lucide-react";

interface SimulationResultsProps {
  simulation: any;
  getTireColor: (tire: string) => string;
}

const SimulationResults = ({ simulation, getTireColor }: SimulationResultsProps) => {
  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <StaggeredAnimation
        delay={300}
        staggerDelay={150}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        {[
          <Card
            key="time"
            className="bg-transparent border-0 shadow-none"
          >
            <CardContent className="text-center p-6 bg-white/5 rounded-[24px]">
              <Clock className="h-6 w-6 text-blue-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-blue-400">
                {simulation.totalTime}
              </div>
              <div className="text-sm text-gray-300">
                Total Race Time
              </div>
            </CardContent>
          </Card>,

          <Card
            key="position"
            className="bg-transparent border-0 shadow-none"
          >
            <CardContent className="text-center p-6 bg-white/5 rounded-[24px]">
              <Target className="h-6 w-6 text-green-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-green-400">
                P{simulation.position}
              </div>
              <div className="text-sm text-gray-300">
                Predicted Position
              </div>
            </CardContent>
          </Card>,

          <Card
            key="efficiency"
            className="bg-transparent border-0 shadow-none"
          >
            <CardContent className="text-center p-6 bg-white/5 rounded-[24px]">
              <TrendingUp className="h-6 w-6 text-purple-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-purple-400">
                {simulation.efficiency}%
              </div>
              <div className="text-sm text-gray-300">
                Strategy Efficiency
              </div>
            </CardContent>
          </Card>,

          <Card
            key="confidence"
            className="bg-transparent border-0 shadow-none"
          >
            <CardContent className="text-center p-6 bg-white/5 rounded-[24px]">
              <Gauge className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-yellow-400">
                {simulation.confidence}%
              </div>
              <div className="text-sm text-gray-300">Confidence</div>
            </CardContent>
          </Card>,
        ]}
      </StaggeredAnimation>

      {/* Stint Breakdown */}
      <Card className="bg-transparent border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
            <Timer className="h-5 w-5 text-purple-500" />
            <span>Stint Analysis</span>
          </CardTitle>
          <CardDescription className="text-gray-400">
            Detailed breakdown of each racing stint
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {simulation.stints.map((stint, index) => (
              <div
                key={index}
                className="flex items-center p-4 bg-white/5 rounded-[24px]"
              >
                <div className="flex items-center space-x-4 flex-1">
                  <div className="text-center">
                    <div className="text-sm text-gray-400">Stint</div>
                    <div className="text-lg font-bold text-white">
                      {stint.stint}
                    </div>
                  </div>

                  <div
                    className={`w-4 h-4 rounded-full ${getTireColor(stint.tire)}`}
                  ></div>
                  <div>
                    <div className="font-medium text-white">
                      {stint.tire} Compound
                    </div>
                    <div className="text-sm text-gray-400">
                      {stint.laps} laps (L{stint.startLap}-L
                      {stint.endLap})
                    </div>
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <div className="text-white font-medium">
                    {stint.avgLapTime}
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      stint.degradation === "High"
                        ? "text-red-400 border-red-400"
                        : stint.degradation === "Medium"
                          ? "text-yellow-400 border-yellow-400"
                          : "text-green-400 border-green-400"
                    }`}
                  >
                    {stint.degradation} Deg
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strategy Timeline */}
      <Card className="bg-transparent border-0 shadow-none">
        <CardHeader>
          <CardTitle className="font-bold text-white">
            Strategy Timeline
          </CardTitle>
          <CardDescription className="text-gray-400">
            Visual representation of pit stops and tire changes
            throughout the race
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Timeline Header */}
            <div className="flex justify-between items-center text-sm text-gray-400">
              <span>Lap 1</span>
              <span>Mid-Race</span>
              <span>Final Lap</span>
            </div>

            {/* Timeline Bar */}
            <div className="relative h-12 bg-[#222] rounded-full overflow-hidden">
              {simulation.stints.map((stint, index) => {
                const totalLaps = simulation.stints.reduce(
                  (sum, s) => sum + s.laps,
                  0,
                );
                const width = (stint.laps / totalLaps) * 100;
                const left =
                  (simulation.stints
                    .slice(0, index)
                    .reduce((sum, s) => sum + s.laps, 0) /
                    totalLaps) *
                  100;

                return (
                  <div
                    key={index}
                    className={`absolute top-0 h-full flex items-center justify-center text-white text-xs font-medium border-r border-[#111111] ${getTireColor(stint.tire)} ${getTireColor(stint.tire).replace("bg-", "bg-opacity-80 bg-")}`}
                    style={{ left: `${left}%`, width: `${width}%` }}
                  >
                    <div className="text-center">
                      <div className="font-bold">
                        {stint.tire.charAt(0)}
                      </div>
                      <div className="text-xs">{stint.laps}L</div>
                    </div>
                  </div>
                );
              })}

              {/* Pit Stop Markers */}
              {simulation.pitStops &&
                simulation.pitStops.map((pitStop, index) => {
                  const totalLaps = simulation.stints.reduce(
                    (sum, s) => sum + s.laps,
                    0,
                  );
                  const position = (pitStop.lap / totalLaps) * 100;

                  return (
                    <div
                      key={index}
                      className="absolute top-0 h-full w-1 bg-yellow-400 opacity-80"
                      style={{ left: `${position}%` }}
                    >
                      <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-black text-xs px-1 rounded whitespace-nowrap">
                        P{pitStop.stint}
                      </div>
                    </div>
                  );
                })}
            </div>

            {/* Timeline Legend */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span className="text-gray-300">Soft</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span className="text-gray-300">Medium</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-white rounded"></div>
                <span className="text-gray-300">Hard</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                <span className="text-gray-300">Inter</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span className="text-gray-300">Wet</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-1 h-3 bg-yellow-400 rounded"></div>
                <span className="text-gray-300">Pit Stop</span>
              </div>
            </div>

            {/* Total Laps */}
            <div className="text-center text-gray-400 text-xs mt-2">
              Total:{" "}
              {simulation.stints.reduce((sum, s) => sum + s.laps, 0)}{" "}
              laps
            </div>

            {/* Pit Stop Details */}
            {simulation.pitStops &&
              simulation.pitStops.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h4 className="text-sm font-medium text-gray-300">
                    Pit Stop Details:
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {simulation.pitStops.map((pitStop, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-white/5 px-4 py-2 rounded-full text-sm"
                      >
                        <span className="text-gray-300">
                          Lap {pitStop.lap}: {pitStop.oldTire} →{" "}
                          {pitStop.newTire}
                        </span>
                        <span className="text-yellow-400 font-medium">
                          {pitStop.pitTime}s
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </div>
        </CardContent>
      </Card>

      {/* Performance Insights */}
      {simulation.optimization && (
        <Card className="bg-transparent border-0 shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
              <TrendingUp className="h-5 w-5 text-green-500" />
              <span>Performance Insights</span>
            </CardTitle>
            <CardDescription className="text-gray-400">
              Advanced analytics and optimization metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">
                    Pace Consistency
                  </span>
                  <span className="text-green-400 font-medium">
                    {(simulation.optimization.consistency * 100).toFixed(1)}
                    %
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">
                    Baseline Time
                  </span>
                  <span className="text-blue-400 font-medium">
                    {Math.floor(simulation.optimization.baseline_time / 60)}
                    :
                    {(simulation.optimization.baseline_time % 60)
                      .toFixed(0)
                      .padStart(2, "0")}
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Overall Risk</span>
                  <span
                    className={`font-medium ${
                      simulation.risk.overall_risk < 0.2
                        ? "text-green-400"
                        : simulation.risk.overall_risk < 0.4
                          ? "text-yellow-400"
                          : "text-red-400"
                    }`}
                  >
                    {simulation.risk.overall_risk < 0.2
                      ? "Low"
                      : simulation.risk.overall_risk < 0.4
                        ? "Medium"
                        : "High"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Pit Stop Risk</span>
                  <span className="text-blue-400 font-medium">
                    {(simulation.risk.pit_stop_risk * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Weather Risk</span>
                  <span className="text-yellow-400 font-medium">
                    {(simulation.risk.weather_risk * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SimulationResults;
