import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import DataWrapper from "@/components/ui/data-wrapper";
import ErrorDisplay from "@/components/ui/error-display";
import LoadingSpinner from "@/components/ui/loading-spinner";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { trackOptions } from "@/data/tracks2025";
import useApiCall from "@/hooks/useApiCall";
import { motion } from "framer-motion";
import {
    Flag,
    Loader2,
    Timer,
    TrendingUp,
    Trophy,
    Users,
    Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

const RacePredictor = () => {
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [inputError, setInputError] = useState("");

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const tracks = trackOptions;

  const weatherConditions = [
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

  const raceApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/predict/race`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          race_name: selectedTrack,
          weather: weather,
          temperature:
            weather === "clear" ? 25.0 : weather === "overcast" ? 20.0 : 18.0,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}: Failed to generate race predictions`,
        );
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Race prediction failed");
      }

      const transformedPredictions = data.predictions.map((pred: any) => ({
        pos: pred.predicted_position,
        driver: pred.driver_code,
        name: pred.driver_name,
        team: pred.team
          .replace(" Honda RBPT", "")
          .replace(" Mercedes", "")
          .replace("Scuderia ", "")
          .replace("BWT ", "")
          .replace(" Aramco Mercedes", "")
          .replace("Visa Cash App RB F1 Team", "RB")
          .replace("MoneyGram Haas F1 Team", "Haas")
          .replace("Kick Sauber F1 Team", "Kick Sauber"),
        confidence: Math.round(pred.confidence),
        gap: pred.gap_to_winner,
      }));

      return {
        predictions: transformedPredictions,
        statistics: data.statistics,
        modelType: data.model_type,
        ensemblePerformance: data.ensemble_performance,
        gridAnalysis: data.grid_analysis,
        strategyInsights: data.strategy_insights,
        weatherAnalysis: data.weather_analysis,
        championshipImpact: data.championship_impact,
        success: data.success,
        raceName: data.race_name,
        weatherConditions: data.weather_conditions,
        temperature: data.temperature,
      };
    },
    { maxRetries: 2, retryDelay: 2000 },
  );

  const handlePredict = () => {
    if (!selectedTrack || !weather) {
      setInputError("Please select both track and weather conditions");
      return;
    }
    setInputError("");
    raceApi.execute();
  };

  const getPositionColor = (pos: number) => {
    if (pos === 1) return "text-yellow-500";
    if (pos === 2) return "text-gray-300";
    if (pos === 3) return "text-amber-600";
    if (pos <= 10) return "text-green-500";
    return "text-white/30";
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32 overflow-hidden selection:bg-red-600/30 font-sans">
      {/* Background Graphic Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 mix-blend-screen">
        <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-red-600/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-red-900/5 rounded-full blur-[150px]"></div>
      </div>

      <div className="max-w-screen-2xl mx-auto relative z-10 pt-8">
        {/* Header - Flowing Typography */}
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col mb-16 gap-6">
            <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              GRID SIMULATOR ENGINE
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
              RACE
              <br />
              PREDICTOR
            </h1>
            <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
              Simulate final positions for the entire 2025 grid based on
              qualifying results, historical team performance, and dynamic race
              conditions via continuous machine learning.
            </p>
          </div>
        </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Input Parameters - Left Column */}
          <AnimatedPageWrapper
            delay={600}
            className="lg:col-span-4 flex flex-col pt-2 lg:pt-0"
          >
            <div className="mb-8">
              <h2 className="text-3xl font-black tracking-tighter">
                PARAMETERS
              </h2>
              <p className="text-white/50 font-light mt-1">
                Configure full grid simulation.
              </p>
            </div>

            <div className="p-8 flex flex-col gap-6 relative group border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent shadow-2xl rounded-[40px] overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/10 blur-[40px] rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-700"></div>

              <div>
                <label className="text-white/40 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Flag className="w-4 h-4 text-red-500" /> Circuit Selection
                </label>
                <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                    <SelectValue placeholder="Select circuit" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                    {tracks.map((track) => (
                      <SelectItem
                        key={track.name}
                        value={track.name}
                        className="text-white hover:bg-white/10 py-3 cursor-pointer"
                      >
                        {track.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-white/40 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-red-500" /> Track Conditions
                </label>
                <Select value={weather} onValueChange={setWeather}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-[20px] h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                    <SelectValue placeholder="Select weather">
                      {weather &&
                        weatherConditions.find((w) => w.value === weather) && (
                          <div className="flex items-center space-x-3">
                            <div
                              className={`w-3 h-3 rounded-full shadow-[0_0_10px_currentColor] ${weatherConditions.find((w) => w.value === weather)?.color}`}
                            ></div>
                            <span>
                              {
                                weatherConditions.find(
                                  (w) => w.value === weather,
                                )?.label
                              }
                            </span>
                          </div>
                        )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px] max-h-[300px]">
                    {weatherConditions.map((condition) => (
                      <SelectItem
                        key={condition.value}
                        value={condition.value}
                        className="text-white hover:bg-white/10 py-3 cursor-pointer"
                      >
                        <div className="flex items-center space-x-3">
                          <div
                            className={`w-3 h-3 rounded-full ${condition.color} shadow-[0_0_10px_currentColor]`}
                          ></div>
                          <div className="flex flex-col">
                            <span className="font-bold">{condition.label}</span>
                            <span className="text-xs text-white/50">
                              {condition.description}
                            </span>
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {inputError && (
                <div className="px-4 py-3 bg-red-500/10 border border-red-500/50 rounded-xl">
                  <p className="text-red-400 text-sm font-bold">{inputError}</p>
                </div>
              )}

              <Button
                onClick={handlePredict}
                disabled={!selectedTrack || !weather || raceApi.loading}
                className="w-full bg-white text-black hover:bg-red-600 hover:text-white mt-4 h-16 rounded-full text-lg font-black tracking-widest transition-all duration-300 disabled:bg-white/10 disabled:text-white/30"
              >
                {raceApi.loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin" /> SIMULATING
                    GRID...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Zap className="h-5 w-5" /> GENERATE RESULTS
                  </span>
                )}
              </Button>
            </div>
          </AnimatedPageWrapper>

          {/* Results Output - Right Column */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-8">
            <DataWrapper
              loading={raceApi.loading}
              error={raceApi.error}
              data={raceApi.data}
              onRetry={raceApi.retry}
              isRetrying={raceApi.isRetrying}
              loadingMessage=""
              errorVariant="inline"
              minHeight="min-h-full"
              fallbackContent={
                <div className="h-full min-h-[500px] flex flex-col items-center justify-center p-12 bg-transparent text-center border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px]">
                  <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center mb-6">
                    <Flag className="h-10 w-10 text-white/20" />
                  </div>
                  <h3 className="text-2xl font-black text-white/80 mb-2">
                    AWAITING SIMULATION
                  </h3>
                  <p className="text-white/40 max-w-sm">
                    Select a track and weather to simulate race outcomes for all
                    20 drivers.
                  </p>
                </div>
              }
            >
              {raceApi.data?.predictions && (
                <div className="flex flex-col gap-12">
                  <div>
                    <h2 className="text-3xl font-black tracking-tighter">
                      SIMULATED RACE STANDINGS
                    </h2>
                    <p className="text-white/50 font-light mt-1 text-red-400">
                      Simulation completed for {selectedTrack}.
                    </p>
                  </div>

                  {/* Free flowing grid layout for positions */}
                  <StaggeredAnimation
                    delay={300}
                    staggerDelay={50}
                    className="flex flex-col gap-2"
                  >
                    {raceApi.data.predictions.map((driver: any) => (
                      <div
                        key={driver.driver}
                        className="flex items-center px-6 py-4 relative group hover:bg-white/[0.02] rounded-[24px] transition-all duration-300"
                      >
                        {driver.pos === 1 && (
                          <div className="absolute inset-0 bg-yellow-500/5 rounded-[24px] z-0"></div>
                        )}

                        <div className="flex items-center gap-8 w-full z-10 relative">
                          <div
                            className={`text-4xl font-black italic tracking-tighter w-16 opacity-80 ${getPositionColor(driver.pos)}`}
                          >
                            {driver.pos}
                          </div>

                          <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div className="flex items-baseline gap-3">
                              <span className="font-bold text-white text-2xl tracking-tight">
                                {driver.driver}
                              </span>
                              <span className="text-white/50 font-light text-xl hidden sm:block">
                                {driver.name}
                              </span>
                              <Badge
                                variant="outline"
                                className="text-white/40 border-white/10 bg-transparent text-[10px] hidden md:flex uppercase tracking-widest ml-2"
                              >
                                {driver.team}
                              </Badge>
                            </div>

                            <div className="flex items-center gap-8 justify-between w-full sm:w-auto">
                              <div className="flex flex-col items-start sm:items-end w-24">
                                <span className="text-white/30 text-[10px] uppercase tracking-widest font-bold">
                                  Gap Leader
                                </span>
                                <span className="text-white/80 font-mono font-medium">
                                  {driver.gap === "0.000"
                                    ? "LEADER"
                                    : `+${driver.gap}`}
                                </span>
                              </div>
                              <div className="bg-red-500/10 text-red-500 border border-red-500/20 px-3 py-1 rounded-full text-xs font-bold w-16 text-center">
                                {driver.confidence}%
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </StaggeredAnimation>

                  {/* Analysis Grids */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Track Context Widget */}
                    <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] flex flex-col justify-between group hover:border-white/10 transition-colors">
                      <div className="flex items-center justify-between mb-8">
                        <Users className="h-8 w-8 text-white/20" />
                        <span className="text-white/30 text-[10px] uppercase font-bold tracking-widest">
                          Model Telemetry
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-6">
                        <div className="flex flex-col">
                          <span className="text-[40px] font-black leading-none mb-1">
                            20
                          </span>
                          <span className="text-white/40 text-[10px] uppercase tracking-widest font-bold">
                            Grid Count
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[40px] font-black leading-none mb-1 text-red-400">
                            {raceApi.data?.statistics?.average_confidence || 87}
                            %
                          </span>
                          <span className="text-white/40 text-[10px] uppercase tracking-widest font-bold">
                            Avg Confidence
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-lg font-bold leading-none mb-2 mt-4 text-white/80">
                            {raceApi.data.modelType || "GBM"}
                          </span>
                          <span className="text-white/40 text-[10px] uppercase tracking-widest font-bold">
                            Architecture
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Dynamics Context Widget */}
                    <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] flex flex-col group hover:border-white/10 transition-colors">
                      <h4 className="text-white/30 font-bold text-[10px] uppercase tracking-widest mb-6 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-red-500" /> Dynamic
                        Insights
                      </h4>

                      <div className="flex flex-col gap-5">
                        <div className="flex justify-between items-center border-b border-white/5 pb-4">
                          <span className="text-white/60 text-sm">
                            Overtaking Difficulty
                          </span>
                          <span className="font-bold">
                            {raceApi.data?.strategyInsights
                              ?.overtaking_difficulty || "Medium"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/5 pb-4">
                          <span className="text-white/60 text-sm">
                            Pit Window
                          </span>
                          <span className="font-bold">
                            {raceApi.data?.strategyInsights
                              ?.pit_window_importance || "High"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/5 pb-4">
                          <span className="text-white/60 text-sm">
                            Safety Car Probability
                          </span>
                          <span className="font-bold text-red-400">
                            {raceApi.data?.strategyInsights
                              ?.safety_car_probability || "High Risk"}
                          </span>
                        </div>
                        <div className="flex justify-between items-center pb-2">
                          <span className="text-white/60 text-sm">
                            Weather Effect
                          </span>
                          <span className="font-bold">
                            {raceApi.data?.weatherAnalysis?.impact_on_grid ||
                              "Minimal"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Array of Specialists */}
                    {(raceApi.data?.weatherAnalysis?.wet_weather_specialists ||
                      raceApi.data?.gridAnalysis?.pole_contenders) && (
                      <div className="md:col-span-2 p-8 bg-black rounded-[40px] flex flex-col relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 to-transparent"></div>
                        <h4 className="text-white/30 font-bold text-[10px] uppercase tracking-widest mb-6 flex items-center gap-2">
                          <Trophy className="h-4 w-4 text-red-500" /> Advanced
                          Driver Impacts
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          {raceApi.data?.gridAnalysis?.pole_contenders && (
                            <div className="flex flex-col">
                              <span className="text-white/80 font-bold mb-3 text-sm">
                                Podium Contenders
                              </span>
                              <div className="flex flex-wrap gap-2">
                                {raceApi.data.gridAnalysis.pole_contenders.map(
                                  (d: string) => (
                                    <span
                                      key={d}
                                      className="bg-white/5 px-3 py-1.5 rounded-full text-xs font-bold text-white/80"
                                    >
                                      {d}
                                    </span>
                                  ),
                                )}
                              </div>
                            </div>
                          )}

                          {raceApi.data?.weatherAnalysis
                            ?.wet_weather_specialists &&
                            raceApi.data.weatherAnalysis.wet_weather_specialists
                              .length > 0 && (
                              <div className="flex flex-col">
                                <span className="text-white/80 font-bold mb-3 text-sm">
                                  Condition Specialists
                                </span>
                                <div className="flex flex-wrap gap-2">
                                  {raceApi.data.weatherAnalysis.wet_weather_specialists.map(
                                    (d: string) => (
                                      <span
                                        key={d}
                                        className="bg-red-500/10 text-red-400 px-3 py-1.5 rounded-full text-xs font-bold"
                                      >
                                        {d}
                                      </span>
                                    ),
                                  )}
                                </div>
                              </div>
                            )}

                          {raceApi.data?.gridAnalysis?.midfield_battle && (
                            <div className="flex flex-col md:col-span-2 mt-4">
                              <span className="text-white/80 font-bold mb-3 text-sm">
                                Midfield Aggressors
                              </span>
                              <div className="flex flex-wrap gap-2">
                                {raceApi.data.gridAnalysis.midfield_battle
                                  .slice(0, 6)
                                  .map((d: string) => (
                                    <span
                                      key={d}
                                      className="text-white/50 text-xs font-bold border border-white/10 px-3 py-1.5 rounded-full"
                                    >
                                      {d}
                                    </span>
                                  ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </DataWrapper>
          </AnimatedPageWrapper>
        </div>
      </div>
    </div>
  );
};

export default RacePredictor;
