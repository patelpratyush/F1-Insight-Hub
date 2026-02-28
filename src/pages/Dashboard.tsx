import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import ChampionshipPressureChart from "@/components/ChampionshipPressureChart";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import useApiCall from "@/hooks/useApiCall";
import { motion } from "framer-motion";
import {
    Activity,
    AlertCircle,
    BarChart3,
    Calendar,
    Cloud,
    CloudRain,
    Crown,
    Flag,
    RefreshCw,
    Sun,
    Target,
    Thermometer,
    Timer,
    TrendingDown,
    TrendingUp,
    Trophy,
    Users,
    Wind,
    Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

const Dashboard = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedDrivers, setSelectedDrivers] = useState([
    "VER",
    "LEC",
    "NOR",
    "RUS",
    "PIA",
    "HAM",
  ]);
  const [showAllRaces, setShowAllRaces] = useState(false);
  const [showDriverDropdown, setShowDriverDropdown] = useState(false);
  const [selectedCircuit, setSelectedCircuit] = useState("Monaco Grand Prix");
  const [liveDataLastUpdate, setLiveDataLastUpdate] = useState(null);

  // API calls
  const dashboardApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/f1/dashboard/2025`);
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success)
        throw new Error(data.message || "Failed to fetch dashboard data");
      return data.data;
    },
    { maxRetries: 3, retryDelay: 2000 },
  );

  const performanceTrendsLast5Api = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/f1/dashboard-trends/2025?all_races=false`,
      );
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success)
        throw new Error(data.message || "Failed to fetch performance trends");
      return data.performance_trends;
    },
    { maxRetries: 3, retryDelay: 2000 },
  );

  const performanceTrendsAllApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/f1/dashboard-trends/2025?all_races=true`,
      );
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success)
        throw new Error(data.message || "Failed to fetch performance trends");
      return data.performance_trends;
    },
    { maxRetries: 3, retryDelay: 2000 },
  );

  const liveWeatherApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/weather/current`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ circuit_name: selectedCircuit }),
      });
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success) throw new Error("Failed to fetch weather data");
      return data;
    },
    { maxRetries: 2, retryDelay: 1000 },
  );

  const liveChampionshipApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/championship/standings`);
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success)
        throw new Error("Failed to fetch championship standings");
      return data;
    },
    { maxRetries: 2, retryDelay: 1000 },
  );

  const availableCircuitsApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/weather/circuits`);
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success) throw new Error("Failed to fetch available circuits");
      return data.circuits;
    },
    { maxRetries: 2, retryDelay: 1000 },
  );

  const nextRaceApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/results/next-race`);
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success) throw new Error("Failed to fetch next race");
      return data;
    },
    { maxRetries: 2, retryDelay: 1000 },
  );

  const raceWeekendForecastApi = useApiCall(
    async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const nextRaceResponse = await fetch(`${apiUrl}/api/results/next-race`);
      if (!nextRaceResponse.ok) throw new Error("Failed to get next race");
      const nextRaceData = await nextRaceResponse.json();
      if (!nextRaceData.success || !nextRaceData.next_race)
        throw new Error("No upcoming race found");

      const nextRace = nextRaceData.next_race;
      const response = await fetch(`${apiUrl}/api/weather/race-weekend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          circuit_name: nextRace.name,
          race_date: nextRace.date,
        }),
      });
      if (!response.ok)
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      if (!data.success)
        throw new Error("Failed to fetch race weekend forecast");
      return data;
    },
    { maxRetries: 2, retryDelay: 1000 },
  );

  const availableDrivers = [
    { code: "VER", name: "Verstappen", color: "#EF4444", strokeDasharray: "" },
    { code: "LEC", name: "Leclerc", color: "#DC143C", strokeDasharray: "" },
    { code: "NOR", name: "Norris", color: "#FF8700", strokeDasharray: "" },
    { code: "RUS", name: "Russell", color: "#00D2BE", strokeDasharray: "" },
    { code: "PIA", name: "Piastri", color: "#FF8700", strokeDasharray: "5 5" },
    { code: "HAM", name: "Hamilton", color: "#DC143C", strokeDasharray: "3 3" },
    {
      code: "ANT",
      name: "Antonelli",
      color: "#00D2BE",
      strokeDasharray: "2 2",
    },
    { code: "ALB", name: "Albon", color: "#0066CC", strokeDasharray: "" },
    { code: "STR", name: "Stroll", color: "#006F62", strokeDasharray: "" },
    { code: "HUL", name: "Hulkenberg", color: "#52E252", strokeDasharray: "" },
    { code: "GAS", name: "Gasly", color: "#0090FF", strokeDasharray: "" },
    { code: "ALO", name: "Alonso", color: "#006F62", strokeDasharray: "4 4" },
    { code: "SAI", name: "Sainz", color: "#0066CC", strokeDasharray: "4 4" },
    { code: "TSU", name: "Tsunoda", color: "#6692FF", strokeDasharray: "" },
    { code: "OCO", name: "Ocon", color: "#FFFFFF", strokeDasharray: "" },
  ];

  const toggleDriver = (driverCode) => {
    setSelectedDrivers((prev) =>
      prev.includes(driverCode)
        ? prev.filter((code) => code !== driverCode)
        : [...prev, driverCode],
    );
  };

  const getFilteredPerformanceData = () => {
    const trendsData = showAllRaces
      ? performanceTrendsAllApi.data || []
      : performanceTrendsLast5Api.data ||
        dashboardApi.data?.performance_trends ||
        [];
    return !trendsData || trendsData.length === 0 ? [] : trendsData;
  };

  const getWeatherIcon = (condition) => {
    switch (condition?.toLowerCase()) {
      case "clear":
        return <Sun className="h-8 w-8 text-white" />;
      case "light_rain":
        return <CloudRain className="h-8 w-8 text-white" />;
      case "heavy_rain":
        return <CloudRain className="h-8 w-8 text-white" />;
      case "overcast":
        return <Cloud className="h-8 w-8 text-white" />;
      default:
        return <Cloud className="h-8 w-8 text-white/50" />;
    }
  };

  const getGripLevelColor = (gripLevel) => {
    switch (gripLevel?.toLowerCase()) {
      case "excellent":
        return "bg-white";
      case "good":
        return "bg-white/80";
      case "variable":
        return "bg-white/50";
      case "poor":
        return "bg-red-500";
      default:
        return "bg-white/20";
    }
  };

  const refreshLiveData = () => {
    liveWeatherApi.execute();
    liveChampionshipApi.execute();
    nextRaceApi.execute();
    raceWeekendForecastApi.execute();
    setLiveDataLastUpdate(new Date());
  };

  useEffect(() => {
    setIsVisible(true);
    dashboardApi.execute();
    if (showAllRaces) performanceTrendsAllApi.execute();
    else performanceTrendsLast5Api.execute();

    availableCircuitsApi.execute();
    liveWeatherApi.execute();
    liveChampionshipApi.execute();
    nextRaceApi.execute();
    raceWeekendForecastApi.execute();
    setLiveDataLastUpdate(new Date());
  }, []);

  useEffect(() => {
    if (showAllRaces) performanceTrendsAllApi.execute();
    else performanceTrendsLast5Api.execute();
  }, [showAllRaces]);

  useEffect(() => {
    if (selectedCircuit) liveWeatherApi.execute();
  }, [selectedCircuit]);

  useEffect(() => {
    const interval = setInterval(() => refreshLiveData(), 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDriverDropdown) {
        const dropdown = document.querySelector(".driver-dropdown");
        if (dropdown && !dropdown.contains(event.target))
          setShowDriverDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showDriverDropdown]);

  const championshipData = dashboardApi.data?.championship_standings || [];
  const recentRaceData = dashboardApi.data?.latest_race || null;
  const weatherData = dashboardApi.data?.weather_analysis || [];
  const upcomingRace = dashboardApi.data?.upcoming_race || null;
  const seasonStats = dashboardApi.data?.season_statistics || {
    completedRaces: 15,
    totalRaces: 24,
  };

  const liveWeatherData = liveWeatherApi.data;
  const liveChampionshipData = liveChampionshipApi.data;
  const nextRaceData = nextRaceApi.data;
  const availableCircuits = availableCircuitsApi.data || [];
  const raceWeekendForecastData = raceWeekendForecastApi.data;

  const getPositionChange = (driver) => {
    const changes = [-2, -1, 0, 0, 0, 1, 2];
    const randomIndex = Math.abs(driver.name.charCodeAt(0)) % changes.length;
    return changes[randomIndex];
  };

  if (dashboardApi.loading && !dashboardApi.data) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading F1 Dashboard..." />
      </div>
    );
  }

  if (dashboardApi.error && !dashboardApi.data) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center">
        <ErrorDisplay
          title="Failed to load dashboard"
          message={dashboardApi.error}
          onRetry={dashboardApi.retry}
          isRetrying={dashboardApi.isRetrying}
          variant="card"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white px-[16px] md:px-[64px] pb-32 overflow-hidden selection:bg-red-600/30 font-sans">
      {/* Background Graphic Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 mix-blend-screen">
        <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-red-600/5 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[60vw] h-[60vw] bg-red-900/5 rounded-full blur-[150px]"></div>
      </div>

      <div className="max-w-screen-2xl mx-auto relative z-10 pt-8">
        {/* Header - Flowing Typography layout */}
        <AnimatedPageWrapper delay={100}>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 gap-6">
            <div className="flex flex-col">
              <span className="text-red-500 font-bold uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                2025 Season Hub
              </span>
              <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-white drop-shadow-md">
                COMMAND <br /> CENTER
              </h1>
            </div>

            <div className="flex gap-4 items-center">
              <Button
                onClick={dashboardApi.retry}
                className="rounded-full bg-white/5 border-l-2 border-t border-white/10 border-r-0 border-b-0 text-white hover:bg-white/10 hover:border-red-500/50 transition-all h-12 px-6"
                disabled={dashboardApi.isRetrying}
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${dashboardApi.isRetrying ? "animate-spin" : ""}`}
                />
                {dashboardApi.isRetrying ? "Syncing Data..." : "Sync Telemetry"}
              </Button>
            </div>
          </div>
        </AnimatedPageWrapper>

        {/* Big Asymmetrical Data Highlights - Not Boxes, but Floating Typographic elements */}
        <StaggeredAnimation
          delay={300}
          staggerDelay={100}
          className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-24 border-y border-white/10 py-12"
        >
          <div className="flex flex-col">
            <span className="text-white/40 uppercase tracking-widest text-xs font-bold mb-4 flex items-center gap-2">
              <Crown className="w-4 h-4 text-red-500" /> Leader
            </span>
            <span className="text-4xl md:text-5xl font-black tracking-tighter">
              {championshipData.length > 0
                ? championshipData[0].name.split(" ")[1] ||
                  championshipData[0].name
                : "N/A"}
            </span>
            <span className="text-red-500 font-mono mt-2">
              {championshipData.length > 0
                ? `${championshipData[0].points} PTS`
                : "0 PTS"}
            </span>
          </div>

          <div className="flex flex-col border-l border-white/5 pl-8">
            <span className="text-white/40 uppercase tracking-widest text-xs font-bold mb-4 flex items-center gap-2">
              <Trophy className="w-4 h-4 text-red-500" /> Prev Winner
            </span>
            <span className="text-4xl md:text-5xl font-black tracking-tighter truncate">
              {recentRaceData?.podium[0]?.name.split(" ")[1] || "N/A"}
            </span>
            <span className="text-white/60 font-mono mt-2 truncate w-full">
              {recentRaceData?.raceName || "Unknown"}
            </span>
          </div>

          <div className="flex flex-col border-l border-white/5 pl-8">
            <span className="text-white/40 uppercase tracking-widest text-xs font-bold mb-4 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-red-500" /> Next Race
            </span>
            <span className="text-4xl md:text-5xl font-black tracking-tighter truncate">
              {nextRaceData?.next_race
                ? nextRaceData.next_race.name.replace(" Grand Prix", "")
                : "TBD"}
            </span>
            <span className="text-white/60 font-mono mt-2">
              {nextRaceData?.next_race
                ? new Date(nextRaceData.next_race.date).toLocaleDateString()
                : "N/A"}
            </span>
          </div>

          <div className="flex flex-col border-l border-white/5 pl-8">
            <span className="text-white/40 uppercase tracking-widest text-xs font-bold mb-4 flex items-center gap-2">
              <Flag className="w-4 h-4 text-red-500" /> Completion
            </span>
            <div className="flex items-end gap-2">
              <span className="text-4xl md:text-5xl font-black tracking-tighter">
                {seasonStats?.completedRaces || 15}
              </span>
              <span className="text-xl text-white/40 font-black tracking-tighter mb-1">
                / {seasonStats?.totalRaces || 24}
              </span>
            </div>
            <span className="text-white/60 font-mono mt-2">ROUND</span>
          </div>
        </StaggeredAnimation>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-24">
          {/* Performance Trends - Massive Full Bleed Graph */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-8">
            <div className="flex flex-col h-full">
              <div className="flex flex-col md:flex-row justify-between md:items-end mb-8 gap-4">
                <div>
                  <h2 className="text-3xl font-black tracking-tighter">
                    DRIVER TRAJECTORY
                  </h2>
                  <p className="text-white/50 font-light mt-1">
                    Points accumulation over time.
                  </p>
                </div>

                {/* Floating Filters */}
                <div className="flex items-center gap-3">
                  <div className="flex bg-[#111111] rounded-full p-1 border-l-2 border-t border-white/10 border-r-0 border-b-0">
                    <button
                      onClick={() => setShowAllRaces(false)}
                      className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${
                        !showAllRaces
                          ? "bg-white text-black leading-none"
                          : "text-white/50 hover:text-white"
                      }`}
                    >
                      5 Races
                    </button>
                    <button
                      onClick={() => setShowAllRaces(true)}
                      className={`px-4 py-2 rounded-full text-xs font-bold transition-all ${
                        showAllRaces
                          ? "bg-white text-black leading-none"
                          : "text-white/50 hover:text-white"
                      }`}
                    >
                      Season
                    </button>
                  </div>

                  <div className="relative driver-dropdown relative z-50">
                    <button
                      onClick={() => setShowDriverDropdown(!showDriverDropdown)}
                      className="flex items-center gap-2 px-5 py-2.5 bg-[#111111] border-l-2 border-t border-white/10 border-r-0 border-b-0 rounded-full hover:bg-white/5 transition-all text-sm font-bold"
                    >
                      Drivers ({selectedDrivers.length}){" "}
                      <span className="text-xs opacity-50">▼</span>
                    </button>
                    {showDriverDropdown && (
                      <div className="absolute top-full right-0 mt-2 w-64 bg-[#111111] border-l-2 border-t border-white/10 border-r-0 border-b-0 rounded-none shadow-2xl p-4 max-h-[300px] overflow-y-auto z-50">
                        <div className="flex gap-2 mb-4 pb-4 border-b border-white/5">
                          <button
                            onClick={() =>
                              setSelectedDrivers(
                                availableDrivers.map((d) => d.code),
                              )
                            }
                            className="text-xs font-bold text-white/50 hover:text-white"
                          >
                            Select All
                          </button>
                          <button
                            onClick={() => setSelectedDrivers([])}
                            className="text-xs font-bold text-white/50 hover:text-white"
                          >
                            Clear
                          </button>
                        </div>
                        <div className="flex flex-col gap-1">
                          {availableDrivers.map((driver) => (
                            <label
                              key={driver.code}
                              className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 cursor-pointer transition-colors"
                            >
                              <Checkbox
                                checked={selectedDrivers.includes(driver.code)}
                                onCheckedChange={() =>
                                  toggleDriver(driver.code)
                                }
                                className="border-white/20 data-[state=checked]:bg-white data-[state=checked]:text-black"
                              />
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: driver.color }}
                              ></div>
                              <span className="text-sm font-medium">
                                {driver.name}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <DataWrapper
                loading={
                  showAllRaces
                    ? performanceTrendsAllApi.loading
                    : performanceTrendsLast5Api.loading
                }
                error={
                  showAllRaces
                    ? performanceTrendsAllApi.error
                    : performanceTrendsLast5Api.error
                }
                data={getFilteredPerformanceData()}
                onRetry={() =>
                  showAllRaces
                    ? performanceTrendsAllApi.execute()
                    : performanceTrendsLast5Api.execute()
                }
                isRetrying={
                  showAllRaces
                    ? performanceTrendsAllApi.isRetrying
                    : performanceTrendsLast5Api.isRetrying
                }
                minHeight="min-h-[400px]"
              >
                <div className="flex-1 w-full min-h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={getFilteredPerformanceData()}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#ffffff"
                        strokeOpacity={0.05}
                        vertical={false}
                      />
                      <XAxis
                        dataKey="race"
                        stroke="#ffffff"
                        strokeOpacity={0.3}
                        tick={{ fill: "#ffffff", opacity: 0.5, fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                        dy={10}
                      />
                      <YAxis
                        stroke="#ffffff"
                        strokeOpacity={0.3}
                        tick={{ fill: "#ffffff", opacity: 0.5, fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                        dx={-10}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#000000",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "16px",
                          color: "#ffffff",
                        }}
                        itemStyle={{ color: "#ffffff" }}
                      />

                      {selectedDrivers.map((driverCode) => {
                        const driver = availableDrivers.find(
                          (d) => d.code === driverCode,
                        );
                        if (!driver) return null;
                        return (
                          <Line
                            key={driverCode}
                            type="monotone"
                            dataKey={driverCode}
                            stroke={driver.color}
                            strokeWidth={3}
                            strokeDasharray={driver.strokeDasharray}
                            name={driver.name}
                            connectNulls={false}
                            dot={{ r: 4, strokeWidth: 0, fill: driver.color }}
                            activeDot={{ r: 6, strokeWidth: 0 }}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </DataWrapper>
            </div>
          </AnimatedPageWrapper>

          {/* Standings List - Organic transparent list */}
          <AnimatedPageWrapper
            delay={800}
            className="lg:col-span-4 flex flex-col pt-2 lg:pt-0"
          >
            <div className="mb-8">
              <h2 className="text-3xl font-black tracking-tighter">
                STANDINGS
              </h2>
              <p className="text-white/50 font-light mt-1">
                Current driver ranks.
              </p>
            </div>
            <DataWrapper
              loading={dashboardApi.loading && !championshipData.length}
              error={
                dashboardApi.error && !championshipData.length
                  ? dashboardApi.error
                  : null
              }
              data={championshipData}
              onRetry={dashboardApi.retry}
              isRetrying={dashboardApi.isRetrying}
              minHeight="min-h-[300px]"
            >
              <div className="flex flex-col gap-2 max-h-[450px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {championshipData.map((driver, idx) => (
                  <div
                    key={driver.driver}
                    className="group flex items-center justify-between p-4 rounded-none hover:bg-white/5 transition-colors duration-300"
                  >
                    <div className="flex items-center gap-4">
                      <span
                        className={`text-xl font-bold w-6 text-center ${idx < 3 ? "text-white" : "text-white/30"}`}
                      >
                        {driver.position}
                      </span>
                      <div className="flex flex-col">
                        <span className="font-bold text-lg leading-tight group-hover:text-red-500 transition-colors">
                          {driver.name}
                        </span>
                        <span className="text-xs text-white/50 uppercase tracking-widest">
                          {driver.team}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-black text-xl">
                        {driver.points}
                      </span>
                      <span className="text-xs text-red-500 font-mono">
                        {driver.wins}W
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </DataWrapper>
          </AnimatedPageWrapper>
        </div>

        {/* Free-flowing Bento style grids for secondary data */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-24">
          {/* Recent Race Results Mini-Standings */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-[#111111] rounded-none p-8 md:p-10 border-l-2 border-t border-white/5 border-r-0 border-b-0 flex flex-col hover:border-red-500/50 hover:shadow-[0_0_40px_rgba(220,38,38,0.1)] transition-all duration-500"
          >
            <div className="mb-8">
              <h3 className="text-white/50 text-xs font-bold uppercase tracking-widest mb-1">
                Latest Results
              </h3>
              <h4 className="text-2xl font-black tracking-tighter">
                {recentRaceData?.raceName}
              </h4>
            </div>

            <div className="flex flex-col gap-4 mb-8">
              {recentRaceData?.podium?.slice(0, 3).map((result, idx) => (
                <div key={result.driver} className="flex items-center gap-4">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-black ${idx === 0 ? "bg-white text-black" : "bg-white/10 text-white"}`}
                  >
                    {result.position}
                  </div>
                  <div className="flex flex-col flex-1">
                    <span className="font-bold">{result.name}</span>
                    <span className="text-white/50 text-xs uppercase tracking-widest">
                      {result.team}
                    </span>
                  </div>
                  <span className="font-mono text-sm">{result.time}</span>
                </div>
              ))}
            </div>

            <div className="mt-auto pt-6 border-t border-white/10 flex justify-between items-center text-sm">
              <span className="text-white/50 font-medium flex items-center gap-2">
                <Timer className="w-4 h-4" /> Fastest Lap
              </span>
              <span className="font-mono bg-red-500/10 text-red-400 px-3 py-1 rounded-full">
                {recentRaceData?.fastestLap?.driver}
              </span>
            </div>
          </motion.div>

          {/* Live Weather Freeform */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="bg-red-950/40 rounded-none p-8 md:p-10 border-l-2 border-t border-red-500/20 border-r-0 border-b-0 flex flex-col relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/10 blur-[60px] rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none group-hover:bg-red-500/20 transition-all duration-700"></div>

            <div className="flex justify-between items-start mb-auto relative z-10">
              <div>
                <h3 className="text-red-400 text-xs font-bold uppercase tracking-widest mb-1">
                  Live Conditions
                </h3>
                <h4 className="text-2xl font-black tracking-tighter pr-4">
                  {liveWeatherData?.location || "Loading..."}
                </h4>
              </div>
              <div
                className="p-3 bg-red-500/10 rounded-full border border-red-500/30 text-red-400 group-hover:bg-red-500 group-hover:text-white transition-all cursor-pointer"
                onClick={refreshLiveData}
              >
                <RefreshCw
                  className={`w-5 h-5 ${liveWeatherApi.loading ? "animate-spin" : ""}`}
                />
              </div>
            </div>

            <div className="flex items-end justify-between my-8 relative z-10">
              <div className="flex flex-col">
                <span className="text-[64px] font-black leading-none tracking-tighter">
                  {liveWeatherData?.temperature?.toFixed(0) || "0"}°
                </span>
                <span className="text-red-300 font-medium capitalize mt-2 flex items-center gap-2">
                  {getWeatherIcon(liveWeatherData?.condition)}{" "}
                  {liveWeatherData?.description || "Unknown"}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 relative z-10 pt-6 border-t border-red-500/20">
              <div className="flex flex-col">
                <span className="text-red-400/60 text-xs font-bold uppercase mb-1">
                  Track
                </span>
                <span className="font-mono text-lg">
                  {liveWeatherData?.track_temperature?.toFixed(1) || "-"}°
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-red-400/60 text-xs font-bold uppercase mb-1">
                  Wind
                </span>
                <span className="font-mono text-lg">
                  {liveWeatherData?.wind_speed?.toFixed(0) || "-"}{" "}
                  <span className="text-xs">kmh</span>
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-red-400/60 text-xs font-bold uppercase mb-1">
                  Grip
                </span>
                <span className="font-mono text-lg text-white capitalize">
                  {liveWeatherData?.grip_level || "-"}
                </span>
              </div>
            </div>
          </motion.div>

          {/* Quick Actions / Jump Menu */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="flex flex-col justify-between p-2"
          >
            <div>
              <h2 className="text-3xl font-black tracking-tighter mb-2">
                QUICK JUMP
              </h2>
              <p className="text-white/50 font-light mb-8">
                Navigate to deep analytics.
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => (window.location.href = "/predictor")}
                className="group flex items-center justify-between p-5 rounded-none bg-[#111111] border-l-2 border-t border-white/10 border-r-0 border-b-0 hover:border-white hover:bg-white text-white hover:text-black transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-white/5 group-hover:bg-black/5 flex items-center justify-center">
                    <Trophy className="w-5 h-5" />
                  </div>
                  <span className="font-bold text-lg">Driver Predictor</span>
                </div>
                <span className="opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all">
                  ➔
                </span>
              </button>

              <button
                onClick={() => (window.location.href = "/telemetry")}
                className="group flex items-center justify-between p-5 rounded-none bg-[#111111] border-l-2 border-t border-white/10 border-r-0 border-b-0 hover:border-white hover:bg-white text-white hover:text-black transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-white/5 group-hover:bg-black/5 flex items-center justify-center">
                    <Activity className="w-5 h-5" />
                  </div>
                  <span className="font-bold text-lg">Telemetry Sync</span>
                </div>
                <span className="opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all">
                  ➔
                </span>
              </button>

              <button
                onClick={() => (window.location.href = "/strategy")}
                className="group flex items-center justify-between p-5 rounded-none bg-[#111111] border-l-2 border-t border-white/10 border-r-0 border-b-0 hover:border-white hover:bg-white text-white hover:text-black transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-white/5 group-hover:bg-black/5 flex items-center justify-center">
                    <Target className="w-5 h-5" />
                  </div>
                  <span className="font-bold text-lg">Strategy Engine</span>
                </div>
                <span className="opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all">
                  ➔
                </span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
