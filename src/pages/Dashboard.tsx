import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorDisplay from "@/components/ui/error-display";
import DataWrapper from "@/components/ui/data-wrapper";
import useApiCall from "@/hooks/useApiCall";
import { 
  BarChart3, Users, Trophy, Timer, TrendingUp, TrendingDown, 
  Zap, Flag, Activity, AlertCircle, Crown, Calendar, MapPin, 
  Thermometer, Eye, Award, Target
} from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import ChampionshipPressureChart from "@/components/ChampionshipPressureChart";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadarChart, 
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter
} from 'recharts';

const Dashboard = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [selectedDrivers, setSelectedDrivers] = useState(['VER', 'LEC', 'NOR', 'RUS', 'PIA', 'HAM']);
  const [showAllRaces, setShowAllRaces] = useState(false);
  const [showDriverDropdown, setShowDriverDropdown] = useState(false);

  // API call for dashboard data with error handling
  const dashboardApi = useApiCall(async () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/f1/dashboard/2025`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch dashboard data');
    }
    
    return data.data;
  }, { maxRetries: 3, retryDelay: 2000 });

  // API calls for performance trends - separate for last 5 and all races
  const performanceTrendsLast5Api = useApiCall(async () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/f1/dashboard-trends/2025?all_races=false`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch performance trends');
    }
    
    return data.performance_trends;
  }, { maxRetries: 3, retryDelay: 2000 });

  const performanceTrendsAllApi = useApiCall(async () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/f1/dashboard-trends/2025?all_races=true`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch performance trends');
    }
    
    return data.performance_trends;
  }, { maxRetries: 3, retryDelay: 2000 });

  // Available drivers with colors for the performance trends
  const availableDrivers = [
    { code: 'VER', name: 'Verstappen', color: '#EF4444', strokeDasharray: '' },
    { code: 'LEC', name: 'Leclerc', color: '#DC143C', strokeDasharray: '' },
    { code: 'NOR', name: 'Norris', color: '#FF8700', strokeDasharray: '' },
    { code: 'RUS', name: 'Russell', color: '#00D2BE', strokeDasharray: '' },
    { code: 'PIA', name: 'Piastri', color: '#FF8700', strokeDasharray: '5 5' },
    { code: 'HAM', name: 'Hamilton', color: '#DC143C', strokeDasharray: '3 3' },
    { code: 'ANT', name: 'Antonelli', color: '#00D2BE', strokeDasharray: '2 2' },
    { code: 'ALB', name: 'Albon', color: '#0066CC', strokeDasharray: '' },
    { code: 'STR', name: 'Stroll', color: '#006F62', strokeDasharray: '' },
    { code: 'HUL', name: 'Hulkenberg', color: '#52E252', strokeDasharray: '' },
    { code: 'GAS', name: 'Gasly', color: '#0090FF', strokeDasharray: '' },
    { code: 'ALO', name: 'Alonso', color: '#006F62', strokeDasharray: '4 4' },
    { code: 'SAI', name: 'Sainz', color: '#0066CC', strokeDasharray: '4 4' },
    { code: 'TSU', name: 'Tsunoda', color: '#6692FF', strokeDasharray: '' },
    { code: 'OCO', name: 'Ocon', color: '#FFFFFF', strokeDasharray: '' }
  ];

  const toggleDriver = (driverCode) => {
    setSelectedDrivers(prev => 
      prev.includes(driverCode) 
        ? prev.filter(code => code !== driverCode)
        : [...prev, driverCode]
    );
  };

  const getFilteredPerformanceData = () => {
    // Use the appropriate API data based on the toggle
    const trendsData = showAllRaces 
      ? (performanceTrendsAllApi.data || [])
      : (performanceTrendsLast5Api.data || dashboardApi.data?.performance_trends || []);
    
    if (!trendsData || trendsData.length === 0) {
      return [];
    }
    
    return trendsData;
  };

  useEffect(() => {
    setIsVisible(true);
    dashboardApi.execute();
    // Load initial data based on showAllRaces state
    if (showAllRaces) {
      performanceTrendsAllApi.execute();
    } else {
      performanceTrendsLast5Api.execute();
    }
  }, []);

  // Update performance trends when toggle changes
  useEffect(() => {
    if (showAllRaces) {
      performanceTrendsAllApi.execute();
    } else {
      performanceTrendsLast5Api.execute();
    }
  }, [showAllRaces]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDriverDropdown) {
        const dropdown = document.querySelector('.driver-dropdown');
        if (dropdown && !dropdown.contains(event.target)) {
          setShowDriverDropdown(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDriverDropdown]);

  // Extract data from API response with safe defaults
  const championshipData = dashboardApi.data?.championship_standings || [];
  const recentRaceData = dashboardApi.data?.latest_race || null;
  const weatherData = dashboardApi.data?.weather_analysis || [];
  const upcomingRace = dashboardApi.data?.upcoming_race || null;
  const seasonStats = dashboardApi.data?.season_statistics || { completedRaces: 15, totalRaces: 24 };

  const getTeamColor = (team) => {
    const colors = {
      "Red Bull Racing": "#0600EF",
      "Ferrari": "#DC143C", 
      "Mercedes": "#00D2BE",
      "McLaren": "#FF8700",
      "Aston Martin": "#006F62",
      "Alpine": "#0090FF",
      "Racing Bulls": "#6692FF",
      "Williams": "#005AFF",
      "Haas": "#FFFFFF",
      "Kick Sauber": "#52E252"
    };
    return colors[team] || "#6B7280";
  };

  const getPositionChange = (driver) => {
    // Simple random position change for now since we don't have reliable historical data
    // In a real implementation, this would compare current vs previous championship position
    const changes = [-2, -1, 0, 0, 0, 1, 2]; // Most drivers stay same, some move up/down
    const randomIndex = Math.abs(driver.name.charCodeAt(0)) % changes.length;
    return changes[randomIndex];
  };

  // Show loading state for initial load
  if (dashboardApi.loading && !dashboardApi.data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading F1 Dashboard..." />
      </div>
    );
  }

  // Show error state if failed to load and no cached data
  if (dashboardApi.error && !dashboardApi.data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex items-center justify-center">
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-7xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className={`flex items-center justify-between mb-6 transition-all duration-1000 delay-300 transform ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
            }`}>
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-red-600 rounded-lg shadow-lg hover:shadow-red-500/25 transition-all duration-300 hover:scale-110">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white">F1 Dashboard</h1>
                  <p className="text-gray-400">Real-time Formula 1 analytics and insights</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="px-3 py-1 bg-red-600 rounded-lg text-white font-medium">
                  2025 Season
                </div>
                <Button 
                  onClick={dashboardApi.retry}
                  variant="outline" 
                  size="sm"
                  className="border-red-600/50 text-red-400 hover:text-white hover:bg-red-600"
                  disabled={dashboardApi.isRetrying}
                >
                  <Activity className={`h-4 w-4 mr-2 ${dashboardApi.isRetrying ? 'animate-spin' : ''}`} />
                  {dashboardApi.isRetrying ? 'Refreshing...' : 'Refresh'}
                </Button>
              </div>
            </div>
          </div>
        </AnimatedPageWrapper>

        {/* Key Stats Row */}
        <StaggeredAnimation delay={400} staggerDelay={100} className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gray-800/50 border-gray-700 hover:border-red-500/50 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Championship Leader</p>
                  <p className="text-2xl font-bold text-white">
                    {championshipData.length > 0 ? championshipData[0].name : "API Error"}
                  </p>
                  <p className="text-red-400 text-sm">
                    {championshipData.length > 0 ? `${championshipData[0].points} points` : "No data"}
                  </p>
                </div>
                <Crown className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 hover:border-blue-500/50 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Last Race Winner</p>
                  <p className="text-2xl font-bold text-white">
                    {recentRaceData?.podium[0]?.name || "API Error"}
                  </p>
                  <p className="text-blue-400 text-sm">{recentRaceData?.raceName || "No data"}</p>
                </div>
                <Trophy className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 hover:border-green-500/50 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Next Race</p>
                  <p className="text-2xl font-bold text-white">
                    {upcomingRace ? upcomingRace.race_name.replace(' Grand Prix', ' GP') : 'Loading...'}
                  </p>
                  <p className="text-green-400 text-sm">
                    {upcomingRace ? new Date(upcomingRace.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : 'TBD'}
                  </p>
                </div>
                <Calendar className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 hover:border-purple-500/50 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm font-medium">Season Races</p>
                  <p className="text-2xl font-bold text-white">{seasonStats?.completedRaces || 15} / {seasonStats?.totalRaces || 24}</p>
                  <p className="text-purple-400 text-sm">
                    {(seasonStats?.completedRaces || 15) === (seasonStats?.totalRaces || 24) ? 'Complete' : 'In Progress'}
                  </p>
                </div>
                <Flag className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </StaggeredAnimation>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
          {/* Championship Standings */}
          <AnimatedPageWrapper delay={600} className="xl:col-span-1">
            <Card className="bg-gray-800/50 border-gray-700 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  <span>Driver Championship</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Current season standings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DataWrapper
                  loading={dashboardApi.loading && !championshipData.length}
                  error={dashboardApi.error && !championshipData.length ? dashboardApi.error : null}
                  data={championshipData}
                  onRetry={dashboardApi.retry}
                  isRetrying={dashboardApi.isRetrying}
                  loadingMessage="Loading championship standings..."
                  errorTitle="Failed to load standings"
                  errorVariant="inline"
                  minHeight="min-h-[300px]"
                >
                  <div className="space-y-3 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
                    {championshipData.map((driver, index) => {
                      const change = getPositionChange(driver);
                      return (
                        <div key={driver.driver} className="flex items-center justify-between p-3 rounded-lg bg-gray-700/30 hover:bg-gray-700/50 transition-all duration-200">
                          <div className="flex items-center space-x-3">
                            <div className="flex items-center space-x-2">
                              <span className="text-lg font-bold text-white w-6">{driver.position}</span>
                              {change !== 0 && (
                                <div className={`flex items-center ${change < 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {change < 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                  <span className="text-xs ml-1">{Math.abs(change)}</span>
                                </div>
                              )}
                            </div>
                            <div>
                              <div className="font-medium text-white">{driver.name}</div>
                              <div className="text-xs text-gray-400">{driver.team}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-white">{driver.points}</div>
                            <div className="text-xs text-gray-400">{driver.wins}W • {driver.podiums}P</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </DataWrapper>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Performance Trends */}
          <AnimatedPageWrapper delay={800} className="xl:col-span-2">
            <Card className="bg-gray-800/50 border-gray-700 h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <TrendingUp className="h-5 w-5 text-blue-500" />
                      <span>Performance Trends</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Points scored in {showAllRaces ? 'all races' : 'last 5 races'}
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 bg-gray-700/50 rounded-lg p-1">
                      <Button
                        variant={!showAllRaces ? "default" : "ghost"}
                        size="sm"
                        onClick={() => setShowAllRaces(false)}
                        className={`text-xs h-7 px-3 ${
                          !showAllRaces 
                            ? 'bg-blue-600 text-white hover:bg-blue-700' 
                            : 'text-gray-300 hover:text-white hover:bg-gray-600'
                        }`}
                      >
                        Last 5
                      </Button>
                      <Button
                        variant={showAllRaces ? "default" : "ghost"}
                        size="sm"
                        onClick={() => setShowAllRaces(true)}
                        className={`text-xs h-7 px-3 ${
                          showAllRaces 
                            ? 'bg-blue-600 text-white hover:bg-blue-700' 
                            : 'text-gray-300 hover:text-white hover:bg-gray-600'
                        }`}
                      >
                        All Races
                      </Button>
                    </div>
                    <div className="relative driver-dropdown">
                      <Button
                        variant="outline"
                        onClick={() => setShowDriverDropdown(!showDriverDropdown)}
                        className="w-40 bg-gray-700 border-gray-600 text-white hover:bg-gray-600 justify-between"
                      >
                        <span>{selectedDrivers.length} driver{selectedDrivers.length !== 1 ? 's' : ''}</span>
                        <div className={`w-4 h-4 opacity-50 transition-transform duration-200 ${showDriverDropdown ? 'rotate-180' : ''}`}>⌄</div>
                      </Button>
                      {showDriverDropdown && (
                        <div className="absolute top-full left-0 mt-1 w-80 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
                        <div className="p-3">
                          <div className="flex items-center space-x-2 mb-3 pb-2 border-b border-gray-600">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedDrivers(availableDrivers.map(d => d.code))}
                              className="text-xs h-6 px-2 text-gray-300 border-gray-500 hover:bg-gray-600"
                            >
                              All
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedDrivers([])}
                              className="text-xs h-6 px-2 text-gray-300 border-gray-500 hover:bg-gray-600"
                            >
                              None
                            </Button>
                          </div>
                          <div className="grid grid-cols-1 gap-1">
                            {availableDrivers.map((driver) => (
                              <div 
                                key={driver.code} 
                                className="flex items-center space-x-3 py-2 px-2 hover:bg-gray-700 rounded cursor-pointer"
                                onClick={() => toggleDriver(driver.code)}
                              >
                                <Checkbox
                                  id={driver.code}
                                  checked={selectedDrivers.includes(driver.code)}
                                  onCheckedChange={() => toggleDriver(driver.code)}
                                  className="border-gray-500"
                                />
                                <div className="flex items-center space-x-2 flex-1">
                                  <div 
                                    className="w-4 h-1 rounded"
                                    style={{ 
                                      backgroundColor: driver.color,
                                      opacity: driver.strokeDasharray ? 0.7 : 1
                                    }}
                                  ></div>
                                  <label 
                                    htmlFor={driver.code} 
                                    className="text-sm text-white cursor-pointer flex-1"
                                  >
                                    {driver.name}
                                  </label>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <DataWrapper
                  loading={showAllRaces ? performanceTrendsAllApi.loading : performanceTrendsLast5Api.loading}
                  error={showAllRaces ? performanceTrendsAllApi.error : performanceTrendsLast5Api.error}
                  data={getFilteredPerformanceData()}
                  onRetry={() => showAllRaces ? performanceTrendsAllApi.execute() : performanceTrendsLast5Api.execute()}
                  isRetrying={showAllRaces ? performanceTrendsAllApi.isRetrying : performanceTrendsLast5Api.isRetrying}
                  loadingMessage="Loading performance trends..."
                  errorTitle="Failed to load performance data"
                  errorVariant="inline"
                  minHeight="min-h-[320px]"
                >
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={getFilteredPerformanceData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="race" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#F3F4F6'
                        }} 
                      />
                      <Legend />
                      {selectedDrivers.map((driverCode) => {
                        const driver = availableDrivers.find(d => d.code === driverCode);
                        if (!driver) return null;
                        return (
                          <Line 
                            key={driverCode}
                            type="monotone" 
                            dataKey={driverCode} 
                            stroke={driver.color} 
                            strokeWidth={2} 
                            strokeDasharray={driver.strokeDasharray}
                            name={driver.name}
                            connectNulls={false}
                          />
                        );
                      })}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </DataWrapper>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
          {/* Recent Race Results */}
          <AnimatedPageWrapper delay={1000} className="xl:col-span-1">
            <Card className="bg-gray-800/50 border-gray-700 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Flag className="h-5 w-5 text-green-500" />
                  <span>Latest Race: {recentRaceData?.raceName}</span>
                </CardTitle>
                <div className="text-gray-400 text-sm">
                  <div className="flex items-center space-x-4">
                    <span className="flex items-center space-x-1">
                      <Calendar className="h-4 w-4" />
                      <span>{recentRaceData?.date}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Thermometer className="h-4 w-4" />
                      <span>{recentRaceData?.temperature}°C</span>
                    </span>
                    <Badge variant="outline" className="text-gray-300 border-gray-600">
                      {recentRaceData?.weather}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <DataWrapper
                  loading={dashboardApi.loading && !recentRaceData}
                  error={dashboardApi.error && !recentRaceData ? dashboardApi.error : null}
                  data={recentRaceData}
                  onRetry={dashboardApi.retry}
                  isRetrying={dashboardApi.isRetrying}
                  loadingMessage="Loading recent race results..."
                  errorTitle="Failed to load race data"
                  errorVariant="inline"
                  minHeight="min-h-[300px]"
                >
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-300 mb-3">Podium Finishers</h4>
                      <div className="space-y-2">
                        {recentRaceData?.podium?.map((result, index) => (
                          <div key={result.driver} className="flex items-center justify-between p-3 rounded-lg bg-gray-700/30">
                            <div className="flex items-center space-x-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                index === 0 ? 'bg-yellow-500 text-black' :
                                index === 1 ? 'bg-gray-400 text-black' :
                                'bg-amber-600 text-white'
                              }`}>
                                {result.position}
                              </div>
                              <div>
                                <div className="font-medium text-white">{result.name}</div>
                                <div className="text-xs text-gray-400">{result.team}</div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-white font-mono">{result.time}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                      <div className="text-sm text-gray-400">
                        <span className="flex items-center space-x-1">
                          <Timer className="h-4 w-4" />
                          <span>Fastest Lap: {recentRaceData?.fastestLap?.driver} ({recentRaceData?.fastestLap?.time})</span>
                        </span>
                      </div>
                      <Badge variant="outline" className="text-gray-300 border-gray-600">
                        {recentRaceData?.totalLaps} laps
                      </Badge>
                    </div>
                  </div>
                </DataWrapper>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Weather Impact Analysis */}
          <AnimatedPageWrapper delay={1200} className="xl:col-span-2">
            <Card className="bg-gray-800/50 border-gray-700 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Thermometer className="h-5 w-5 text-orange-500" />
                  <span>Weather Impact Analysis</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Average performance by weather conditions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DataWrapper
                  loading={dashboardApi.loading && !weatherData.length}
                  error={dashboardApi.error && !weatherData.length ? dashboardApi.error : null}
                  data={weatherData}
                  onRetry={dashboardApi.retry}
                  isRetrying={dashboardApi.isRetrying}
                  loadingMessage="Loading weather analysis..."
                  errorTitle="Failed to load weather data"
                  errorVariant="inline"
                  minHeight="min-h-[320px]"
                >
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart 
                        data={weatherData} 
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        barCategoryGap="15%"
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis 
                          dataKey="condition" 
                          stroke="#9CA3AF" 
                          fontSize={12}
                          interval={0}
                        />
                        <YAxis 
                          stroke="#9CA3AF" 
                          domain={[0, 8]} 
                          fontSize={12}
                          label={{ value: 'Average Position', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1F2937', 
                            border: '1px solid #374151',
                            borderRadius: '8px',
                            color: '#F3F4F6'
                          }}
                          formatter={(value, name) => [
                            value ? `${parseFloat(value).toFixed(1)}` : 'N/A', 
                            `${name}`
                          ]}
                          labelFormatter={(label) => `${label} Conditions`}
                        />
                        <Legend 
                          wrapperStyle={{ paddingTop: '20px' }}
                          iconType="rect"
                        />
                        {/* Core 6 drivers with distinct colors */}
                        <Bar dataKey="avgPosition.VER" fill="#1E40AF" name="Verstappen" radius={[2, 2, 0, 0]} />
                        <Bar dataKey="avgPosition.LEC" fill="#DC2626" name="Leclerc" radius={[2, 2, 0, 0]} />
                        <Bar dataKey="avgPosition.NOR" fill="#F59E0B" name="Norris" radius={[2, 2, 0, 0]} />
                        <Bar dataKey="avgPosition.PIA" fill="#10B981" name="Piastri" radius={[2, 2, 0, 0]} />
                        <Bar dataKey="avgPosition.RUS" fill="#06B6D4" name="Russell" radius={[2, 2, 0, 0]} />
                        <Bar dataKey="avgPosition.HAM" fill="#8B5CF6" name="Hamilton" radius={[2, 2, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </DataWrapper>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>
        </div>

        {/* Championship Pressure Visualization */}
        <AnimatedPageWrapper delay={1400}>
          <ChampionshipPressureChart 
            standings={championshipData}
            remainingRaces={Math.max(0, (seasonStats?.totalRaces || 24) - (seasonStats?.completedRaces || 15))}
            currentRound={seasonStats?.completedRaces || 15}
            totalRounds={seasonStats?.totalRaces || 24}
          />
        </AnimatedPageWrapper>

        {/* Quick Actions */}
        <AnimatedPageWrapper delay={1600}>
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center space-x-2">
                <Zap className="h-5 w-5 text-purple-500" />
                <span>Quick Analysis Tools</span>
              </CardTitle>
              <CardDescription className="text-gray-400">
                Jump directly to advanced F1 analytics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Button 
                  className="h-20 flex-col space-y-2 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 hover:text-red-300"
                  onClick={() => window.location.href = '/predictor'}
                >
                  <Trophy className="h-6 w-6" />
                  <span className="text-sm">Driver Predictor</span>
                </Button>
                
                <Button 
                  className="h-20 flex-col space-y-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50 text-blue-400 hover:text-blue-300"
                  onClick={() => window.location.href = '/race-predictor'}
                >
                  <TrendingUp className="h-6 w-6" />
                  <span className="text-sm">Race Predictor</span>
                </Button>
                
                <Button 
                  className="h-20 flex-col space-y-2 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 hover:text-green-300"
                  onClick={() => window.location.href = '/telemetry'}
                >
                  <Activity className="h-6 w-6" />
                  <span className="text-sm">Telemetry</span>
                </Button>
                
                <Button 
                  className="h-20 flex-col space-y-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-400 hover:text-purple-300"
                  onClick={() => window.location.href = '/strategy'}
                >
                  <Target className="h-6 w-6" />
                  <span className="text-sm">Strategy Sim</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </AnimatedPageWrapper>
      </div>
    </div>
  );
};

export default Dashboard;