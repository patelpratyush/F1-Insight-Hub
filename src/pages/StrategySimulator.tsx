
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Zap, Clock, Gauge, Target, Timer, TrendingUp, GitCompare, Plus, X, Brain } from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { drivers2025 } from "@/data/drivers2025";
import { DriverSelect } from "@/components/DriverSelect";
import { getCircuitByTrackName, trackNames } from "@/data/tracks2025";

const StrategySimulator = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [strategyType, setStrategyType] = useState(""); // "one_stop", "two_stop", "three_stop"
  const [selectedTires, setSelectedTires] = useState([]); // Array of tire compounds
  const [tireStrategy, setTireStrategy] = useState(""); // Generated strategy string
  const [safetyCarProbability, setSafetyCarProbability] = useState([30]);
  const [weather, setWeather] = useState("");
  const [simulation, setSimulation] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Strategy comparison state
  const [activeMode, setActiveMode] = useState("simulate"); // "simulate", "compare", or "optimize"
  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  
  // Strategy optimization state
  const [optimizationResults, setOptimizationResults] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationParams, setOptimizationParams] = useState({
    target: "position", // "position", "time", or "points"
    riskTolerance: 50, // 0-100 scale
    prioritizeConsistency: true
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);
  
  // Use centralized track data - all 2025 F1 tracks  
  const tracks = trackNames;
  
  // Strategy types for dynamic pit stop selection
  const strategyTypes = [
    { value: "one_stop", label: "1 Stop", description: "Single pit stop strategy" },
    { value: "two_stop", label: "2 Stops", description: "Two pit stop strategy" },
    { value: "three_stop", label: "3 Stops", description: "Three pit stop strategy" }
  ];
  
  // Available tire compounds based on weather conditions
  const getTireCompounds = (weatherCondition) => {
    const dryTires = [
      { value: "Soft", label: "Soft", color: "bg-red-500" },
      { value: "Medium", label: "Medium", color: "bg-yellow-500" },
      { value: "Hard", label: "Hard", color: "bg-white" }
    ];
    
    const wetTires = [
      { value: "Intermediate", label: "Intermediate", color: "bg-green-500" },
      { value: "Wet", label: "Full Wet", color: "bg-blue-500" }
    ];
    
    switch(weatherCondition) {
      case "clear":
      case "overcast":
        return dryTires;
      case "light_rain":
      case "mixed":
        return [...dryTires, ...wetTires];
      case "heavy_rain":
        return wetTires;
      default:
        return [...dryTires, ...wetTires];
    }
  };
  
  // Generate tire strategy string from selected compounds
  const generateTireStrategy = () => {
    if (selectedTires.length === 0) return "";
    return selectedTires.join("-");
  };
  
  // Update tire strategy when tire selection changes
  useEffect(() => {
    setTireStrategy(generateTireStrategy());
  }, [selectedTires]);
  
  // Get number of required tire selections based on strategy type
  const getRequiredTireSelections = (type) => {
    switch(type) {
      case "one_stop": return 2; // Start tire + 1 pit stop
      case "two_stop": return 3; // Start tire + 2 pit stops
      case "three_stop": return 4; // Start tire + 3 pit stops
      default: return 0;
    }
  };
  
  // Reset tire selection when strategy type or weather changes
  useEffect(() => {
    setSelectedTires([]);
    setTireStrategy("");
  }, [strategyType, weather]);
  
  // Pre-built strategies for comparison mode
  const getComparisonStrategies = () => {
    const compounds = getTireCompounds(weather);
    const dryTires = ["Soft", "Medium", "Hard"];
    const wetTires = ["Intermediate", "Wet"];
    
    let strategies = [];
    
    if (weather === "clear" || weather === "overcast") {
      // Dry weather strategies
      strategies = [
        "Soft-Medium-Hard",
        "Medium-Hard-Hard", 
        "Soft-Soft-Medium",
        "Medium-Medium-Hard",
        "Hard-Hard-Medium",
        "Soft-Hard",
        "Medium-Hard"
      ];
    } else if (weather === "heavy_rain") {
      // Wet weather strategies
      strategies = [
        "Wet-Intermediate",
        "Intermediate-Wet",
        "Wet-Wet-Intermediate",
        "Intermediate-Intermediate",
        "Wet-Intermediate-Intermediate"
      ];
    } else {
      // Mixed conditions strategies
      strategies = [
        "Soft-Medium-Intermediate",
        "Intermediate-Medium-Hard",
        "Medium-Intermediate-Hard",
        "Intermediate-Soft-Medium",
        "Wet-Intermediate-Medium",
        "Intermediate-Wet-Medium",
        "Medium-Intermediate",
        "Soft-Intermediate"
      ];
    }
    
    return strategies;
  };
  
  const weatherOptions = [
    { value: "clear", label: "Clear", description: "Normal dry race, fastest pace", color: "bg-yellow-500" },
    { value: "overcast", label: "Overcast", description: "Cooler track, moderate grip", color: "bg-gray-400" },
    { value: "light_rain", label: "Light Rain", description: "Intermediate tires, variable grip", color: "bg-blue-400" },
    { value: "heavy_rain", label: "Heavy Rain", description: "Full wets, slow pace, higher risk", color: "bg-blue-600" },
    { value: "mixed", label: "Mixed Conditions", description: "Switching between dry and wet", color: "bg-purple-500" }
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
          track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
          weather: weather,
          tire_strategy: tireStrategy,
          safety_car_probability: safetyCarProbability[0],
          qualifying_position: 10, // Default starting position
          team: selectedDriverData?.team || "Red Bull Racing",
          temperature: weather === 'clear' ? 25.0 : weather === 'overcast' ? 20.0 : 18.0
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

  const handleCompareStrategies = async () => {
    if (!selectedDriver || !selectedTrack || !weather || selectedStrategies.length < 2) {
      setError("Please select driver, track, weather, and at least 2 strategies to compare");
      return;
    }

    setIsComparing(true);
    setError("");
    setComparisonResults(null);

    try {
      const selectedDriverData = drivers2025.find(d => d.id === selectedDriver);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/strategy/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver: selectedDriver,
          track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
          weather: weather,
          strategies: selectedStrategies,
          safety_car_probability: safetyCarProbability[0],
          qualifying_position: 10 // Default starting position
        }),
      });

      if (!response.ok) {
        throw new Error(`Comparison failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Strategy comparison failed');
      }

      setComparisonResults(data);
    } catch (err) {
      console.error('Strategy comparison error:', err);
      setError(err.message || 'Failed to compare strategies. Please try again.');
    } finally {
      setIsComparing(false);
    }
  };

  const handleOptimizeStrategy = async () => {
    if (!selectedDriver || !selectedTrack || !weather) {
      setError("Please select driver, track, and weather conditions for optimization");
      return;
    }

    setIsOptimizing(true);
    setError("");
    setOptimizationResults(null);

    try {
      const selectedDriverData = drivers2025.find(d => d.id === selectedDriver);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/strategy/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver: selectedDriver,
          track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
          weather: weather,
          safety_car_probability: safetyCarProbability[0],
          qualifying_position: 10, // Default starting position
          target_metric: optimizationParams.target,
          risk_tolerance: optimizationParams.riskTolerance / 100, // Convert to 0-1 scale
          prioritize_consistency: optimizationParams.prioritizeConsistency,
          team: selectedDriverData?.team || "Red Bull Racing",
          temperature: weather === 'clear' ? 25.0 : weather === 'overcast' ? 20.0 : 18.0
        }),
      });

      if (!response.ok) {
        throw new Error(`Optimization failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Strategy optimization failed');
      }

      // Transform the optimization results to match UI expectations
      // Check if this is Gemini AI response or traditional response
      const isGeminiPowered = data.ai_powered === true;
      
      const transformedResults = {
        recommended_strategy: {
          strategy: data.optimal_strategy || "Unknown Strategy",
          predicted_position: data.predicted_position || 10,
          total_race_time: data.total_race_time || "1:30:00.000",
          efficiency_score: data.efficiency_score || 70,
          confidence: data.confidence || 0.7,
          risk_score: data.risk_analysis?.overall_risk || 0.5,
          consistency_score: data.optimization_metrics?.consistency || 0.8,
          ai_reasoning: data.ai_reasoning || null,
          risk_assessment: data.risk_assessment || null
        },
        alternative_strategies: data.alternative_strategies || [],
        insights: data.insights || [
          `Optimal strategy found: ${data.optimal_strategy || "strategy analysis"}`,
          `Expected finishing position: P${data.predicted_position || "?"}`,
          `Strategy efficiency: ${Math.round((data.efficiency_score || 70))}%`,
          `Risk assessment: ${data.confidence ? `${Math.round(data.confidence * 100)}% confidence` : "Analyzing risk factors"}`
        ],
        weather_advice: data.weather_advice || null,
        optimization_target: optimizationParams.target,
        ai_powered: isGeminiPowered,
        confidence_score: data.confidence_score || data.confidence || 0.7,
        success: true
      };

      console.log('Raw API response:', data);
      console.log('Available fields:', Object.keys(data));
      console.log('Transformed results:', transformedResults);
      
      setOptimizationResults(transformedResults);
    } catch (err) {
      console.error('Strategy optimization error:', err);
      setError(err.message || 'Failed to optimize strategy. Please try again.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const addStrategy = (strategy) => {
    if (!selectedStrategies.includes(strategy) && selectedStrategies.length < 5) {
      setSelectedStrategies([...selectedStrategies, strategy]);
    }
  };

  const removeStrategy = (strategy) => {
    setSelectedStrategies(selectedStrategies.filter(s => s !== strategy));
  };

  const getTireColor = (tire) => {
    switch(tire) {
      case "Soft": return "bg-red-500";
      case "Medium": return "bg-yellow-500"; 
      case "Hard": return "bg-white";
      case "Intermediate": return "bg-green-500";
      case "Wet": return "bg-blue-500";
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

        {/* Mode Switching Tabs */}
        <AnimatedPageWrapper delay={400}>
          <div className="mb-8">
            <div className="flex space-x-1 bg-gray-800/50 p-1 rounded-lg border border-gray-700 w-fit">
              <button
                onClick={() => setActiveMode("simulate")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "simulate"
                    ? "bg-purple-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                }`}
              >
                <Zap className="h-4 w-4" />
                <span>Single Strategy</span>
              </button>
              <button
                onClick={() => setActiveMode("compare")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "compare"
                    ? "bg-purple-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                }`}
              >
                <GitCompare className="h-4 w-4" />
                <span>Compare Strategies</span>
              </button>
              <button
                onClick={() => setActiveMode("optimize")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "optimize"
                    ? "bg-purple-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                }`}
              >
                <Brain className="h-4 w-4" />
                <span>AI Optimize</span>
              </button>
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
                  <Select value={selectedDriver} onValueChange={setSelectedDriver}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select driver">
                        {selectedDriver && (
                          <span>
                            {drivers2025.find(d => d.id === selectedDriver)?.name || selectedDriver}
                          </span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {drivers2025.map((driver) => (
                        <SelectItem key={driver.id} value={driver.id} className="text-white hover:bg-gray-600">
                          <div className="flex flex-col">
                            <span className="font-medium">{driver.name}</span>
                            <span className="text-xs text-gray-400">#{driver.number} - {driver.team}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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

                {/* Strategy Selection - Different UI for each mode */}
                {activeMode === "simulate" ? (
                  <div className="space-y-4">
                    {/* Strategy Type Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Strategy Type</label>
                      <Select value={strategyType} onValueChange={setStrategyType}>
                        <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                          <SelectValue placeholder="Select pit stop strategy" />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-700 border-gray-600">
                          {strategyTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value} className="text-white hover:bg-gray-600">
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {/* Dynamic Tire Selection */}
                    {strategyType && weather && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Tire Compounds ({selectedTires.length}/{getRequiredTireSelections(strategyType)})
                        </label>
                        <div className="space-y-2">
                          {Array.from({ length: getRequiredTireSelections(strategyType) }, (_, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <span className="text-xs text-gray-400 w-16">
                                {index === 0 ? 'Start:' : `Pit ${index}:`}
                              </span>
                              <Select 
                                value={selectedTires[index] || ""} 
                                onValueChange={(value) => {
                                  const newTires = [...selectedTires];
                                  newTires[index] = value;
                                  setSelectedTires(newTires);
                                }}
                              >
                                <SelectTrigger className="bg-gray-700 border-gray-600 text-white flex-1">
                                  <SelectValue placeholder="Select tire compound">
                                    {selectedTires[index] && (
                                      <div className="flex items-center space-x-2">
                                        <div className={`w-3 h-3 rounded-full ${getTireCompounds(weather).find(t => t.value === selectedTires[index])?.color}`}></div>
                                        <span>{selectedTires[index]}</span>
                                      </div>
                                    )}
                                  </SelectValue>
                                </SelectTrigger>
                                <SelectContent className="bg-gray-700 border-gray-600">
                                  {getTireCompounds(weather).map((tire) => (
                                    <SelectItem key={tire.value} value={tire.value} className="text-white hover:bg-gray-600">
                                      <div className="flex items-center space-x-2">
                                        <div className={`w-3 h-3 rounded-full ${tire.color}`}></div>
                                        <span>{tire.label}</span>
                                      </div>
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          ))}
                        </div>
                        
                        {/* Generated Strategy Preview */}
                        {tireStrategy && (
                          <div className="mt-3 p-3 bg-gray-700/30 rounded-lg">
                            <div className="text-xs text-gray-400 mb-1">Generated Strategy:</div>
                            <div className="flex items-center space-x-2">
                              <span className="text-white font-medium">{tireStrategy}</span>
                              <div className="flex space-x-1 ml-2">
                                {selectedTires.map((tire, idx) => (
                                  <div key={idx} className={`w-4 h-4 rounded-full ${getTireColor(tire)}`} title={tire}></div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : activeMode === "compare" ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Strategies to Compare ({selectedStrategies.length}/5)
                    </label>
                    
                    {/* Strategy Selection */}
                    <Select onValueChange={addStrategy}>
                      <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                        <SelectValue placeholder="Add strategy to compare" />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-700 border-gray-600">
                        {getComparisonStrategies().filter(s => !selectedStrategies.includes(s)).map((strategy) => (
                          <SelectItem key={strategy} value={strategy} className="text-white hover:bg-gray-600">
                            {strategy}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    {/* Selected Strategies */}
                    <div className="mt-3 space-y-2">
                      {selectedStrategies.map((strategy, index) => (
                        <div key={strategy} className="flex items-center justify-between bg-gray-700/50 p-2 rounded-md">
                          <span className="text-sm text-white">{index + 1}. {strategy}</span>
                          <Button
                            onClick={() => removeStrategy(strategy)}
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-gray-400 hover:text-red-400"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  /* Optimization Mode */
                  <div className="space-y-4">
                    <div className="text-sm text-gray-400 mb-4">
                      Let AI find the optimal strategy based on your preferences and race conditions.
                    </div>
                    
                    {/* Optimization Target */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">Optimization Target</label>
                      <Select 
                        value={optimizationParams.target} 
                        onValueChange={(value) => setOptimizationParams(prev => ({ ...prev, target: value }))}
                      >
                        <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                          <SelectValue placeholder="Select optimization target">
                            {optimizationParams.target && (
                              <span>
                                {optimizationParams.target === "position" && "Best Position"}
                                {optimizationParams.target === "time" && "Fastest Time"}
                                {optimizationParams.target === "points" && "Most Points"}
                              </span>
                            )}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent className="bg-gray-700 border-gray-600">
                          <SelectItem value="position" className="text-white hover:bg-gray-600">
                            <div className="flex flex-col">
                              <span className="font-medium">Best Position</span>
                              <span className="text-xs text-gray-400">Optimize for highest finishing position</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="time" className="text-white hover:bg-gray-600">
                            <div className="flex flex-col">
                              <span className="font-medium">Fastest Time</span>
                              <span className="text-xs text-gray-400">Optimize for lowest total race time</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="points" className="text-white hover:bg-gray-600">
                            <div className="flex flex-col">
                              <span className="font-medium">Most Points</span>
                              <span className="text-xs text-gray-400">Optimize for maximum championship points</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    {/* Risk Tolerance */}
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-300">
                        Risk Tolerance ({optimizationParams.riskTolerance}%)
                      </label>
                      <div className="px-2">
                        <Slider
                          value={[optimizationParams.riskTolerance]}
                          onValueChange={(value) => setOptimizationParams(prev => ({ ...prev, riskTolerance: value[0] }))}
                          max={100}
                          step={5}
                          className="w-full"
                        />
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Conservative</span>
                        <span>Aggressive</span>
                      </div>
                    </div>
                    
                    {/* Consistency Toggle */}
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-gray-300">Prioritize Consistency</span>
                        <div className="text-xs text-gray-400">Focus on reliable results over risky gains</div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setOptimizationParams(prev => ({ ...prev, prioritizeConsistency: !prev.prioritizeConsistency }))}
                        className={`${
                          optimizationParams.prioritizeConsistency 
                            ? 'bg-purple-600 border-purple-600 text-white' 
                            : 'bg-gray-700 border-gray-600 text-gray-300'
                        }`}
                      >
                        {optimizationParams.prioritizeConsistency ? 'On' : 'Off'}
                      </Button>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weather</label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select weather">
                        {weather && weatherOptions.find(w => w.value === weather) && (
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${weatherOptions.find(w => w.value === weather)?.color} flex-shrink-0`}></div>
                            <span>{weatherOptions.find(w => w.value === weather)?.label}</span>
                          </div>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600 min-w-[280px] max-h-[300px] z-50">
                      {weatherOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="text-white hover:bg-gray-600 py-3">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${option.color} flex-shrink-0`}></div>
                            <div className="flex flex-col">
                              <span className="font-medium">{option.label}</span>
                              <span className="text-xs text-gray-400">{option.description}</span>
                            </div>
                          </div>
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

                {/* Action Button - Different for each mode */}
                {activeMode === "simulate" ? (
                  <Button 
                    onClick={handleSimulate}
                    disabled={!selectedDriver || !selectedTrack || !strategyType || !tireStrategy || !weather || isLoading || selectedTires.length !== getRequiredTireSelections(strategyType)}
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
                ) : activeMode === "compare" ? (
                  <Button 
                    onClick={handleCompareStrategies}
                    disabled={!selectedDriver || !selectedTrack || !weather || selectedStrategies.length < 2 || isComparing}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white mt-6 disabled:opacity-50"
                    size="lg"
                  >
                    {isComparing ? (
                      <>
                        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent" />
                        Comparing...
                      </>
                    ) : (
                      <>
                        <GitCompare className="mr-2 h-4 w-4" />
                        Compare Strategies
                      </>
                    )}
                  </Button>
                ) : (
                  <Button 
                    onClick={handleOptimizeStrategy}
                    disabled={!selectedDriver || !selectedTrack || !weather || !optimizationParams.target || isOptimizing}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white mt-6 disabled:opacity-50"
                    size="lg"
                  >
                    {isOptimizing ? (
                      <>
                        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-r-transparent" />
                        Optimizing...
                      </>
                    ) : (
                      <>
                        <Brain className="mr-2 h-4 w-4" />
                        Find Optimal Strategy
                      </>
                    )}
                  </Button>
                )}
                
                {error && (
                  <div className="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Results Section */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-3">
            {activeMode === "simulate" && simulation ? (
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
                        Total: {simulation.stints.reduce((sum, s) => sum + s.laps, 0)} laps
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
            ) : activeMode === "compare" && comparisonResults ? (
              <div className="space-y-6">
                {/* Strategy Comparison Results */}
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <GitCompare className="h-5 w-5 text-purple-500" />
                      <span>Strategy Comparison Results</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Comparing {comparisonResults.strategies_compared} strategies for {selectedDriver}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Strategies Ranked by Performance */}
                      {Object.entries(comparisonResults.results)
                        .sort(([,a], [,b]) => a.predicted_position - b.predicted_position)
                        .map(([strategy, result], index) => {
                          const isWinner = index === 0;
                          return (
                            <div key={strategy} className={`p-4 rounded-lg border ${
                              isWinner 
                                ? 'bg-green-900/20 border-green-500/50' 
                                : 'bg-gray-700/30 border-gray-600'
                            }`}>
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center space-x-3">
                                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                    isWinner ? 'bg-green-500 text-black' : 'bg-gray-600 text-white'
                                  }`}>
                                    {index + 1}
                                  </div>
                                  <div>
                                    <h3 className="font-semibold text-white">{strategy}</h3>
                                    {isWinner && <span className="text-xs text-green-400">Recommended</span>}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-lg font-bold text-white">P{result.predicted_position}</div>
                                  <div className="text-sm text-gray-400">{result.total_race_time}</div>
                                </div>
                              </div>
                              
                              {/* Strategy Details */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-400">Efficiency:</span>
                                  <span className="text-white ml-2">{Math.round(result.efficiency_score)}%</span>
                                </div>
                                <div>
                                  <span className="text-gray-400">Confidence:</span>
                                  <span className="text-white ml-2">{Math.round(result.confidence * 100)}%</span>
                                </div>
                                <div>
                                  <span className="text-gray-400">Pit Stops:</span>
                                  <span className="text-white ml-2">{result.pit_stops?.length || 0}</span>
                                </div>
                                <div>
                                  <span className="text-gray-400">Total Time:</span>
                                  <span className="text-white ml-2">{result.total_seconds}s</span>
                                </div>
                              </div>
                              
                              {/* Stint Breakdown */}
                              {result.stints && (
                                <div className="mt-3">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <span className="text-xs text-gray-400">Stint Breakdown:</span>
                                  </div>
                                  <div className="flex space-x-1">
                                    {result.stints.map((stint, stintIndex) => (
                                      <div key={stintIndex} className="flex flex-col items-center">
                                        <div className={`w-4 h-6 rounded-sm ${getTireColor(stint.tire_compound)}`}></div>
                                        <span className="text-xs text-gray-400 mt-1">{stint.laps}L</span>
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
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <Target className="h-5 w-5 text-blue-500" />
                      <span>Performance Comparison</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Position Comparison */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Final Position</h4>
                        <div className="space-y-2">
                          {Object.entries(comparisonResults.results).map(([strategy, result], index) => (
                            <div key={strategy} className="flex items-center justify-between">
                              <span className="text-gray-300">{strategy}</span>
                              <div className="flex items-center space-x-2">
                                <div className="w-24 bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-purple-500 h-2 rounded-full"
                                    style={{ width: `${Math.max(5, (21 - result.predicted_position) * 5)}%` }}
                                  ></div>
                                </div>
                                <span className="text-white font-medium w-8">P{result.predicted_position}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Time Comparison */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-300 mb-2">Race Time</h4>
                        <div className="space-y-2">
                          {Object.entries(comparisonResults.results).map(([strategy, result], index) => (
                            <div key={strategy} className="flex items-center justify-between">
                              <span className="text-gray-300">{strategy}</span>
                              <span className="text-white font-mono">{result.total_race_time}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : activeMode === "optimize" && optimizationResults ? (
              <div className="space-y-6">
                {/* Optimization Results */}
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <Brain className="h-5 w-5 text-purple-500" />
                      <span>{optimizationResults.ai_powered ? 'Gemini AI Strategy Optimization' : 'Strategy Optimization Results'}</span>
                      {optimizationResults.ai_powered && (
                        <Badge variant="outline" className="text-purple-400 border-purple-400 text-xs">
                          AI Powered
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      {optimizationResults.ai_powered 
                        ? 'Intelligent strategy recommendations powered by Google Gemini AI'
                        : 'Strategy recommendations based on simulation analysis'
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* Recommended Strategy */}
                      <div className="p-4 bg-gradient-to-r from-purple-900/20 to-purple-800/20 rounded-lg border border-purple-500/30">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h3 className="text-lg font-bold text-white">Recommended Strategy</h3>
                            <p className="text-sm text-purple-300">
                              {optimizationResults.recommended_strategy?.strategy || "Analyzing optimal strategy..."}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-purple-400">
                              P{optimizationResults.recommended_strategy?.predicted_position || "?"}
                            </div>
                            <div className="text-sm text-gray-400">
                              {optimizationResults.recommended_strategy?.total_race_time || "Calculating..."}
                            </div>
                          </div>
                        </div>
                        
                        {/* Strategy Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Efficiency:</span>
                            <span className="text-white ml-2 font-medium">
                              {Math.round(optimizationResults.recommended_strategy?.efficiency_score || 0)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Confidence:</span>
                            <span className="text-white ml-2 font-medium">
                              {Math.round((optimizationResults.recommended_strategy?.confidence || 0) * 100)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Risk Score:</span>
                            <span className="text-white ml-2 font-medium">
                              {Math.round((optimizationResults.recommended_strategy?.risk_score || 0) * 100)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Consistency:</span>
                            <span className="text-white ml-2 font-medium">
                              {Math.round((optimizationResults.recommended_strategy?.consistency_score || 0) * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {/* AI Reasoning (if available) */}
                      {optimizationResults.ai_powered && optimizationResults.recommended_strategy.ai_reasoning && (
                        <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                          <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
                            <Brain className="h-4 w-4 text-blue-400" />
                            <span>AI Strategic Analysis</span>
                          </h4>
                          <p className="text-gray-300 text-sm leading-relaxed">
                            {optimizationResults.recommended_strategy.ai_reasoning}
                          </p>
                          {optimizationResults.recommended_strategy.risk_assessment && (
                            <div className="mt-3 text-xs text-blue-300">
                              <strong>Risk Assessment:</strong> {optimizationResults.recommended_strategy.risk_assessment}
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
                      {optimizationResults.alternative_strategies && optimizationResults.alternative_strategies.length > 0 && (
                        <div>
                          <h4 className="text-white font-medium mb-3">Alternative Strategies</h4>
                          <div className="space-y-3">
                            {optimizationResults.alternative_strategies.slice(0, 3).map((strategy, index) => (
                              <div key={index} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                                <div>
                                  <span className="text-white font-medium">{strategy.strategy}</span>
                                  <div className="text-xs text-gray-400 mt-1">
                                    Efficiency: {Math.round(strategy.efficiency_score)}% • 
                                    Risk: {Math.round(strategy.risk_score * 100)}%
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-white font-medium">P{strategy.predicted_position}</div>
                                  <div className="text-xs text-gray-400">{strategy.total_race_time}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Optimization Insights */}
                      {optimizationResults.insights && (
                        <div>
                          <h4 className="text-white font-medium mb-3">AI Insights</h4>
                          <div className="space-y-2">
                            {optimizationResults.insights.map((insight, index) => (
                              <div key={index} className="flex items-start space-x-2 text-sm">
                                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                                <span className="text-gray-300">{insight}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <div className="space-y-4">
                    {activeMode === "simulate" ? (
                      <>
                        <Zap className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">No Simulation Run</CardTitle>
                        <CardDescription className="text-gray-500">
                          Configure your strategy parameters and run a simulation to see predicted outcomes.
                        </CardDescription>
                      </>
                    ) : activeMode === "compare" ? (
                      <>
                        <GitCompare className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">No Comparison Run</CardTitle>
                        <CardDescription className="text-gray-500">
                          Select at least 2 strategies to compare and see which performs better.
                        </CardDescription>
                      </>
                    ) : (
                      <>
                        <Brain className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">No Optimization Run</CardTitle>
                        <CardDescription className="text-gray-500">
                          Configure your optimization parameters and let AI find the optimal strategy.
                        </CardDescription>
                      </>
                    )}
                  </div>
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
