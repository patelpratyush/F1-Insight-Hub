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
import { drivers2025 } from "@/data/drivers2025";
import { trackNames } from "@/data/tracks2025";
import useApiCall from "@/hooks/useApiCall";
import { motion } from "framer-motion";
import {
    AlertCircle,
    Cloud,
    Target,
    TrendingUp,
    Trophy,
    Users,
    Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

const DriverPredictor = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [inputError, setInputError] = useState("");

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const drivers = drivers2025;
  const tracks = trackNames;

  const predictionApi = useApiCall(
    async () => {
      const selectedDriverData = drivers.find((d) => d.id === selectedDriver);
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

      const response = await fetch(`${apiUrl}/api/predict/driver`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          driver: selectedDriver,
          track: selectedTrack,
          weather: weather.toLowerCase(),
          team: selectedDriverData?.team || "Unknown",
        }),
      });

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}: Failed to generate prediction`,
        );
      }

      const data = await response.json();

      if (!data.success && data.message) {
        throw new Error(data.message);
      }

      const podiumProbability =
        data.predicted_race_position <= 3
          ? Math.min(
              95,
              data.race_confidence * 100 +
                (4 - data.predicted_race_position) * 10,
            )
          : Math.max(5, (21 - data.predicted_race_position) * 3);

      return {
        qualifying: data.predicted_qualifying_position,
        race: data.predicted_race_position,
        podiumProbability: podiumProbability,
        qualifyingConfidence: data.qualifying_confidence,
        raceConfidence: data.race_confidence,
        modelType: data.model_type,
        ensembleBreakdown: data.ensemble_breakdown,
        featureImportance: data.feature_importance,
        uncertaintyRange: data.uncertainty_range,
        modelPerformance: data.model_performance,
        driverRatings: data.driver_ratings,
        carRatings: data.car_ratings,
        weatherImpact: data.weather_impact,
        historicalComparison: data.historical_comparison,
        trackAnalysis: data.track_analysis,
        predictionFactors: data.prediction_factors,
        confidenceExplanation: data.confidence_explanation,
        riskAssessment: data.risk_assessment,
      };
    },
    { maxRetries: 2, retryDelay: 1500 },
  );

  const handlePredict = () => {
    if (!selectedDriver || !selectedTrack || !weather) {
      setInputError("Please select driver, track, and weather conditions");
      return;
    }
    setInputError("");
    predictionApi.execute();
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
              MACHINE LEARNING INFERENCE
            </span>
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md">
              DRIVER
              <br />
              PREDICTOR
            </h1>
            <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
              Gradient Boosting ML model trained on 2024-2025 F1 data. Forecasts
              race results utilizing historic qualifying times, live weather,
              and dynamic track features.
            </p>
          </div>
        </AnimatedPageWrapper>

        <div className="flex flex-col gap-12">
          {/* Input Parameters - Left Column */}
          <AnimatedPageWrapper
            delay={600}
            className="w-full flex flex-col pt-2 lg:pt-0"
          >
            <div className="mb-8">
              <h2 className="text-3xl font-black tracking-tighter">
                PARAMETERS
              </h2>
              <p className="text-white/50 font-light mt-1">
                Configure telemetry variables.
              </p>
            </div>

            <div className="flex flex-col lg:flex-row gap-6 relative group items-start lg:items-end">
              <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/10 blur-[40px] rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none transition-all duration-700"></div>

              <div className="flex-1 w-full">
                <label className="text-white/40 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Users className="w-4 h-4 text-red-500" /> Driver Object
                </label>
                <Select
                  value={selectedDriver}
                  onValueChange={setSelectedDriver}
                >
                  <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                    <SelectValue placeholder="Select a driver">
                      {selectedDriver && (
                        <span>
                          {drivers.find((d) => d.id === selectedDriver)?.name ||
                            selectedDriver}
                        </span>
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                    {drivers.map((driver) => (
                      <SelectItem
                        key={driver.id}
                        value={driver.id}
                        className="text-white hover:bg-white/10 py-3 cursor-pointer"
                      >
                        <div className="flex flex-col">
                          <span className="font-bold">{driver.name}</span>
                          <span className="text-xs text-white/50">
                            #{driver.number} - {driver.team}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex-1 w-full">
                <label className="text-white/40 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4 text-red-500" /> Circuit Data
                </label>
                <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                    <SelectValue placeholder="Select a track" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px] max-h-[300px]">
                    {tracks.map((track) => (
                      <SelectItem
                        key={track}
                        value={track}
                        className="text-white hover:bg-white/10 py-3 cursor-pointer"
                      >
                        {track}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex-1 w-full">
                <label className="text-white/40 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Cloud className="w-4 h-4 text-red-500" /> Weather Condition
                </label>
                <Select value={weather} onValueChange={setWeather}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                    <SelectValue placeholder="Select weather">
                      {weather && (
                        <div className="flex items-center space-x-3">
                          <div
                            className={`w-3 h-3 rounded-full shadow-[0_0_10px_currentColor] ${
                              weather === "clear"
                                ? "bg-yellow-500 text-yellow-500"
                                : weather === "overcast"
                                  ? "bg-gray-400 text-gray-400"
                                  : weather === "light_rain"
                                    ? "bg-blue-400 text-blue-400"
                                    : weather === "heavy_rain"
                                      ? "bg-blue-600 text-blue-600"
                                      : weather === "mixed"
                                        ? "bg-purple-500 text-purple-500"
                                        : "bg-white/50 text-white/50"
                            }`}
                          ></div>
                          <span className="capitalize">
                            {weather.replace("_", " ")}
                          </span>
                        </div>
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                    <SelectItem
                      value="clear"
                      className="text-white hover:bg-white/10 py-3 cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-yellow-500"></span>{" "}
                          Clear
                        </span>
                        <span className="text-xs text-white/50 ml-5">
                          Standard dry race calculation
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem
                      value="overcast"
                      className="text-white hover:bg-white/10 py-3 cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-gray-400"></span>{" "}
                          Overcast
                        </span>
                        <span className="text-xs text-white/50 ml-5">
                          Cool track, extended tire life
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem
                      value="light_rain"
                      className="text-white hover:bg-white/10 py-3 cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-blue-400"></span>{" "}
                          Light Rain
                        </span>
                        <span className="text-xs text-white/50 ml-5">
                          Intermediate conditions inference
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem
                      value="heavy_rain"
                      className="text-white hover:bg-white/10 py-3 cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-blue-600"></span>{" "}
                          Heavy Rain
                        </span>
                        <span className="text-xs text-white/50 ml-5">
                          Full wet variables applied
                        </span>
                      </div>
                    </SelectItem>
                    <SelectItem
                      value="mixed"
                      className="text-white hover:bg-white/10 py-3 cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-purple-500"></span>{" "}
                          Mixed
                        </span>
                        <span className="text-xs text-white/50 ml-5">
                          High risk crossover conditions
                        </span>
                      </div>
                    </SelectItem>
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
                disabled={
                  !selectedDriver ||
                  !selectedTrack ||
                  !weather ||
                  predictionApi.loading
                }
                className="flex-1 w-full lg:w-auto bg-white text-black hover:bg-red-600 hover:text-white h-14 rounded-full text-lg font-black tracking-widest transition-all duration-300 disabled:bg-white/10 disabled:text-white/30"
              >
                {predictionApi.loading ? (
                  <span className="flex items-center gap-2">
                    <Zap className="h-5 w-5 animate-bounce" /> INFERRING...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Zap className="h-5 w-5" /> GENERATE
                  </span>
                )}
              </Button>
            </div>
          </AnimatedPageWrapper>

          {/* Results Output - Right Column */}
          <AnimatedPageWrapper
            delay={800}
            className="w-full border-t border-white/10 pt-12"
          >
            <DataWrapper
              loading={predictionApi.loading}
              error={predictionApi.error}
              data={predictionApi.data}
              onRetry={predictionApi.retry}
              isRetrying={predictionApi.isRetrying}
              loadingMessage=""
              errorVariant="inline"
              minHeight="min-h-full"
              fallbackContent={
                <div className="h-full min-h-[500px] flex flex-col items-center justify-center p-12 bg-transparent">
                  <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center mb-6">
                    <Trophy className="h-10 w-10 text-white/20" />
                  </div>
                  <h3 className="text-2xl font-black text-white/80 mb-2">
                    AWAITING PARAMETERS
                  </h3>
                  <p className="text-white/40 text-center max-w-sm">
                    Select a driver, track, and weather configuration to run the
                    inference model.
                  </p>
                </div>
              }
            >
              {predictionApi.data && (
                <div className="flex flex-col gap-8">
                  <div className="mb-4">
                    <h2 className="text-3xl font-black tracking-tighter">
                      INFERENCE OUTPUT
                    </h2>
                    <p className="text-white/50 font-light mt-1 text-red-400">
                      Model successfully ran for {selectedDriver} at{" "}
                      {selectedTrack}.
                    </p>
                  </div>

                  {/* Top Level Predictions Grid */}
                  <StaggeredAnimation
                    delay={300}
                    staggerDelay={100}
                    className="grid grid-cols-1 md:grid-cols-3 gap-6"
                  >
                    <div className="p-8 flex flex-col items-center justify-center relative group transition-all">
                      <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-all z-0"></div>
                      <span className="text-[80px] font-black leading-none tracking-tighter text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] relative z-10 mb-4 animate-pulse">
                        P{predictionApi.data.qualifying}
                      </span>
                      <div className="flex flex-col items-center text-center relative z-10">
                        <span className="text-white/50 font-bold text-xs uppercase tracking-widest mb-1">
                          Qualifying
                        </span>
                        <span className="text-white/30 text-[10px] bg-white/5 px-2 py-0.5 rounded-full">
                          Confidence:{" "}
                          {predictionApi.data.qualifyingConfidence
                            ? (
                                predictionApi.data.qualifyingConfidence * 100
                              ).toFixed(0)
                            : 75}
                          %
                        </span>
                      </div>
                    </div>

                    <div className="p-8 flex flex-col items-center justify-center relative group hover:text-red-500 transition-all">
                      <div className="absolute rounded-full w-full h-full bg-red-600/10 blur-[40px] group-hover:bg-red-600/20 transition-all z-0"></div>
                      <span className="text-[80px] font-black leading-none tracking-tighter text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] relative z-10 mb-4 animate-pulse">
                        P{predictionApi.data.race}
                      </span>
                      <div className="flex flex-col items-center text-center relative z-10">
                        <span className="text-red-400 font-bold text-xs uppercase tracking-widest mb-1">
                          RACE FINISH
                        </span>
                        <span className="text-red-400/50 text-[10px] bg-red-500/10 border-l-2 border-t border-red-500/20 border-r-0 border-b-0 px-2 py-0.5 rounded-full">
                          Confidence:{" "}
                          {predictionApi.data.raceConfidence
                            ? (predictionApi.data.raceConfidence * 100).toFixed(
                                0,
                              )
                            : 65}
                          %
                        </span>
                      </div>
                    </div>

                    <div className="p-8 flex flex-col items-center justify-center relative group transition-all">
                      <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-all z-0"></div>
                      <span className="text-[80px] font-black leading-none tracking-tighter text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] relative z-10 mb-4">
                        {Math.round(predictionApi.data.podiumProbability)}%
                      </span>
                      <div className="flex flex-col items-center text-center relative z-10">
                        <span className="text-white/50 font-bold text-xs uppercase tracking-widest mb-1">
                          Podium Chance
                        </span>
                        <span className="text-white/30 text-[10px] bg-white/5 px-2 py-0.5 rounded-full">
                          Top 3 Finish Margin
                        </span>
                      </div>
                    </div>
                  </StaggeredAnimation>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Confidence Intervals */}
                    {predictionApi.data.uncertaintyRange && (
                      <div className="p-8 flex flex-col">
                        <h4 className="text-white font-bold text-lg mb-6 flex items-center gap-2">
                          <Target className="h-5 w-5 text-red-500" />
                          Uncertainty Variance
                        </h4>

                        <div className="flex flex-col gap-6">
                          <div className="flex flex-col gap-3">
                            <div className="flex justify-between items-center text-sm font-bold">
                              <span className="text-white/50">Quali Range</span>
                              <span className="text-white">
                                {
                                  predictionApi.data.uncertaintyRange.qualifying
                                    ?.confidence_interval
                                }
                              </span>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-white/30 font-mono text-xs w-6">
                                P
                                {
                                  predictionApi.data.uncertaintyRange.qualifying
                                    ?.min_position
                                }
                              </span>
                              <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden relative">
                                <div
                                  className="absolute top-0 bottom-0 bg-white/30 rounded-full"
                                  style={{ left: "0%", right: "0%" }}
                                ></div>
                                <div className="absolute top-0 bottom-0 w-1 bg-white left-1/2 -translate-x-1/2 rounded-full shadow-[0_0_10px_white]"></div>
                              </div>
                              <span className="text-white/30 font-mono text-xs w-6">
                                P
                                {
                                  predictionApi.data.uncertaintyRange.qualifying
                                    ?.max_position
                                }
                              </span>
                            </div>
                          </div>

                          <div className="flex flex-col gap-3">
                            <div className="flex justify-between items-center text-sm font-bold">
                              <span className="text-red-400">Race Range</span>
                              <span className="text-red-400">
                                {
                                  predictionApi.data.uncertaintyRange.race
                                    ?.confidence_interval
                                }
                              </span>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-white/30 font-mono text-xs w-6">
                                P
                                {
                                  predictionApi.data.uncertaintyRange.race
                                    ?.min_position
                                }
                              </span>
                              <div className="flex-1 h-3 bg-red-950/30 rounded-full overflow-hidden relative">
                                <div
                                  className="absolute top-0 bottom-0 bg-red-500/40 rounded-full"
                                  style={{ left: "0%", right: "0%" }}
                                ></div>
                                <div className="absolute top-0 bottom-0 w-1 bg-red-500 left-1/2 -translate-x-1/2 rounded-full shadow-[0_0_10px_red]"></div>
                              </div>
                              <span className="text-white/30 font-mono text-xs w-6">
                                P
                                {
                                  predictionApi.data.uncertaintyRange.race
                                    ?.max_position
                                }
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Metadata & Analysis */}
                    <div className="flex flex-col gap-6">
                      <div className="p-6 flex flex-col justify-center">
                        <h4 className="text-white/50 font-bold text-xs uppercase tracking-widest mb-4 flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-white" />
                          Model Architecture
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col">
                            <span className="text-white/30 text-xs mb-1">
                              Architecture
                            </span>
                            <span className="font-bold">
                              {predictionApi.data.modelType
                                ? "Enhanced Ensemble"
                                : "Gradient Boost"}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-white/30 text-xs mb-1">
                              Accuracy Factor
                            </span>
                            <span className="font-bold text-red-400">
                              {predictionApi.data.modelPerformance
                                ?.model_accuracy || "+89%"}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-white/30 text-xs mb-1">
                              Training Sets
                            </span>
                            <span className="font-bold font-mono">
                              {predictionApi.data.modelPerformance
                                ?.training_data_size || 718}
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-white/30 text-xs mb-1">
                              Base Weather
                            </span>
                            <span className="font-bold capitalize">
                              {weather.replace("_", " ")}
                            </span>
                          </div>
                        </div>
                      </div>

                      {predictionApi.data.riskAssessment && (
                        <div className="p-6 flex flex-col justify-center">
                          <h4 className="text-white/50 font-bold text-xs uppercase tracking-widest mb-4 flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-white" />
                            Factor Risk
                          </h4>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex justify-between items-center text-sm bg-white/5 px-3 py-2 rounded-xl">
                              <span className="text-white/60">Weather</span>
                              <span
                                className={`font-bold ${predictionApi.data.riskAssessment.weather_risk === "High" ? "text-red-500" : "text-white"}`}
                              >
                                {predictionApi.data.riskAssessment.weather_risk}
                              </span>
                            </div>
                            <div className="flex justify-between items-center text-sm bg-white/5 px-3 py-2 rounded-xl">
                              <span className="text-white/60">Strategy</span>
                              <span className="font-bold text-white">
                                {
                                  predictionApi.data.riskAssessment
                                    .strategy_risk
                                }
                              </span>
                            </div>
                            <div className="flex justify-between items-center text-sm bg-white/5 px-3 py-2 rounded-xl">
                              <span className="text-white/60">Mechanical</span>
                              <span className="font-bold text-white">
                                {
                                  predictionApi.data.riskAssessment
                                    .mechanical_risk
                                }
                              </span>
                            </div>
                            <div className="flex justify-between items-center text-sm bg-white/5 px-3 py-2 rounded-xl">
                              <span className="text-white">Overall</span>
                              <span
                                className={`font-bold ${predictionApi.data.riskAssessment.overall_risk === "High" ? "text-red-500" : "text-white"}`}
                              >
                                {predictionApi.data.riskAssessment.overall_risk}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* AI Explanation Terminal Block */}
                  {predictionApi.data.confidenceExplanation && (
                    <div className="p-8 mt-2 relative">
                      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 to-transparent"></div>
                      <h4 className="text-white font-bold text-xs uppercase tracking-widest mb-4 flex items-center gap-2 opacity-50">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                        Neural Analysis Report
                      </h4>
                      <p className="text-white/80 font-mono text-sm leading-relaxed whitespace-pre-line tracking-tight">
                        {predictionApi.data.confidenceExplanation}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </DataWrapper>
          </AnimatedPageWrapper>
        </div>
      </div>
    </div>
  );
};

export default DriverPredictor;
