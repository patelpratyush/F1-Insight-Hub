import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Brain } from "lucide-react";

interface OptimizationResultsProps {
  optimizationResults: any;
}

const OptimizationResults = ({ optimizationResults }: OptimizationResultsProps) => {
  return (
    <div className="space-y-6">
      {/* Optimization Results */}
      <Card className="bg-transparent border-0 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
            <Brain className="h-5 w-5 text-purple-500" />
            <span>
              {optimizationResults.ai_powered
                ? "Gemini AI Strategy Optimization"
                : "Strategy Optimization Results"}
            </span>
            {optimizationResults.ai_powered && (
              <Badge
                variant="outline"
                className="text-purple-400 border-purple-400 text-xs"
              >
                AI Powered
              </Badge>
            )}
          </CardTitle>
          <CardDescription className="text-gray-400">
            {optimizationResults.ai_powered
              ? "Intelligent strategy recommendations powered by Google Gemini AI"
              : "Strategy recommendations based on simulation analysis"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Recommended Strategy */}
            <div className="p-4 bg-gradient-to-r from-purple-900/20 to-purple-800/20 rounded-lg border border-purple-500/30">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    Recommended Strategy
                  </h3>
                  <p className="text-sm text-purple-300">
                    {optimizationResults.recommended_strategy
                      ?.strategy || "Analyzing optimal strategy..."}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-400">
                    P
                    {optimizationResults.recommended_strategy
                      ?.predicted_position || "?"}
                  </div>
                  <div className="text-sm text-gray-400">
                    {optimizationResults.recommended_strategy
                      ?.total_race_time || "Calculating..."}
                  </div>
                </div>
              </div>

              {/* Strategy Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Efficiency:</span>
                  <span className="text-white ml-2 font-medium">
                    {Math.round(
                      optimizationResults.recommended_strategy
                        ?.efficiency_score || 0,
                    )}
                    %
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Confidence:</span>
                  <span className="text-white ml-2 font-medium">
                    {Math.round(
                      (optimizationResults.recommended_strategy
                        ?.confidence || 0) * 100,
                    )}
                    %
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Risk Score:</span>
                  <span className="text-white ml-2 font-medium">
                    {Math.round(
                      (optimizationResults.recommended_strategy
                        ?.risk_score || 0) * 100,
                    )}
                    %
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Consistency:</span>
                  <span className="text-white ml-2 font-medium">
                    {Math.round(
                      (optimizationResults.recommended_strategy
                        ?.consistency_score || 0) * 100,
                    )}
                    %
                  </span>
                </div>
              </div>
            </div>

            {/* AI Reasoning (if available) */}
            {optimizationResults.ai_powered &&
              optimizationResults.recommended_strategy
                ?.ai_reasoning && (
                <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                  <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
                    <Brain className="h-4 w-4 text-blue-400" />
                    <span>AI Strategic Analysis</span>
                  </h4>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {
                      optimizationResults.recommended_strategy
                        .ai_reasoning
                    }
                  </p>
                  {optimizationResults.recommended_strategy
                    .risk_assessment && (
                    <div className="mt-3 text-xs text-blue-300">
                      <strong>Risk Assessment:</strong>{" "}
                      {
                        optimizationResults.recommended_strategy
                          .risk_assessment
                      }
                    </div>
                  )}
                </div>
              )}

            {/* Weather-Specific Advice (if available) */}
            {optimizationResults.weather_advice && (
              <div className="p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
                  <span>🌤️</span>
                  <span>Weather-Specific Advice</span>
                </h4>
                <p className="text-gray-300 text-sm">
                  {optimizationResults.weather_advice}
                </p>
              </div>
            )}

            {/* Alternative Strategies */}
            {optimizationResults.alternative_strategies &&
              optimizationResults.alternative_strategies.length >
                0 && (
                <div>
                  <h4 className="text-white font-medium mb-3">
                    Alternative Strategies
                  </h4>
                  <div className="space-y-3">
                    {optimizationResults.alternative_strategies
                      .slice(0, 3)
                      .map((strategy, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-4 bg-white/5 rounded-[24px]"
                        >
                          <div>
                            <span className="text-white font-medium">
                              {strategy.strategy}
                            </span>
                            <div className="text-xs text-gray-400 mt-1">
                              Efficiency:{" "}
                              {Math.round(strategy.efficiency_score)}%
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-white font-medium">
                              P{strategy.predicted_position}
                            </div>
                            <div className="text-xs text-gray-400">
                              {strategy.total_race_time}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Optimization Insights */}
            {optimizationResults.insights && (
              <div>
                <h4 className="text-white font-medium mb-3">
                  AI Insights
                </h4>
                <div className="space-y-2">
                  {optimizationResults.insights.map(
                    (insight, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-2 text-sm"
                      >
                        <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-gray-300">
                          {insight}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OptimizationResults;
