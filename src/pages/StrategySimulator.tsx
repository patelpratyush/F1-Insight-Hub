import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import { DriverSelect } from "@/components/DriverSelect";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import ComparisonResults from "@/components/strategy/ComparisonResults";
import OptimizationResults from "@/components/strategy/OptimizationResults";
import SimulationResults from "@/components/strategy/SimulationResults";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { useDrivers, useTracks } from "@/hooks/useF1Metadata";
import { getCurrentSeasonYear } from "@/lib/season";
import { API_BASE } from "@/lib/api";
import {
    Brain,
    Clock,
    Gauge,
    GitCompare,
    Plus,
    Target,
    Timer,
    TrendingUp,
    X,
    Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

const StrategySimulator = () => {
  const currentSeasonYear = getCurrentSeasonYear();
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
    prioritizeConsistency: true,
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const { data: apiDrivers } = useDrivers(currentSeasonYear);
  const { data: apiTracks } = useTracks(currentSeasonYear);
  const driverList = (apiDrivers || []).map((d) => ({
    id: d.code,
    name: d.name,
    team: d.team,
    number: Number(d.number) || 0,
    teamColor: d.teamColor,
  }));
  const tracks = (apiTracks || []).map((t) => t.race_name);
  const getCircuitByTrackName = (trackName: string) => {
    const track = (apiTracks || []).find((t) => t.race_name === trackName);
    return track ? track.circuit : trackName;
  };

  // Strategy types for dynamic pit stop selection
  const strategyTypes = [
    {
      value: "one_stop",
      label: "1 Stop",
      description: "Single pit stop strategy",
    },
    {
      value: "two_stop",
      label: "2 Stops",
      description: "Two pit stop strategy",
    },
    {
      value: "three_stop",
      label: "3 Stops",
      description: "Three pit stop strategy",
    },
  ];

  // Available tire compounds based on weather conditions
  const getTireCompounds = (weatherCondition) => {
    const dryTires = [
      { value: "Soft", label: "Soft", color: "bg-red-500" },
      { value: "Medium", label: "Medium", color: "bg-yellow-500" },
      { value: "Hard", label: "Hard", color: "bg-white" },
    ];

    const wetTires = [
      { value: "Intermediate", label: "Intermediate", color: "bg-green-500" },
      { value: "Wet", label: "Full Wet", color: "bg-blue-500" },
    ];

    switch (weatherCondition) {
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

  // Map display tire names to backend compound codes
  const COMPOUND_CODE: Record<string, string> = {
    Soft: "SOFT",
    Medium: "MEDIUM",
    Hard: "HARD",
    Intermediate: "INTER",
    Wet: "WET",
  };
  const toCompoundCode = (name: string) => COMPOUND_CODE[name] || name.toUpperCase();

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
    switch (type) {
      case "one_stop":
        return 2; // Start tire + 1 pit stop
      case "two_stop":
        return 3; // Start tire + 2 pit stops
      case "three_stop":
        return 4; // Start tire + 3 pit stops
      default:
        return 0;
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
        "Medium-Hard",
      ];
    } else if (weather === "heavy_rain") {
      // Wet weather strategies
      strategies = [
        "Wet-Intermediate",
        "Intermediate-Wet",
        "Wet-Wet-Intermediate",
        "Intermediate-Intermediate",
        "Wet-Intermediate-Intermediate",
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
        "Soft-Intermediate",
      ];
    }

    return strategies;
  };

  const weatherOptions = [
    {
      value: "clear",
      label: "Clear",
      description: "Normal dry race, fastest pace",
      color: "bg-yellow-500",
    },
    {
      value: "overcast",
      label: "Overcast",
      description: "Cooler track, moderate grip",
      color: "bg-gray-400",
    },
    {
      value: "light_rain",
      label: "Light Rain",
      description: "Intermediate tires, variable grip",
      color: "bg-blue-400",
    },
    {
      value: "heavy_rain",
      label: "Heavy Rain",
      description: "Full wets, slow pace, higher risk",
      color: "bg-blue-600",
    },
    {
      value: "mixed",
      label: "Mixed Conditions",
      description: "Switching between dry and wet",
      color: "bg-purple-500",
    },
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
      const selectedDriverData = driverList.find(
        (d) => d.id === selectedDriver,
      );

      const response = await fetch(
        `${API_BASE}/api/strategy/simulate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            driver: selectedDriver,
            track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
            weather: weather,
            starting_tire: toCompoundCode(selectedTires[0]),
            stint_compounds: selectedTires.map(toCompoundCode),
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Simulation failed");
      }

      // Transform API response to match UI expectations
      const transformedSimulation = {
        strategy_id: data.strategy_id,
        totalTime: data.total_race_time,
        total_seconds: data.total_seconds,
        position: data.predicted_position,
        efficiency: Math.round(data.efficiency_score),
        confidence: Math.round(data.confidence * 100),
        stints: data.stints.map((stint) => ({
          stint: stint.stint_number,
          tire: stint.tire_compound,
          laps: stint.laps,
          avgLapTime: stint.avg_lap_time,
          degradation: stint.degradation_level,
          startLap: stint.start_lap,
          endLap: stint.end_lap,
        })),
        pitStops: data.pit_stops.map((stop) => ({
          lap: stop.lap,
          stint: stop.stint_number,
          oldTire: stop.old_tire,
          newTire: stop.new_tire,
          pitTime: stop.pit_time.toFixed(1),
          reason: stop.reason,
        })),
        timeline: data.timeline,
        optimization: data.optimization_metrics,
        risk: data.risk_analysis,
      };

      setSimulation(transformedSimulation);
    } catch (err) {
      console.error("Strategy simulation error:", err);
      setError(
        err.message || "Failed to simulate race strategy. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompareStrategies = async () => {
    if (
      !selectedDriver ||
      !selectedTrack ||
      !weather ||
      selectedStrategies.length < 2
    ) {
      setError(
        "Please select driver, track, weather, and at least 2 strategies to compare",
      );
      return;
    }

    setIsComparing(true);
    setError("");
    setComparisonResults(null);

    try {
      const selectedDriverData = driverList.find(
        (d) => d.id === selectedDriver,
      );

      const response = await fetch(
        `${API_BASE}/api/strategy/compare`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            driver: selectedDriver,
            track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
            weather: weather,
            strategies: selectedStrategies.map((s) =>
              s.split("-").map(toCompoundCode),
            ),
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Comparison failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Strategy comparison failed");
      }

      setComparisonResults(data);
    } catch (err) {
      console.error("Strategy comparison error:", err);
      setError(
        err.message || "Failed to compare strategies. Please try again.",
      );
    } finally {
      setIsComparing(false);
    }
  };

  const handleOptimizeStrategy = async () => {
    if (!selectedDriver || !selectedTrack || !weather) {
      setError(
        "Please select driver, track, and weather conditions for optimization",
      );
      return;
    }

    setIsOptimizing(true);
    setError("");
    setOptimizationResults(null);

    try {
      const selectedDriverData = driverList.find(
        (d) => d.id === selectedDriver,
      );

      const response = await fetch(
        `${API_BASE}/api/strategy/optimize`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            driver: selectedDriver,
            track: getCircuitByTrackName(selectedTrack), // Convert track name to circuit name for API
            weather: weather,
            use_ai: true,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Optimization failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Strategy optimization failed");
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
          risk_assessment: data.risk_assessment || null,
        },
        alternative_strategies: data.alternative_strategies || [],
        insights: data.insights || [
          `Optimal strategy found: ${data.optimal_strategy || "strategy analysis"}`,
          `Expected finishing position: P${data.predicted_position || "?"}`,
          `Strategy efficiency: ${Math.round(data.efficiency_score || 70)}%`,
          `Risk assessment: ${data.confidence ? `${Math.round(data.confidence * 100)}% confidence` : "Analyzing risk factors"}`,
        ],
        weather_advice: data.weather_advice || null,
        optimization_target: optimizationParams.target,
        ai_powered: isGeminiPowered,
        confidence_score: data.confidence_score || data.confidence || 0.7,
        success: true,
      };

      setOptimizationResults(transformedResults);
    } catch (err) {
      console.error("Strategy optimization error:", err);
      setError(err.message || "Failed to optimize strategy. Please try again.");
    } finally {
      setIsOptimizing(false);
    }
  };

  const addStrategy = (strategy) => {
    if (
      !selectedStrategies.includes(strategy) &&
      selectedStrategies.length < 5
    ) {
      setSelectedStrategies([...selectedStrategies, strategy]);
    }
  };

  const removeStrategy = (strategy) => {
    setSelectedStrategies(selectedStrategies.filter((s) => s !== strategy));
  };

  const getTireColor = (tire) => {
    switch (tire) {
      case "Soft":
        return "bg-red-500";
      case "Medium":
        return "bg-yellow-500";
      case "Hard":
        return "bg-white";
      case "Intermediate":
        return "bg-green-500";
      case "Wet":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32 overflow-hidden selection:bg-red-600/30 font-sans">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-purple-600/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-blue-900/5 rounded-full blur-[150px]"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-7xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className="flex flex-col mb-12 gap-6 relative z-10">
              <span className="text-purple-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                RACE OPTIMIZATION
              </span>
              <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
                STRATEGY
                <br />
                SIMULATOR
              </h1>
              <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
                Simulate pitstop plans, optimize tire allocations, and generate
                race winning strategies using AI analysis.
              </p>
            </div>
          </div>
        </AnimatedPageWrapper>

        {/* Mode Switching Tabs */}
        <AnimatedPageWrapper delay={400}>
          <div className="mb-8">
            <div className="flex space-x-2 bg-white/5 p-2 rounded-[32px] w-fit">
              <button
                onClick={() => setActiveMode("simulate")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "simulate"
                    ? "bg-white text-black font-bold shadow-lg"
                    : "text-white/50 hover:text-white"
                } rounded-full px-6 py-3 transition-all duration-300 flex items-center space-x-2`}
              >
                <Zap className="h-4 w-4" />
                <span>Single Strategy</span>
              </button>
              <button
                onClick={() => setActiveMode("compare")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "compare"
                    ? "bg-white text-black font-bold shadow-lg"
                    : "text-white/50 hover:text-white"
                } rounded-full px-6 py-3 transition-all duration-300 flex items-center space-x-2`}
              >
                <GitCompare className="h-4 w-4" />
                <span>Compare Strategies</span>
              </button>
              <button
                onClick={() => setActiveMode("optimize")}
                className={`px-6 py-3 rounded-md transition-all duration-200 flex items-center space-x-2 ${
                  activeMode === "optimize"
                    ? "bg-white text-black font-bold shadow-lg"
                    : "text-white/50 hover:text-white"
                } rounded-full px-6 py-3 transition-all duration-300 flex items-center space-x-2`}
              >
                <Brain className="h-4 w-4" />
                <span>AI Optimize</span>
              </button>
            </div>
          </div>
        </AnimatedPageWrapper>

        <div className="flex flex-col gap-12">
          {/* Strategy Configuration */}
          <AnimatedPageWrapper delay={600} className="w-full space-y-6">
            <Card className="bg-transparent border-0 shadow-none">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4 text-white">
                  <Target className="h-5 w-5 text-purple-500" />
                  <span>Strategy Setup</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Configure race parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 items-end">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Driver
                  </label>
                  <Select
                    value={selectedDriver}
                    onValueChange={setSelectedDriver}
                  >
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                      <SelectValue placeholder="Select driver">
                        {selectedDriver && (
                          <span>
                            {driverList.find((d) => d.id === selectedDriver)
                              ?.name || selectedDriver}
                          </span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {driverList.map((driver) => (
                        <SelectItem
                          key={driver.id}
                          value={driver.id}
                          className="text-white hover:bg-white/10 cursor-pointer"
                        >
                          <div className="flex flex-col">
                            <span className="font-medium">{driver.name}</span>
                            <span className="text-xs text-gray-400">
                              #{driver.number} - {driver.team}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Track
                  </label>
                  <Select
                    value={selectedTrack}
                    onValueChange={setSelectedTrack}
                  >
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                      <SelectValue placeholder="Select track" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {tracks.map((track) => (
                        <SelectItem
                          key={track}
                          value={track}
                          className="text-white hover:bg-white/10 cursor-pointer"
                        >
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
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Strategy Type
                      </label>
                      <Select
                        value={strategyType}
                        onValueChange={setStrategyType}
                      >
                        <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                          <SelectValue placeholder="Select pit stop strategy" />
                        </SelectTrigger>
                        <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                          {strategyTypes.map((type) => (
                            <SelectItem
                              key={type.value}
                              value={type.value}
                              className="text-white hover:bg-white/10 cursor-pointer"
                            >
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
                          Tire Compounds ({selectedTires.length}/
                          {getRequiredTireSelections(strategyType)})
                        </label>
                        <div className="space-y-2">
                          {Array.from(
                            { length: getRequiredTireSelections(strategyType) },
                            (_, index) => (
                              <div
                                key={index}
                                className="flex items-center space-x-2"
                              >
                                <span className="text-xs text-gray-400 w-16">
                                  {index === 0 ? "Start:" : `Pit ${index}:`}
                                </span>
                                <Select
                                  value={selectedTires[index] || ""}
                                  onValueChange={(value) => {
                                    const newTires = [...selectedTires];
                                    newTires[index] = value;
                                    setSelectedTires(newTires);
                                  }}
                                >
                                  <SelectTrigger className="bg-white/5 border-white/10 text-white flex-1 rounded-[20px] h-14 px-5 text-lg font-bold">
                                    <SelectValue placeholder="Select tire compound">
                                      {selectedTires[index] && (
                                        <div className="flex items-center space-x-2">
                                          <div
                                            className={`w-3 h-3 rounded-full ${getTireCompounds(weather).find((t) => t.value === selectedTires[index])?.color}`}
                                          ></div>
                                          <span>{selectedTires[index]}</span>
                                        </div>
                                      )}
                                    </SelectValue>
                                  </SelectTrigger>
                                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                                    {getTireCompounds(weather).map((tire) => (
                                      <SelectItem
                                        key={tire.value}
                                        value={tire.value}
                                        className="text-white hover:bg-white/10 cursor-pointer"
                                      >
                                        <div className="flex items-center space-x-2">
                                          <div
                                            className={`w-3 h-3 rounded-full ${tire.color}`}
                                          ></div>
                                          <span>{tire.label}</span>
                                        </div>
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                            ),
                          )}
                        </div>

                        {/* Generated Strategy Preview */}
                        {tireStrategy && (
                          <div className="mt-3 p-4 bg-white/5 rounded-[24px]">
                            <div className="text-xs text-gray-400 mb-1">
                              Generated Strategy:
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-white font-medium">
                                {tireStrategy}
                              </span>
                              <div className="flex space-x-1 ml-2">
                                {selectedTires.map((tire, idx) => (
                                  <div
                                    key={idx}
                                    className={`w-4 h-4 rounded-full ${getTireColor(tire)}`}
                                    title={tire}
                                  ></div>
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
                      <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                        <SelectValue placeholder="Add strategy to compare" />
                      </SelectTrigger>
                      <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                        {getComparisonStrategies()
                          .filter((s) => !selectedStrategies.includes(s))
                          .map((strategy) => (
                            <SelectItem
                              key={strategy}
                              value={strategy}
                              className="text-white hover:bg-white/10 cursor-pointer"
                            >
                              {strategy}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>

                    {/* Selected Strategies */}
                    <div className="mt-3 space-y-2">
                      {selectedStrategies.map((strategy, index) => (
                        <div
                          key={strategy}
                          className="flex items-center justify-between bg-white/5 px-4 py-2 rounded-full"
                        >
                          <span className="text-sm text-white">
                            {index + 1}. {strategy}
                          </span>
                          <Button
                            onClick={() => removeStrategy(strategy)}
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-gray-400 hover:text-red-400"
                            aria-label={`Remove strategy ${strategy}`}
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
                      Let AI find the optimal strategy based on your preferences
                      and race conditions.
                    </div>

                    {/* Optimization Target */}
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Optimization Target
                      </label>
                      <Select
                        value={optimizationParams.target}
                        onValueChange={(value) =>
                          setOptimizationParams((prev) => ({
                            ...prev,
                            target: value,
                          }))
                        }
                      >
                        <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                          <SelectValue placeholder="Select optimization target">
                            {optimizationParams.target && (
                              <span>
                                {optimizationParams.target === "position" &&
                                  "Best Position"}
                                {optimizationParams.target === "time" &&
                                  "Fastest Time"}
                                {optimizationParams.target === "points" &&
                                  "Most Points"}
                              </span>
                            )}
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                          <SelectItem
                            value="position"
                            className="text-white hover:bg-white/10 cursor-pointer"
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">Best Position</span>
                              <span className="text-xs text-gray-400">
                                Optimize for highest finishing position
                              </span>
                            </div>
                          </SelectItem>
                          <SelectItem
                            value="time"
                            className="text-white hover:bg-white/10 cursor-pointer"
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">Fastest Time</span>
                              <span className="text-xs text-gray-400">
                                Optimize for lowest total race time
                              </span>
                            </div>
                          </SelectItem>
                          <SelectItem
                            value="points"
                            className="text-white hover:bg-white/10 cursor-pointer"
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">Most Points</span>
                              <span className="text-xs text-gray-400">
                                Optimize for maximum championship points
                              </span>
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
                          onValueChange={(value) =>
                            setOptimizationParams((prev) => ({
                              ...prev,
                              riskTolerance: value[0],
                            }))
                          }
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
                        <span className="text-sm font-medium text-gray-300">
                          Prioritize Consistency
                        </span>
                        <div className="text-xs text-gray-400">
                          Focus on reliable results over risky gains
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setOptimizationParams((prev) => ({
                            ...prev,
                            prioritizeConsistency: !prev.prioritizeConsistency,
                          }))
                        }
                        className={`${
                          optimizationParams.prioritizeConsistency
                            ? "bg-purple-600 border-purple-600 text-white"
                            : "bg-white/5 border-white/5 text-gray-300 hover:text-white"
                        }`}
                      >
                        {optimizationParams.prioritizeConsistency
                          ? "On"
                          : "Off"}
                      </Button>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Weather
                  </label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-purple-500/50">
                      <SelectValue placeholder="Select weather">
                        {weather &&
                          weatherOptions.find((w) => w.value === weather) && (
                            <div className="flex items-center space-x-2">
                              <div
                                className={`w-2 h-2 rounded-full ${weatherOptions.find((w) => w.value === weather)?.color} flex-shrink-0`}
                              ></div>
                              <span>
                                {
                                  weatherOptions.find(
                                    (w) => w.value === weather,
                                  )?.label
                                }
                              </span>
                            </div>
                          )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 min-w-[280px] max-h-[300px] z-[999] rounded-[24px]">
                      {weatherOptions.map((option) => (
                        <SelectItem
                          key={option.value}
                          value={option.value}
                          className="text-white hover:bg-white/10 py-3 cursor-pointer"
                        >
                          <div className="flex items-center space-x-2">
                            <div
                              className={`w-2 h-2 rounded-full ${option.color} flex-shrink-0`}
                            ></div>
                            <div className="flex flex-col">
                              <span className="font-medium">
                                {option.label}
                              </span>
                              <span className="text-xs text-gray-400">
                                {option.description}
                              </span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">
                    Safety Car Probability
                  </label>
                  <div className="px-2">
                    <Slider
                      value={safetyCarProbability}
                      onValueChange={setSafetyCarProbability}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                  </div>
                  <div className="text-center text-sm text-gray-400">
                    {safetyCarProbability[0]}%
                  </div>
                </div>

                {/* Action Button - Different for each mode */}
                {activeMode === "simulate" ? (
                  <Button
                    onClick={handleSimulate}
                    disabled={
                      !selectedDriver ||
                      !selectedTrack ||
                      !strategyType ||
                      !tireStrategy ||
                      !weather ||
                      isLoading ||
                      selectedTires.length !==
                        getRequiredTireSelections(strategyType)
                    }
                    className="w-full bg-white hover:bg-purple-600 text-black hover:text-white rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02] disabled:opacity-50 md:col-span-2 lg:col-span-3 xl:col-span-4"
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
                    disabled={
                      !selectedDriver ||
                      !selectedTrack ||
                      !weather ||
                      selectedStrategies.length < 2 ||
                      isComparing
                    }
                    className="w-full bg-white hover:bg-purple-600 text-black hover:text-white rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02] disabled:opacity-50 md:col-span-2 lg:col-span-3 xl:col-span-4"
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
                    disabled={
                      !selectedDriver ||
                      !selectedTrack ||
                      !weather ||
                      !optimizationParams.target ||
                      isOptimizing
                    }
                    className="w-full bg-white hover:bg-purple-600 text-black hover:text-white rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02] disabled:opacity-50 md:col-span-2 lg:col-span-3 xl:col-span-4"
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
          <AnimatedPageWrapper
            delay={800}
            className="w-full border-t border-white/10 pt-12"
          >
            {activeMode === "simulate" && simulation ? (
              <SimulationResults simulation={simulation} getTireColor={getTireColor} />
            ) : activeMode === "compare" && comparisonResults ? (
              <ComparisonResults comparisonResults={comparisonResults} selectedDriver={selectedDriver} getTireColor={getTireColor} />
            ) : activeMode === "optimize" && optimizationResults ? (
              <OptimizationResults optimizationResults={optimizationResults} />
            ) : (
              <Card className="bg-transparent border-0 h-96 flex items-center justify-center pt-12">
                <CardContent className="text-center">
                  <div className="space-y-4">
                    {activeMode === "simulate" ? (
                      <>
                        <Zap className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">
                          No Simulation Run
                        </CardTitle>
                        <CardDescription className="text-gray-500">
                          Configure your strategy parameters and run a
                          simulation to see predicted outcomes.
                        </CardDescription>
                      </>
                    ) : activeMode === "compare" ? (
                      <>
                        <GitCompare className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">
                          No Comparison Run
                        </CardTitle>
                        <CardDescription className="text-gray-500">
                          Select at least 2 strategies to compare and see which
                          performs better.
                        </CardDescription>
                      </>
                    ) : (
                      <>
                        <Brain className="h-16 w-16 text-gray-600 mx-auto" />
                        <CardTitle className="text-gray-400">
                          No Optimization Run
                        </CardTitle>
                        <CardDescription className="text-gray-500">
                          Configure your optimization parameters and let AI find
                          the optimal strategy.
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
