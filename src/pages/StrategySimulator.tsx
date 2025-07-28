
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Zap, Clock, Gauge, Target, Timer, TrendingUp } from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { drivers2025 } from "@/data/drivers2025";
import { DriverSelect } from "@/components/DriverSelect";

const StrategySimulator = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [tireStrategy, setTireStrategy] = useState("");
  const [safetyCarProbability, setSafetyCarProbability] = useState([30]);
  const [weather, setWeather] = useState("");
  const [simulation, setSimulation] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsVisible(true);
  }, []);
  
  const tracks = ["Monaco", "Silverstone", "Monza", "Spa-Francorchamps", "Suzuka"];
  const strategies = [
    "Soft-Medium-Hard",
    "Medium-Hard-Hard", 
    "Soft-Soft-Medium",
    "Medium-Medium-Hard",
    "Hard-Hard-Medium"
  ];
  
  const weatherOptions = [
    { value: "dry", label: "Dry" },
    { value: "light_rain", label: "Light Rain" },
    { value: "wet", label: "Wet" },
    { value: "mixed", label: "Mixed" }
  ];

  const handleSimulate = async () => {
    if (!selectedDriver || !selectedTrack || !tireStrategy || !weather) {
      setError("Please fill in all required fields");
      return;
    }

    setIsLoading(true);
    setError("");
    setSimulation(null);

    try {
      const selectedDriverData = drivers2025.find(d => d.id === selectedDriver);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/strategy/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver: selectedDriver,
          track: selectedTrack,
          weather: weather,
          tire_strategy: tireStrategy,
          safety_car_probability: safetyCarProbability[0],
          qualifying_position: 10, // Default starting position
          team: selectedDriverData?.team || "Red Bull Racing",
          temperature: 25.0
        }),
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Simulation failed');
      }

      // Transform API response to match UI expectations
      const transformedSimulation = {
        strategy_id: data.strategy_id,
        totalTime: data.total_race_time,
        total_seconds: data.total_seconds,
        position: data.predicted_position,
        efficiency: Math.round(data.efficiency_score),
        confidence: Math.round(data.confidence * 100),
        stints: data.stints.map(stint => ({
          stint: stint.stint_number,
          tire: stint.tire_compound,
          laps: stint.laps,
          avgLapTime: stint.avg_lap_time,
          degradation: stint.degradation_level,
          startLap: stint.start_lap,
          endLap: stint.end_lap
        })),
        pitStops: data.pit_stops.map(stop => ({
          lap: stop.lap,
          stint: stop.stint_number,
          oldTire: stop.old_tire,
          newTire: stop.new_tire,
          pitTime: stop.pit_time.toFixed(1),
          reason: stop.reason
        })),
        timeline: data.timeline,
        optimization: data.optimization_metrics,
        risk: data.risk_analysis
      };

      setSimulation(transformedSimulation);
    } catch (err) {
      console.error('Strategy simulation error:', err);
      setError(err.message || 'Failed to simulate race strategy. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getTireColor = (tire) => {
    switch(tire) {
      case "Soft": return "bg-red-500";
      case "Medium": return "bg-yellow-500"; 
      case "Hard": return "bg-white";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-yellow-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-7xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className={`flex items-center space-x-3 mb-4 transition-all duration-1000 delay-300 transform ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
            }`}>
              <div className="p-3 bg-purple-600 rounded-lg shadow-lg hover:shadow-purple-500/25 transition-all duration-300 hover:scale-110">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">Race Strategy Simulator</h1>
            </div>
            <div className={`transition-all duration-1000 delay-500 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
            }`}>
              <p className="text-gray-400 text-lg">
                Simulate different pit stop strategies and compare outcomes using advanced race modeling algorithms.
              </p>
              <div className="mt-2 text-sm text-gray-500">
                ⚡ Strategy optimization • 🏁 Pit stop timing • 🛞 Tire degradation modeling
              </div>
            </div>
          </div>
        </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Strategy Configuration */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-1 space-y-6">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Target className="h-5 w-5 text-purple-500" />
                  <span>Strategy Setup</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Configure race parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Driver</label>
                  <DriverSelect 
                    value={selectedDriver} 
                    onValueChange={setSelectedDriver}
                    placeholder="Select driver"
                    dark={true}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Track</label>
                  <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select track" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {tracks.map((track) => (
                        <SelectItem key={track} value={track} className="text-white hover:bg-gray-600">
                          {track}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Tire Strategy</label>
                  <Select value={tireStrategy} onValueChange={setTireStrategy}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select strategy" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {strategies.map((strategy) => (
                        <SelectItem key={strategy} value={strategy} className="text-white hover:bg-gray-600">
                          {strategy}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weather</label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select weather" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {weatherOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="text-white hover:bg-gray-600">
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">Safety Car Probability</label>
                  <div className="px-2">
                    <Slider
                      value={safetyCarProbability}
                      onValueChange={setSafetyCarProbability}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                  </div>
                  <div className="text-center text-sm text-gray-400">{safetyCarProbability[0]}%</div>
                </div>

                <Button 
                  onClick={handleSimulate}
                  disabled={!selectedDriver || !selectedTrack || !tireStrategy || !weather || isLoading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white mt-6 disabled:opacity-50"
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent" />
                      Simulating...
                    </>
                  ) : (
                    <>
                      <Zap className="mr-2 h-4 w-4" />
                      Run Simulation
                    </>
                  )}
                </Button>
                
                {error && (
                  <div className="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Simulation Results */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-3">
            {simulation ? (
              <div className="space-y-6">
                {/* Overview Stats */}
                <StaggeredAnimation
                  delay={300}
                  staggerDelay={150}
                  className="grid grid-cols-1 md:grid-cols-4 gap-4"
                >
                  {[
                  <Card key="time" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Clock className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-blue-400">{simulation.totalTime}</div>
                      <div className="text-sm text-gray-300">Total Race Time</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="position" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Target className="h-6 w-6 text-green-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-green-400">P{simulation.position}</div>
                      <div className="text-sm text-gray-300">Predicted Position</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="efficiency" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <TrendingUp className="h-6 w-6 text-purple-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-purple-400">{simulation.efficiency}%</div>
                      <div className="text-sm text-gray-300">Strategy Efficiency</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="confidence" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Gauge className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-yellow-400">{simulation.confidence}%</div>
                      <div className="text-sm text-gray-300">Confidence</div>
                    </CardContent>
                  </Card>
                  ]}
                </StaggeredAnimation>

                {/* Stint Breakdown */}
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
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
                        <div key={index} className="flex items-center p-4 bg-gray-700/30 rounded-lg">
                          <div className="flex items-center space-x-4 flex-1">
                            <div className="text-center">
                              <div className="text-sm text-gray-400">Stint</div>
                              <div className="text-lg font-bold text-white">{stint.stint}</div>
                            </div>
                            
                            <div className={`w-4 h-4 rounded-full ${getTireColor(stint.tire)}`}></div>
                            <div>
                              <div className="font-medium text-white">{stint.tire} Compound</div>
                              <div className="text-sm text-gray-400">{stint.laps} laps (L{stint.startLap}-L{stint.endLap})</div>
                            </div>
                          </div>
                          
                          <div className="text-right space-y-1">
                            <div className="text-white font-medium">{stint.avgLapTime}</div>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${
                                stint.degradation === 'High' ? 'text-red-400 border-red-400' :
                                stint.degradation === 'Medium' ? 'text-yellow-400 border-yellow-400' :
                                'text-green-400 border-green-400'
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
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white">Strategy Timeline</CardTitle>
                    <CardDescription className="text-gray-400">
                      Visual representation of pit stops and tire changes throughout the race
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
                      <div className="relative h-12 bg-gray-700/30 rounded-lg overflow-hidden">
                        {simulation.stints.map((stint, index) => {
                          const totalLaps = simulation.stints.reduce((sum, s) => sum + s.laps, 0);
                          const width = (stint.laps / totalLaps) * 100;
                          const left = simulation.stints.slice(0, index).reduce((sum, s) => sum + s.laps, 0) / totalLaps * 100;
                          
                          return (
                            <div
                              key={index}
                              className={`absolute top-0 h-full flex items-center justify-center text-white text-xs font-medium border-r border-gray-600 ${getTireColor(stint.tire)} ${getTireColor(stint.tire).replace('bg-', 'bg-opacity-80 bg-')}`}
                              style={{ left: `${left}%`, width: `${width}%` }}
                            >
                              <div className="text-center">
                                <div className="font-bold">{stint.tire.charAt(0)}</div>
                                <div className="text-xs">{stint.laps}L</div>
                              </div>
                            </div>
                          );
                        })}
                        
                        {/* Pit Stop Markers */}
                        {simulation.pitStops && simulation.pitStops.map((pitStop, index) => {
                          const totalLaps = simulation.stints.reduce((sum, s) => sum + s.laps, 0);
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
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
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
                          <div className="w-1 h-3 bg-yellow-400 rounded"></div>
                          <span className="text-gray-300">Pit Stop</span>
                        </div>
                        <div className="text-gray-400">
                          Total: {simulation.stints.reduce((sum, s) => sum + s.laps, 0)} laps
                        </div>
                      </div>
                      
                      {/* Pit Stop Details */}
                      {simulation.pitStops && simulation.pitStops.length > 0 && (
                        <div className="mt-4 space-y-2">
                          <h4 className="text-sm font-medium text-gray-300">Pit Stop Details:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {simulation.pitStops.map((pitStop, index) => (
                              <div key={index} className="flex items-center justify-between bg-gray-700/50 p-2 rounded text-sm">
                                <span className="text-gray-300">
                                  Lap {pitStop.lap}: {pitStop.oldTire} → {pitStop.newTire}
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
                  <Card className="bg-gray-800/50 border-gray-700">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center space-x-2">
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
                            <span className="text-gray-300">Time Consistency</span>
                            <span className="text-green-400 font-medium">
                              {(simulation.optimization.time_consistency * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-300">Position Stability</span>
                            <span className="text-blue-400 font-medium">
                              {(simulation.optimization.position_stability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-300">Podium Probability</span>
                            <span className="text-yellow-400 font-medium">
                              {(simulation.optimization.podium_probability * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-300">Best Case Time</span>
                            <span className="text-green-400 font-medium">
                              {Math.floor(simulation.optimization.best_case_time / 60)}:{(simulation.optimization.best_case_time % 60).toFixed(0).padStart(2, '0')}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-300">Median Position</span>
                            <span className="text-blue-400 font-medium">
                              P{Math.round(simulation.optimization.median_position)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-300">Strategy Risk</span>
                            <span className={`font-medium ${
                              simulation.risk.strategy_robustness > 0.8 ? 'text-green-400' :
                              simulation.risk.strategy_robustness > 0.6 ? 'text-yellow-400' : 'text-red-400'
                            }`}>
                              {simulation.risk.strategy_robustness > 0.8 ? 'Low' :
                               simulation.risk.strategy_robustness > 0.6 ? 'Medium' : 'High'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <Zap className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">No Simulation Run</CardTitle>
                  <CardDescription className="text-gray-500">
                    Configure your strategy parameters and run a simulation to see predicted outcomes.
                  </CardDescription>
                </CardContent>
              </Card>
            )}
          </AnimatedPageWrapper>
        </div>
      </div>
    </div>
  );
};

export default StrategySimulator;
