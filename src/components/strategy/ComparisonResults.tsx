import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { GitCompare, Target } from "lucide-react";

interface ComparisonResultsProps {
  comparisonResults: any;
  selectedDriver: string;
  getTireColor: (tire: string) => string;
}

const ComparisonResults = ({
  comparisonResults,
  selectedDriver,
  getTireColor,
}: ComparisonResultsProps) => {
  return (
    <div className="space-y-6">
      {/* Strategy Comparison Results */}
      <Card className="bg-transparent border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
            <GitCompare className="h-5 w-5 text-purple-500" />
            <span>Strategy Comparison Results</span>
          </CardTitle>
          <CardDescription className="text-gray-400">
            Comparing {comparisonResults.strategies_compared}{" "}
            strategies for {selectedDriver}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Strategies Ranked by Performance */}
            {Object.entries(comparisonResults.results)
              .sort(
                ([, a]: any, [, b]: any) =>
                  a.predicted_position - b.predicted_position,
              )
              .map(([strategy, result]: any, index) => {
                const isWinner = index === 0;
                return (
                  <div
                    key={strategy}
                    className={`p-4 rounded-[24px] border ${
                      isWinner
                        ? "bg-gradient-to-r from-purple-500/20 to-transparent border-t border-l border-purple-500/50"
                        : "bg-white/5 border-white/5"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            isWinner
                              ? "bg-purple-500 text-white"
                              : "bg-white/10 text-white"
                          }`}
                        >
                          {index + 1}
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">
                            {strategy}
                          </h3>
                          {isWinner && (
                            <span className="text-xs text-green-400">
                              Recommended
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-white">
                          P{result.predicted_position}
                        </div>
                        <div className="text-sm text-gray-400">
                          {result.total_race_time}
                        </div>
                      </div>
                    </div>

                    {/* Strategy Details */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">
                          Efficiency:
                        </span>
                        <span className="text-white ml-2">
                          {Math.round(result.efficiency_score)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">
                          Confidence:
                        </span>
                        <span className="text-white ml-2">
                          {Math.round(result.confidence * 100)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">
                          Pit Stops:
                        </span>
                        <span className="text-white ml-2">
                          {result.pit_stops?.length || 0}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">
                          Total Time:
                        </span>
                        <span className="text-white ml-2">
                          {result.total_seconds}s
                        </span>
                      </div>
                    </div>

                    {/* Stint Breakdown */}
                    {result.stints && (
                      <div className="mt-3">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-xs text-gray-400">
                            Stint Breakdown:
                          </span>
                        </div>
                        <div className="flex space-x-1">
                          {result.stints.map((stint, stintIndex) => (
                            <div
                              key={stintIndex}
                              className="flex flex-col items-center"
                            >
                              <div
                                className={`w-4 h-6 rounded-sm ${getTireColor(stint.tire_compound)}`}
                              ></div>
                              <span className="text-xs text-gray-400 mt-1">
                                {stint.laps}L
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Comparison Chart */}
      <Card className="bg-transparent border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
            <Target className="h-5 w-5 text-blue-500" />
            <span>Performance Comparison</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Position Comparison */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">
                Final Position
              </h4>
              <div className="space-y-2">
                {Object.entries(comparisonResults.results).map(
                  ([strategy, result]: any) => (
                    <div
                      key={strategy}
                      className="flex items-center justify-between"
                    >
                      <span className="text-gray-300">
                        {strategy}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-white/10 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{
                              width: `${Math.max(5, (21 - result.predicted_position) * 5)}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-white font-medium w-8">
                          P{result.predicted_position}
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>

            {/* Time Comparison */}
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">
                Race Time
              </h4>
              <div className="space-y-2">
                {Object.entries(comparisonResults.results).map(
                  ([strategy, result]: any) => (
                    <div
                      key={strategy}
                      className="flex items-center justify-between"
                    >
                      <span className="text-gray-300">
                        {strategy}
                      </span>
                      <span className="text-white font-mono">
                        {result.total_race_time}
                      </span>
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ComparisonResults;
