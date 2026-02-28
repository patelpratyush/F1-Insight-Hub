import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import DriverComparisonTelemetry from "@/components/DriverComparisonTelemetry";
import InteractiveTrackMap from "@/components/InteractiveTrackMap";
import LapSelector from "@/components/LapSelector";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import TelemetryOverlapGraphs from "@/components/TelemetryOverlapGraphs";
import TelemetrySpeedTrace from "@/components/TelemetrySpeedTrace";
import { Alert, AlertDescription } from "@/components/ui/alert";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import WeatherContextPanel from "@/components/WeatherContextPanel";
import { driverCodes, drivers2025 } from "@/data/drivers2025";
import { trackNames } from "@/data/tracks2025";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Gauge,
  Loader2,
  Settings,
  Users,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const TelemetryAnalyzer = () => {
  const [selectedSeason, setSelectedSeason] = useState("2025");
  const [selectedGP, setSelectedGP] = useState("");
  const [selectedSession, setSelectedSession] = useState("Qualifying"); // Start with Qualifying as most representative
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedDriver2, setSelectedDriver2] = useState("");
  const [viewMode, setViewMode] = useState("distance"); // "distance" or "time"
  const [telemetryData, setTelemetryData] = useState(null);
  const [speedTraceData, setSpeedTraceData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [error, setError] = useState("");
  const [selectedLap, setSelectedLap] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [availableLaps, setAvailableLaps] = useState([]);
  const [trackMapData, setTrackMapData] = useState(null);
  const [showRacingLine, setShowRacingLine] = useState(true);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const seasons = ["2024", "2025"];
  const sessionMap = {
    "Practice 2": "FP2", // Most representative practice session
    "Practice 3": "FP3", // Final setup confirmation
    "Sprint Qualifying": "SQ", // Sprint pole position battle
    Qualifying: "Q", // Peak performance for race
    Sprint: "S", // Short race format
    Race: "R", // Full race distance
  };

  // Use centralized driver codes
  const drivers = driverCodes;

  // Fetch available races for selected season
  const { data: availableRaces, isLoading: racesLoading } = useQuery({
    queryKey: ["available-sessions", selectedSeason],
    queryFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/telemetry/available-sessions/${selectedSeason}`,
      );
      if (!response.ok) throw new Error("Failed to fetch available races");
      return response.json();
    },
    enabled: !!selectedSeason,
  });

  // Analyze telemetry mutation
  const analyzeTelemetry = useMutation({
    mutationFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/telemetry/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          year: parseInt(selectedSeason),
          race: selectedGP,
          session: sessionMap[selectedSession] || selectedSession,
          drivers: [selectedDriver],
        }),
      });
      if (!response.ok) throw new Error("Failed to analyze telemetry");
      return response.json();
    },
    onSuccess: (data) => {
      setTelemetryData(data);
      setError("");

      // Extract available laps from the telemetry data
      if (
        selectedDriver &&
        data?.performance_metrics?.[selectedDriver]?.lap_times?.all_laps
      ) {
        const laps = data.performance_metrics[
          selectedDriver
        ].lap_times.all_laps.map((lap) => lap.lap_number);
        setAvailableLaps(laps.sort((a, b) => a - b));
        if (laps.length > 0 && !laps.includes(selectedLap)) {
          setSelectedLap(laps[0]);
        }
      }
    },
    onError: (error) => {
      setError(error.message);
      setTelemetryData(null);
    },
  });

  // Get speed trace mutation
  const getSpeedTrace = useMutation({
    mutationFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/telemetry/speed-trace`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          year: parseInt(selectedSeason),
          race: selectedGP,
          driver: selectedDriver,
          session: sessionMap[selectedSession] || selectedSession,
          lap_number: selectedLap,
        }),
      });
      if (!response.ok) throw new Error("Failed to get speed trace");
      return response.json();
    },
    onSuccess: (data) => {
      setSpeedTraceData(data);
      setError("");
    },
    onError: (error) => {
      setError(error.message);
      setSpeedTraceData(null);
    },
  });

  // Get track map mutation
  const getTrackMap = useMutation({
    mutationFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/telemetry/track-map`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          year: parseInt(selectedSeason),
          race: selectedGP,
          driver: selectedDriver,
          session: sessionMap[selectedSession] || selectedSession,
          lap_number: selectedLap,
        }),
      });
      if (!response.ok) throw new Error("Failed to get track map");
      return response.json();
    },
    onSuccess: (data) => {
      setTrackMapData(data);
      setError("");
    },
    onError: (error) => {
      setError(error.message);
      setTrackMapData(null);
    },
  });

  // Driver comparison mutation
  const getDriverComparison = useMutation({
    mutationFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/telemetry/driver-comparison`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            year: parseInt(selectedSeason),
            race: selectedGP,
            driver1: selectedDriver,
            driver2: selectedDriver2,
            session: sessionMap[selectedSession] || selectedSession,
            lap_type: "fastest",
          }),
        },
      );
      if (!response.ok) throw new Error("Failed to get driver comparison");
      return response.json();
    },
    onSuccess: (data) => {
      setComparisonData(data);
      setError("");
    },
    onError: (error) => {
      setError(error.message);
      setComparisonData(null);
    },
  });

  const handleAnalyze = () => {
    analyzeTelemetry.mutate();
  };

  const handleSpeedTrace = () => {
    getSpeedTrace.mutate();
  };

  const handleDriverComparison = () => {
    getDriverComparison.mutate();
  };

  const handleTrackMap = () => {
    getTrackMap.mutate();
  };

  // Auto-refresh speed trace and track map when lap changes
  useEffect(() => {
    if (
      selectedLap &&
      selectedSeason &&
      selectedGP &&
      selectedSession &&
      selectedDriver
    ) {
      if (speedTraceData) {
        getSpeedTrace.mutate();
      }
      if (trackMapData) {
        getTrackMap.mutate();
      }
    }
  }, [selectedLap]);

  // Get lap-specific data from telemetry
  const getLapSpecificData = () => {
    if (
      !telemetryData?.performance_metrics?.[selectedDriver]?.lap_times?.all_laps
    ) {
      return null;
    }

    const allLaps =
      telemetryData.performance_metrics[selectedDriver].lap_times.all_laps;
    const currentLap = allLaps.find((lap) => lap.lap_number === selectedLap);

    return currentLap;
  };

  // Get race options from API data
  // Hybrid approach: Filter API races against standard 2025 track list for consistency
  const apiRaces = availableRaces?.available_races || [];
  const raceOptions = apiRaces.filter((race) =>
    trackNames.some(
      (trackName) =>
        race.race_name === trackName ||
        race.race_name.includes(trackName.replace(" Grand Prix", "")),
    ),
  );

  // Helper function to format lap time
  const formatLapTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(3);
    return `${minutes}:${remainingSeconds.padStart(6, "0")}`;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32 overflow-hidden selection:bg-red-600/30 font-sans">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-red-600/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-red-900/5 rounded-full blur-[150px]"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-7xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className="flex flex-col mb-12 gap-6 relative z-10">
              <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                DEEP DATA TELEMETRY
              </span>
              <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md leading-none">
                TELEMETRY
                <br />
                ANALYZER
              </h1>
              <p className="text-white/50 text-xl font-light max-w-2xl mt-4">
                Analyze and visualize telemetry data for drivers across
                different sessions with detailed lap-by-lap insights.
              </p>
            </div>
          </div>
        </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Controls Section */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-1">
            <Card className="bg-transparent border-0 shadow-none">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4">
                  <Settings className="h-5 w-5 text-green-500" />
                  <span>Session Selection</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Choose session and driver for analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Season
                  </label>
                  <Select
                    value={selectedSeason}
                    onValueChange={setSelectedSeason}
                  >
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                      <SelectValue placeholder="Select season" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {seasons.map((season) => (
                        <SelectItem
                          key={season}
                          value={season}
                          className="text-white hover:bg-white/10 cursor-pointer"
                        >
                          {season}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Grand Prix
                  </label>
                  <Select value={selectedGP} onValueChange={setSelectedGP}>
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                      <SelectValue placeholder="Select GP" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {racesLoading ? (
                        <SelectItem
                          value="loading"
                          disabled
                          className="text-gray-400"
                        >
                          Loading races...
                        </SelectItem>
                      ) : (
                        raceOptions.map((race) => (
                          <SelectItem
                            key={race.race_name}
                            value={race.race_name}
                            className="text-white hover:bg-white/10 cursor-pointer"
                          >
                            {race.race_name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Session
                  </label>
                  <Select
                    value={selectedSession}
                    onValueChange={setSelectedSession}
                  >
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                      <SelectValue placeholder="Select session" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {Object.keys(sessionMap).map((session) => (
                        <SelectItem
                          key={session}
                          value={session}
                          className="text-white hover:bg-white/10 cursor-pointer"
                        >
                          {session}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {/* Session Type Indicator */}
                  {selectedSession && (
                    <div className="mt-4 p-4 border-l-2 border-red-500 bg-white/5 rounded-r-[20px]">
                      <div className="text-xs text-gray-400">
                        Selected Session
                      </div>
                      <div className="text-sm font-medium text-white">
                        {selectedSession}
                      </div>
                      <div className="text-xs text-blue-400">
                        {selectedSession === "Practice 2"
                          ? "🏁 Long runs & tire testing"
                          : selectedSession === "Practice 3"
                            ? "⚙️ Final setup tuning"
                            : selectedSession === "Sprint Qualifying"
                              ? "🏆 Sprint pole battle"
                              : selectedSession === "Qualifying"
                                ? "🚀 Pure speed focus"
                                : selectedSession === "Sprint"
                                  ? "⚡ Short format race"
                                  : "🏁 Full race distance"}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Driver
                  </label>
                  <Select
                    value={selectedDriver}
                    onValueChange={setSelectedDriver}
                  >
                    <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                      <SelectValue placeholder="Select driver">
                        {selectedDriver && (
                          <span>
                            {drivers2025.find((d) => d.id === selectedDriver)
                              ?.name || selectedDriver}
                          </span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                      {drivers.map((driverCode) => {
                        const driverInfo = drivers2025.find(
                          (d) => d.id === driverCode,
                        );
                        return (
                          <SelectItem
                            key={driverCode}
                            value={driverCode}
                            className="text-white hover:bg-white/10 cursor-pointer"
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">
                                {driverInfo?.name || driverCode}
                              </span>
                              <span className="text-xs text-gray-400">
                                #{driverInfo?.number} - {driverInfo?.team}
                              </span>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3 mt-6">
                  <Button
                    onClick={handleAnalyze}
                    disabled={
                      !selectedSeason ||
                      !selectedGP ||
                      !selectedSession ||
                      !selectedDriver ||
                      analyzeTelemetry.isPending
                    }
                    className="w-full bg-red-600 hover:bg-red-700 text-white rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02]"
                    size="lg"
                  >
                    {analyzeTelemetry.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Zap className="mr-2 h-4 w-4" />
                    )}
                    Analyze Session
                  </Button>

                  <Button
                    onClick={handleSpeedTrace}
                    disabled={
                      !selectedSeason ||
                      !selectedGP ||
                      !selectedSession ||
                      !selectedDriver ||
                      getSpeedTrace.isPending
                    }
                    className="w-full bg-white hover:bg-white/90 text-black rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02]"
                    size="lg"
                  >
                    {getSpeedTrace.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Gauge className="mr-2 h-4 w-4" />
                    )}
                    Speed Trace
                  </Button>

                  <Button
                    onClick={handleTrackMap}
                    disabled={
                      !selectedSeason ||
                      !selectedGP ||
                      !selectedSession ||
                      !selectedDriver ||
                      getTrackMap.isPending
                    }
                    className="w-full bg-transparent border border-white/20 hover:bg-white/10 text-white rounded-full h-16 text-lg font-bold tracking-widest transition-all hover:scale-[1.02]"
                    size="lg"
                  >
                    {getTrackMap.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Settings className="mr-2 h-4 w-4" />
                    )}
                    Track Map
                  </Button>
                </div>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Data Visualization Section */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-3">
            {error && (
              <Alert className="mb-6 border-red-600 bg-red-600/10">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-red-400">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {/* Weather Context Panel - Above Telemetry Analysis */}
            {selectedGP && selectedSession && (
              <div className="mb-6">
                <WeatherContextPanel
                  race={selectedGP}
                  session={sessionMap[selectedSession] || selectedSession}
                />
              </div>
            )}

            {telemetryData || speedTraceData ? (
              <Card className="bg-transparent border-0 shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 border-b border-white/10 pb-4 mb-4">
                    <BarChart3 className="h-5 w-5 text-green-500" />
                    <span>Telemetry Analysis - {selectedDriver}</span>
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    {selectedSeason} • {selectedGP} • {selectedSession}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-6 bg-white/5 p-2 rounded-[32px] h-auto">
                      <TabsTrigger
                        value="overview"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Overview
                      </TabsTrigger>
                      <TabsTrigger
                        value="speed"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Speed
                      </TabsTrigger>
                      <TabsTrigger
                        value="throttle"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Throttle
                      </TabsTrigger>
                      <TabsTrigger
                        value="overlap"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Overlap
                      </TabsTrigger>
                      <TabsTrigger
                        value="trackmap"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Track Map
                      </TabsTrigger>
                      <TabsTrigger
                        value="comparison"
                        className="text-white data-[state=active]:bg-white data-[state=active]:text-black rounded-full py-3 font-bold transition-all"
                      >
                        Compare
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="mt-6">
                      {telemetryData && (
                        <div className="space-y-6">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center p-6 bg-white/5 rounded-[24px]">
                              <Activity className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                              <div className="text-lg font-bold text-blue-400">
                                {telemetryData.session_info?.event_name}
                              </div>
                              <div className="text-sm text-gray-300">Event</div>
                            </div>

                            <div className="text-center p-6 bg-white/5 rounded-[24px]">
                              <Gauge className="h-6 w-6 text-green-400 mx-auto mb-2" />
                              <div className="text-lg font-bold text-green-400">
                                {telemetryData.session_info?.track_name}
                              </div>
                              <div className="text-sm text-gray-300">Track</div>
                            </div>

                            <div className="text-center p-6 bg-white/5 rounded-[24px]">
                              <Zap className="h-6 w-6 text-purple-400 mx-auto mb-2" />
                              <div className="text-lg font-bold text-purple-400">
                                {telemetryData.session_info?.weather?.air_temp?.toFixed(
                                  1,
                                ) || "N/A"}
                                °C
                              </div>
                              <div className="text-sm text-gray-300">
                                Air Temp
                              </div>
                            </div>

                            <div className="text-center p-6 bg-white/5 rounded-[24px]">
                              <Users className="h-6 w-6 text-red-400 mx-auto mb-2" />
                              <div className="text-lg font-bold text-red-400">
                                {
                                  Object.keys(
                                    telemetryData.performance_metrics || {},
                                  ).length
                                }
                              </div>
                              <div className="text-sm text-gray-300">
                                Drivers Analyzed
                              </div>
                            </div>
                          </div>

                          {/* Lap Selector with Playback */}
                          {selectedDriver && availableLaps.length > 0 && (
                            <LapSelector
                              availableLaps={availableLaps}
                              selectedLap={selectedLap}
                              onLapChange={setSelectedLap}
                              isPlaying={isPlaying}
                              onPlayStateChange={setIsPlaying}
                              playbackSpeed={playbackSpeed}
                              onSpeedChange={setPlaybackSpeed}
                            />
                          )}

                          {/* Lap-Specific Information */}
                          {selectedDriver &&
                            availableLaps.length > 0 &&
                            (() => {
                              const lapData = getLapSpecificData();
                              return lapData ? (
                                <div className="bg-[#111] border border-white/5 rounded-[32px] p-6">
                                  <h3 className="text-lg font-bold text-white mb-4">
                                    Lap {selectedLap} Details - {selectedDriver}
                                  </h3>
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="text-center">
                                      <div className="text-2xl font-bold text-blue-400">
                                        {(() => {
                                          const minutes = Math.floor(
                                            lapData.lap_time / 60,
                                          );
                                          const seconds = (
                                            lapData.lap_time % 60
                                          ).toFixed(3);
                                          return `${minutes}:${seconds.padStart(6, "0")}`;
                                        })()}
                                      </div>
                                      <div className="text-sm text-gray-300">
                                        Lap Time
                                      </div>
                                    </div>

                                    <div className="text-center">
                                      <div className="text-2xl font-bold text-green-400">
                                        {lapData.position || "N/A"}
                                      </div>
                                      <div className="text-sm text-gray-300">
                                        Position
                                      </div>
                                    </div>

                                    <div className="text-center">
                                      <div className="text-2xl font-bold text-yellow-400">
                                        {lapData.compound || "Unknown"}
                                      </div>
                                      <div className="text-sm text-gray-300">
                                        Tire Compound
                                      </div>
                                    </div>

                                    <div className="text-center">
                                      <div
                                        className={`text-2xl font-bold ${
                                          lapData.lap_number ===
                                          telemetryData.performance_metrics[
                                            selectedDriver
                                          ].lap_times?.fastest_lap_number
                                            ? "text-purple-400"
                                            : "text-gray-400"
                                        }`}
                                      >
                                        {lapData.lap_number ===
                                        telemetryData.performance_metrics[
                                          selectedDriver
                                        ].lap_times?.fastest_lap_number
                                          ? "🏆 FASTEST"
                                          : "REGULAR"}
                                      </div>
                                      <div className="text-sm text-gray-300">
                                        Lap Type
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ) : null;
                            })()}

                          {/* Performance metrics display */}
                          {selectedDriver &&
                            telemetryData.performance_metrics?.[
                              selectedDriver
                            ] && (
                              <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] relative group">
                                <div className="flex items-center justify-between mb-4">
                                  <h3 className="text-xl font-bold text-white">
                                    {selectedDriver} Performance Metrics
                                  </h3>
                                  {availableLaps.length > 0 && (
                                    <div className="bg-white/10 px-4 py-1.5 rounded-full">
                                      <span className="text-blue-400 font-medium text-sm">
                                        Viewing: Lap {selectedLap}
                                      </span>
                                    </div>
                                  )}
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-400">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].speed_stats?.max_speed?.toFixed(1) ||
                                        "N/A"}
                                    </div>
                                    <div className="text-sm text-gray-300">
                                      Max Speed (km/h)
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-green-400">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].lap_times?.fastest_lap?.toFixed(3) ||
                                        "N/A"}
                                    </div>
                                    <div className="text-sm text-gray-300">
                                      Fastest Lap (s)
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-purple-400">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].throttle_stats?.avg_throttle?.toFixed(
                                        1,
                                      ) || "N/A"}
                                      %
                                    </div>
                                    <div className="text-sm text-gray-300">
                                      Avg Throttle
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-red-400">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].brake_stats?.brake_zones?.length || 0}
                                    </div>
                                    <div className="text-sm text-gray-300">
                                      Brake Zones
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}

                          {/* Driver Laptimes Scatterplot */}
                          {selectedDriver &&
                            telemetryData.performance_metrics?.[
                              selectedDriver
                            ] && (
                              <div className="p-8 border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] relative group">
                                <h3 className="text-xl font-bold text-white mb-4">
                                  {selectedDriver} Session Lap Times
                                </h3>
                                <div className="h-96">
                                  <ResponsiveContainer
                                    width="100%"
                                    height="100%"
                                  >
                                    <ScatterChart>
                                      <CartesianGrid
                                        strokeDasharray="3 3"
                                        stroke="#374151"
                                      />
                                      <XAxis
                                        type="number"
                                        dataKey="lap_number"
                                        domain={["dataMin", "dataMax"]}
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                        label={{
                                          value: "Lap Number",
                                          position: "insideBottom",
                                          offset: -5,
                                          style: {
                                            textAnchor: "middle",
                                            fill: "#9CA3AF",
                                          },
                                        }}
                                      />
                                      <YAxis
                                        type="number"
                                        dataKey="lap_time"
                                        domain={["dataMin - 1", "dataMax + 1"]}
                                        reversed={true}
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                        tickFormatter={(value) =>
                                          `${Math.floor(value / 60)}:${(value % 60).toFixed(1).padStart(4, "0")}`
                                        }
                                        label={{
                                          value: "Lap Time",
                                          angle: -90,
                                          position: "insideLeft",
                                          style: {
                                            textAnchor: "middle",
                                            fill: "#9CA3AF",
                                          },
                                        }}
                                      />

                                      {/* Compound-based scatter points */}
                                      {(() => {
                                        const allLaps =
                                          telemetryData.performance_metrics[
                                            selectedDriver
                                          ]?.lap_times?.all_laps || [];
                                        const compoundColors = {
                                          SOFT: "#EF4444", // Red
                                          MEDIUM: "#EAB308", // Yellow
                                          HARD: "#E5E7EB", // White/Gray
                                          INTERMEDIATE: "#10B981", // Green
                                          WET: "#3B82F6", // Blue
                                          UNKNOWN: "#9CA3AF", // Gray
                                        };

                                        const compounds = [
                                          ...new Set(
                                            allLaps.map((lap) => lap.compound),
                                          ),
                                        ].filter((c) => c !== "UNKNOWN");

                                        return compounds.map((compound) => (
                                          <Scatter
                                            key={compound}
                                            name={
                                              compound === "SOFT"
                                                ? "🔴 SOFT"
                                                : compound === "MEDIUM"
                                                  ? "🟡 MEDIUM"
                                                  : compound === "HARD"
                                                    ? "⚪ HARD"
                                                    : compound
                                            }
                                            data={allLaps.filter(
                                              (lap) =>
                                                lap.compound === compound,
                                            )}
                                            fill={
                                              compoundColors[compound] ||
                                              "#9CA3AF"
                                            }
                                            fillOpacity={0.8}
                                          />
                                        ));
                                      })()}

                                      {/* Fastest lap highlight with special styling */}
                                      <Scatter
                                        name="🏆 Fastest Lap"
                                        data={
                                          telemetryData.performance_metrics[
                                            selectedDriver
                                          ]?.lap_times?.all_laps?.filter(
                                            (lap) =>
                                              lap.lap_number ===
                                              telemetryData.performance_metrics[
                                                selectedDriver
                                              ]?.lap_times?.fastest_lap_number,
                                          ) || []
                                        }
                                        fill="#FF0000"
                                        stroke="#FFFFFF"
                                        strokeWidth={2}
                                        fillOpacity={1}
                                      />

                                      {/* Currently selected lap highlight */}
                                      <Scatter
                                        name={`🎯 Selected Lap ${selectedLap}`}
                                        data={
                                          telemetryData.performance_metrics[
                                            selectedDriver
                                          ]?.lap_times?.all_laps?.filter(
                                            (lap) =>
                                              lap.lap_number === selectedLap,
                                          ) || []
                                        }
                                        fill="#3B82F6"
                                        stroke="#FFFFFF"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        shape="star"
                                      />

                                      <Tooltip
                                        content={({ active, payload }) => {
                                          if (
                                            active &&
                                            payload &&
                                            payload.length
                                          ) {
                                            const data = payload[0].payload;
                                            const isFastest =
                                              data.lap_number ===
                                              telemetryData.performance_metrics[
                                                selectedDriver
                                              ].lap_times?.fastest_lap_number;
                                            return (
                                              <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                                                <p className="text-white font-medium">{`Lap ${data.lap_number}`}</p>
                                                <p className="text-green-400">{`Time: ${formatLapTime(data.lap_time)}`}</p>
                                                {data.compound &&
                                                  data.compound !==
                                                    "Unknown" && (
                                                    <p className="text-purple-400">{`Tire: ${data.compound}`}</p>
                                                  )}
                                                {data.sector_1 && (
                                                  <div className="text-sm text-gray-400 mt-1">
                                                    <p>{`S1: ${formatLapTime(data.sector_1)}`}</p>
                                                    {data.sector_2 && (
                                                      <p>{`S2: ${formatLapTime(data.sector_2)}`}</p>
                                                    )}
                                                    {data.sector_3 && (
                                                      <p>{`S3: ${formatLapTime(data.sector_3)}`}</p>
                                                    )}
                                                  </div>
                                                )}
                                                {isFastest && (
                                                  <p className="text-red-400 font-bold">
                                                    🏆 Fastest Lap
                                                  </p>
                                                )}
                                                {!data.is_valid && (
                                                  <p className="text-yellow-400">
                                                    ⚠️ Invalid/Outlap
                                                  </p>
                                                )}
                                              </div>
                                            );
                                          }
                                          return null;
                                        }}
                                      />
                                      <Legend
                                        verticalAlign="top"
                                        height={36}
                                        iconType="circle"
                                        wrapperStyle={{
                                          paddingBottom: "20px",
                                          fontSize: "12px",
                                          lineHeight: "14px",
                                        }}
                                      />
                                    </ScatterChart>
                                  </ResponsiveContainer>
                                </div>
                                <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                                  <div className="text-center">
                                    <div className="text-green-400 font-bold">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].lap_times?.consistency?.toFixed(3) ||
                                        "N/A"}
                                      s
                                    </div>
                                    <div className="text-gray-400">
                                      Consistency (StdDev)
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-blue-400 font-bold">
                                      {formatLapTime(
                                        telemetryData.performance_metrics[
                                          selectedDriver
                                        ].lap_times?.average_lap || 0,
                                      )}
                                    </div>
                                    <div className="text-gray-400">
                                      Average Lap
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-purple-400 font-bold">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].lap_times?.improvement_rate?.toFixed(
                                        3,
                                      ) || "N/A"}
                                      s/lap
                                    </div>
                                    <div className="text-gray-400">
                                      Improvement Rate
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-yellow-400 font-bold">
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].lap_times?.total_laps || 0}
                                    </div>
                                    <div className="text-gray-400">
                                      Total Laps
                                    </div>
                                  </div>
                                </div>

                                {/* Session Type Specific Insights */}
                                <div className="mt-4 text-sm text-gray-400">
                                  <div className="flex items-center justify-between">
                                    <span>Session Analysis:</span>
                                    <span className="text-white">
                                      {selectedSession === "Practice 2"
                                        ? "Practice 2 - Representative pace & tire testing"
                                        : selectedSession === "Practice 3"
                                          ? "Practice 3 - Final setup confirmation"
                                          : selectedSession ===
                                              "Sprint Qualifying"
                                            ? "Sprint Qualifying - Short format pole position"
                                            : selectedSession === "Qualifying"
                                              ? "Qualifying - Peak performance for race grid"
                                              : selectedSession === "Sprint"
                                                ? "Sprint - Short race with points"
                                                : "Race - Full distance competition & strategy"}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between mt-1">
                                    <span>Fastest Lap:</span>
                                    <span className="text-red-400 font-medium">
                                      Lap{" "}
                                      {telemetryData.performance_metrics[
                                        selectedDriver
                                      ].lap_times?.fastest_lap_number || "N/A"}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="speed" className="mt-6">
                      {speedTraceData && !speedTraceData.error ? (
                        <div className="space-y-4">
                          {/* Speed Tab Header */}
                          <div className="bg-[#111] border border-white/5 rounded-[32px] p-6">
                            <div className="flex items-center justify-between">
                              <h3 className="text-lg font-bold text-white">
                                Speed Analysis - {selectedDriver}
                              </h3>
                              <div className="bg-white/10 px-4 py-1.5 rounded-full">
                                <span className="text-green-400 font-medium text-sm">
                                  Lap {selectedLap} Data
                                </span>
                              </div>
                            </div>
                            <div className="mt-3 text-sm text-gray-400">
                              💡 Tip: Use the "Overlap" tab for multi-variable
                              telemetry analysis with toggles and zoom
                              functionality
                            </div>
                          </div>

                          <TelemetrySpeedTrace
                            telemetryData={speedTraceData.telemetry}
                            lapInfo={speedTraceData.lap_info}
                            analysis={speedTraceData.analysis}
                            corners={speedTraceData.corners || []}
                          />
                        </div>
                      ) : (
                        <div className="h-80 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
                          <div className="text-center">
                            <Gauge className="h-16 w-16 text-blue-500 mx-auto mb-4" />
                            <div className="text-gray-400">
                              Speed Trace Analysis
                            </div>
                            <div className="text-sm text-gray-500">
                              Click "Speed Trace" button to load detailed
                              telemetry visualization
                            </div>
                            {speedTraceData?.error && (
                              <div className="text-red-400 mt-2">
                                Error: {speedTraceData.error}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="throttle" className="mt-6">
                      {speedTraceData && !speedTraceData.error ? (
                        <div className="space-y-6">
                          {/* Throttle Tab Header */}
                          <div className="bg-[#111] border border-white/5 rounded-[32px] p-6">
                            <div className="flex items-center justify-between">
                              <h3 className="text-lg font-bold text-white">
                                Throttle & Brake Analysis - {selectedDriver}
                              </h3>
                              <div className="bg-white/10 px-4 py-1.5 rounded-full">
                                <span className="text-yellow-400 font-medium text-sm">
                                  Lap {selectedLap} Data
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Throttle vs Brake Analysis */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                                <Zap className="h-5 w-5 text-green-500 mr-2" />
                                Throttle Application
                              </h3>
                              <div className="space-y-4">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">
                                    Max Throttle:
                                  </span>
                                  <span className="text-green-400 font-bold">
                                    100%
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">
                                    Avg Throttle:
                                  </span>
                                  <span className="text-green-400 font-bold">
                                    {speedTraceData.analysis.full_throttle_pct?.toFixed(
                                      1,
                                    )}
                                    %
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">
                                    Full Throttle Time:
                                  </span>
                                  <span className="text-green-400 font-bold">
                                    {speedTraceData.analysis.full_throttle_pct?.toFixed(
                                      1,
                                    )}
                                    %
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                                <Activity className="h-5 w-5 text-red-500 mr-2" />
                                Braking Analysis
                              </h3>
                              <div className="space-y-4">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">
                                    Brake Zones:
                                  </span>
                                  <span className="text-red-400 font-bold">
                                    {speedTraceData.analysis.braking_zones}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">
                                    Data Type:
                                  </span>
                                  <span className="text-gray-400">
                                    On/Off Signal
                                  </span>
                                </div>
                                <div className="text-sm text-gray-500">
                                  Note: FastF1 brake data for this session is
                                  boolean (on/off) rather than pressure
                                  percentage.
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Input Comparison Chart */}
                          <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                            <h3 className="text-lg font-bold text-white mb-4">
                              Throttle Application vs Speed
                            </h3>
                            <div className="h-96">
                              <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart
                                  data={speedTraceData.telemetry.distance.map(
                                    (distance, index) => ({
                                      distance: Math.round(distance),
                                      speed:
                                        speedTraceData.telemetry.speed[index] ||
                                        0,
                                      throttle:
                                        speedTraceData.telemetry.throttle[
                                          index
                                        ] || 0,
                                    }),
                                  )}
                                >
                                  <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#374151"
                                  />
                                  <XAxis
                                    dataKey="distance"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                    label={{
                                      value: "Distance (m)",
                                      position: "insideBottom",
                                      offset: -5,
                                      style: {
                                        textAnchor: "middle",
                                        fill: "#9CA3AF",
                                      },
                                    }}
                                  />
                                  <YAxis
                                    yAxisId="speed"
                                    domain={[0, "dataMax"]}
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                    label={{
                                      value: "Speed (km/h)",
                                      angle: -90,
                                      position: "insideLeft",
                                      style: {
                                        textAnchor: "middle",
                                        fill: "#9CA3AF",
                                      },
                                    }}
                                  />
                                  <YAxis
                                    yAxisId="throttle"
                                    orientation="right"
                                    domain={[0, 100]}
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                    label={{
                                      value: "Throttle (%)",
                                      angle: 90,
                                      position: "insideRight",
                                      style: {
                                        textAnchor: "middle",
                                        fill: "#9CA3AF",
                                      },
                                    }}
                                  />

                                  {/* Speed line */}
                                  <Line
                                    yAxisId="speed"
                                    type="monotone"
                                    dataKey="speed"
                                    stroke="#3B82F6"
                                    strokeWidth={2}
                                    dot={false}
                                    name="Speed"
                                  />

                                  {/* Throttle area */}
                                  <Area
                                    yAxisId="throttle"
                                    type="monotone"
                                    dataKey="throttle"
                                    stroke="#10B981"
                                    fill="#10B981"
                                    fillOpacity={0.3}
                                    strokeWidth={2}
                                    name="Throttle"
                                  />

                                  <Tooltip
                                    content={({ active, payload, label }) => {
                                      if (active && payload && payload.length) {
                                        return (
                                          <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                                            <p className="text-white font-medium">{`Distance: ${label}m`}</p>
                                            <p className="text-blue-400">{`Speed: ${payload.find((p) => p.dataKey === "speed")?.value?.toFixed(1)} km/h`}</p>
                                            <p className="text-green-400">{`Throttle: ${payload.find((p) => p.dataKey === "throttle")?.value?.toFixed(0)}%`}</p>
                                          </div>
                                        );
                                      }
                                      return null;
                                    }}
                                  />
                                  <Legend
                                    verticalAlign="top"
                                    height={36}
                                    iconType="line"
                                    wrapperStyle={{
                                      paddingBottom: "20px",
                                      fontSize: "12px",
                                    }}
                                  />
                                </ComposedChart>
                              </ResponsiveContainer>
                            </div>
                          </div>

                          {/* Throttle vs Speed Correlation */}
                          <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                            <h3 className="text-lg font-bold text-white mb-4">
                              Throttle vs Speed Correlation
                            </h3>
                            <div className="h-80">
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart
                                  data={(() => {
                                    // Group data by throttle percentage and average the speeds
                                    const grouped = {};
                                    speedTraceData.telemetry.throttle.forEach(
                                      (throttle, index) => {
                                        const throttleVal = Math.round(
                                          throttle || 0,
                                        );
                                        const speed =
                                          speedTraceData.telemetry.speed[
                                            index
                                          ] || 0;
                                        if (throttleVal > 0) {
                                          if (!grouped[throttleVal]) {
                                            grouped[throttleVal] = [];
                                          }
                                          grouped[throttleVal].push(speed);
                                        }
                                      },
                                    );

                                    // Calculate average speed for each throttle percentage
                                    return Object.keys(grouped)
                                      .map((throttle) => ({
                                        throttle: parseInt(throttle),
                                        speed:
                                          grouped[throttle].reduce(
                                            (sum, speed) => sum + speed,
                                            0,
                                          ) / grouped[throttle].length,
                                      }))
                                      .sort((a, b) => a.throttle - b.throttle);
                                  })()}
                                >
                                  <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#374151"
                                  />
                                  <XAxis
                                    dataKey="throttle"
                                    type="number"
                                    domain={[0, 100]}
                                    ticks={[0, 20, 40, 60, 80, 100]}
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                    label={{
                                      value: "Throttle (%)",
                                      position: "insideBottom",
                                      offset: -5,
                                      style: {
                                        textAnchor: "middle",
                                        fill: "#9CA3AF",
                                      },
                                    }}
                                  />
                                  <YAxis
                                    dataKey="speed"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: "#9CA3AF", fontSize: 12 }}
                                    label={{
                                      value: "Speed (km/h)",
                                      angle: -90,
                                      position: "insideLeft",
                                      style: {
                                        textAnchor: "middle",
                                        fill: "#9CA3AF",
                                      },
                                    }}
                                  />

                                  <Line
                                    type="monotone"
                                    dataKey="speed"
                                    stroke="#8B5CF6"
                                    strokeWidth={2}
                                    dot={{
                                      fill: "#8B5CF6",
                                      strokeWidth: 0,
                                      r: 1,
                                    }}
                                    name="Speed Response"
                                  />

                                  <Tooltip
                                    content={({ active, payload, label }) => {
                                      if (active && payload && payload.length) {
                                        return (
                                          <div className="bg-black border border-white/20 rounded-[16px] p-4 shadow-2xl">
                                            <p className="text-white font-medium">{`Throttle: ${label}%`}</p>
                                            <p className="text-purple-400">{`Speed: ${payload[0]?.value?.toFixed(1)} km/h`}</p>
                                          </div>
                                        );
                                      }
                                      return null;
                                    }}
                                  />
                                  <Legend
                                    verticalAlign="top"
                                    height={36}
                                    iconType="line"
                                    wrapperStyle={{
                                      paddingBottom: "20px",
                                      fontSize: "12px",
                                    }}
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                            <div className="mt-4 text-sm text-gray-400">
                              This chart shows how speed responds to throttle
                              input. Higher correlation indicates more
                              predictable acceleration.
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="h-80 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
                          <div className="text-center">
                            <Zap className="h-16 w-16 text-green-500 mx-auto mb-4" />
                            <div className="text-gray-400">
                              Throttle Analysis
                            </div>
                            <div className="text-sm text-gray-500">
                              Click "Speed Trace" to load throttle and brake
                              data
                            </div>
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="overlap" className="mt-6">
                      {speedTraceData && !speedTraceData.error ? (
                        <TelemetryOverlapGraphs
                          telemetryData={speedTraceData.telemetry}
                          driverName={selectedDriver}
                          lapNumber={selectedLap}
                          viewMode={viewMode as "distance" | "time"}
                          onViewModeChange={(mode) => setViewMode(mode)}
                          corners={speedTraceData.corners || []}
                        />
                      ) : (
                        <div className="h-96 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
                          <div className="text-center">
                            <BarChart3 className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                            <div className="text-gray-400">
                              Telemetry Overlap Analysis
                            </div>
                            <div className="text-sm text-gray-500">
                              Click "Speed Trace" button to load telemetry data
                              for overlap visualization
                            </div>
                            {speedTraceData?.error && (
                              <div className="text-red-400 mt-2">
                                Error: {speedTraceData.error}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="trackmap" className="mt-6">
                      {trackMapData && !trackMapData.error ? (
                        <InteractiveTrackMap
                          trackData={trackMapData.track_map}
                          driverName={selectedDriver}
                          lapNumber={selectedLap}
                          isPlaying={isPlaying}
                          onPlayStateChange={setIsPlaying}
                          showRacingLine={showRacingLine}
                          onRacingLineToggle={setShowRacingLine}
                          colorScheme="speed"
                        />
                      ) : (
                        <div className="h-96 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
                          <div className="text-center">
                            <Settings className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                            <div className="text-gray-400">
                              Interactive Track Map
                            </div>
                            <div className="text-sm text-gray-500">
                              Click "Track Map" button to load track
                              visualization
                            </div>
                            {trackMapData?.error && (
                              <div className="text-red-400 mt-2">
                                Error: {trackMapData.error}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="comparison" className="mt-6">
                      <div className="space-y-6">
                        {/* Driver Selection for Comparison */}
                        <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                            <Users className="h-5 w-5 text-purple-500 mr-2" />
                            Driver Comparison Setup
                          </h3>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Driver 1
                              </label>
                              <Select
                                value={selectedDriver}
                                onValueChange={setSelectedDriver}
                              >
                                <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                                  <SelectValue placeholder="Select first driver">
                                    {selectedDriver && (
                                      <span>
                                        {drivers2025.find(
                                          (d) => d.id === selectedDriver,
                                        )?.name || selectedDriver}
                                      </span>
                                    )}
                                  </SelectValue>
                                </SelectTrigger>
                                <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                                  {drivers.map((driverCode) => {
                                    const driverInfo = drivers2025.find(
                                      (d) => d.id === driverCode,
                                    );
                                    return (
                                      <SelectItem
                                        key={driverCode}
                                        value={driverCode}
                                        className="text-white hover:bg-white/10 cursor-pointer"
                                      >
                                        <div className="flex flex-col">
                                          <span className="font-medium">
                                            {driverInfo?.name || driverCode}
                                          </span>
                                          <span className="text-xs text-gray-400">
                                            #{driverInfo?.number} -{" "}
                                            {driverInfo?.team}
                                          </span>
                                        </div>
                                      </SelectItem>
                                    );
                                  })}
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Driver 2
                              </label>
                              <Select
                                value={selectedDriver2}
                                onValueChange={setSelectedDriver2}
                              >
                                <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                                  <SelectValue placeholder="Select second driver">
                                    {selectedDriver2 && (
                                      <span>
                                        {drivers2025.find(
                                          (d) => d.id === selectedDriver2,
                                        )?.name || selectedDriver2}
                                      </span>
                                    )}
                                  </SelectValue>
                                </SelectTrigger>
                                <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                                  {drivers
                                    .filter((d) => d !== selectedDriver)
                                    .map((driverCode) => {
                                      const driverInfo = drivers2025.find(
                                        (d) => d.id === driverCode,
                                      );
                                      return (
                                        <SelectItem
                                          key={driverCode}
                                          value={driverCode}
                                          className="text-white hover:bg-white/10 cursor-pointer"
                                        >
                                          <div className="flex flex-col">
                                            <span className="font-medium">
                                              {driverInfo?.name || driverCode}
                                            </span>
                                            <span className="text-xs text-gray-400">
                                              #{driverInfo?.number} -{" "}
                                              {driverInfo?.team}
                                            </span>
                                          </div>
                                        </SelectItem>
                                      );
                                    })}
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                View Mode
                              </label>
                              <Select
                                value={viewMode}
                                onValueChange={setViewMode}
                              >
                                <SelectTrigger className="bg-white/5 border-white/10 text-white rounded-full h-14 px-5 text-lg font-bold focus:ring-red-500/50">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-[#111111] border-white/10 rounded-[24px]">
                                  <SelectItem
                                    value="distance"
                                    className="text-white hover:bg-white/10 cursor-pointer"
                                  >
                                    Distance
                                  </SelectItem>
                                  <SelectItem
                                    value="time"
                                    className="text-white hover:bg-white/10 cursor-pointer"
                                  >
                                    Time
                                  </SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <Button
                            className="mt-4 bg-purple-600 hover:bg-purple-700"
                            onClick={handleDriverComparison}
                            disabled={
                              !selectedSeason ||
                              !selectedGP ||
                              !selectedSession ||
                              !selectedDriver ||
                              !selectedDriver2 ||
                              getDriverComparison.isPending
                            }
                          >
                            {getDriverComparison.isPending ? (
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <Users className="mr-2 h-4 w-4" />
                            )}
                            Compare Drivers
                          </Button>
                        </div>

                        {/* Driver Comparison Results */}
                        {comparisonData && !comparisonData.error ? (
                          <DriverComparisonTelemetry
                            driver1={comparisonData.driver1}
                            driver2={comparisonData.driver2}
                            viewMode={viewMode}
                            corners={comparisonData.corners || []}
                          />
                        ) : (
                          <div className="border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent rounded-[40px] p-8">
                            <h3 className="text-lg font-bold text-white mb-4">
                              Driver Comparison Visualization
                            </h3>
                            <div className="h-64 bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] flex items-center justify-center p-6">
                              <div className="text-center">
                                <Users className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                                <div className="text-gray-400">
                                  Driver Comparison Charts
                                </div>
                                <div className="text-sm text-gray-500">
                                  {comparisonData?.error
                                    ? `Error: ${comparisonData.error}`
                                    : 'Select two drivers and click "Compare Drivers" to see detailed telemetry comparison'}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-gradient-to-br from-white/[0.02] to-transparent border-t border-l border-white/5 rounded-[40px] h-96 flex items-center justify-center shadow-none p-6">
                <CardContent className="text-center">
                  <Activity className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">
                    No Telemetry Data Loaded
                  </CardTitle>
                  <CardDescription className="text-gray-500">
                    Select a season, Grand Prix, session, and driver to analyze
                    telemetry data.
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

export default TelemetryAnalyzer;
