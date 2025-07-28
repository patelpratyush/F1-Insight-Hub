import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart3, Users, Trophy, Timer, TrendingUp, TrendingDown, 
  Zap, Flag, Activity, AlertCircle, Crown, Calendar, MapPin, 
  Thermometer, Eye, Award, Target
} from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { drivers2025 } from "@/data/drivers2025";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, RadarChart, 
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ScatterChart, Scatter
} from 'recharts';

const Dashboard = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [recentRaceData, setRecentRaceData] = useState(null);
  const [championshipData, setChampionshipData] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState([]);
  const [weatherData, setWeatherData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsVisible(true);
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Use real FastF1 API for 2025 dashboard data
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/f1/dashboard/2025`);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update state with real data
        setChampionshipData(data.data.championship_standings || []);
        setRecentRaceData(data.data.latest_race);
        setPerformanceMetrics(data.data.performance_trends || []);
        setWeatherData(data.data.weather_analysis || []);
      } else {
        console.error('API returned error:', data);
        // No fallback - show error state
        setChampionshipData([]);
        setRecentRaceData(null);
        setPerformanceMetrics([]);
        setWeatherData([]);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // No fallback - show error state
      setChampionshipData([]);
      setRecentRaceData(null);
      setPerformanceMetrics([]);
      setWeatherData([]);
    } finally {
      setIsLoading(false);
    }
  };

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

  const getPositionChange = (position) => {
    // Mock position changes
    const changes = { 1: 0, 2: 1, 3: -1, 4: 2, 5: -1, 6: 3, 7: -2, 8: 1 };
    return changes[position] || 0;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-gray-400">Loading F1 Dashboard...</p>
        </div>
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
                  onClick={loadDashboardData}
                  variant="outline" 
                  size="sm"
                  className="border-red-600/50 text-red-400 hover:text-white hover:bg-red-600"
                >
                  <Activity className="h-4 w-4 mr-2" />
                  Refresh
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
                  <p className="text-2xl font-bold text-white">Dutch GP</p>
                  <p className="text-green-400 text-sm">August 24, 2025</p>
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
                  <p className="text-2xl font-bold text-white">13 / 24</p>
                  <p className="text-purple-400 text-sm">In Progress</p>
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
                <div className="space-y-3">
                  {championshipData.length > 0 ? championshipData.slice(0, 8).map((driver, index) => {
                    const change = getPositionChange(driver.position);
                    return (
                      <div key={driver.driver} className="flex items-center justify-between p-3 rounded-lg bg-gray-700/30 hover:bg-gray-700/50 transition-all duration-200">
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg font-bold text-white w-6">{driver.position}</span>
                            {change !== 0 && (
                              <div className={`flex items-center ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {change > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
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
                  }) : (
                    <div className="text-center py-8">
                      <p className="text-gray-400">No championship data available</p>
                      <p className="text-sm text-gray-500">Check API connection</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Performance Trends */}
          <AnimatedPageWrapper delay={800} className="xl:col-span-2">
            <Card className="bg-gray-800/50 border-gray-700 h-full">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-blue-500" />
                  <span>Performance Trends</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Points scored in last 5 races
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {performanceMetrics.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={performanceMetrics}>
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
                      <Line type="monotone" dataKey="VER" stroke="#EF4444" strokeWidth={2} name="Verstappen" />
                      <Line type="monotone" dataKey="LEC" stroke="#DC143C" strokeWidth={2} name="Leclerc" />
                      <Line type="monotone" dataKey="NOR" stroke="#FF8700" strokeWidth={2} name="Norris" />
                      <Line type="monotone" dataKey="RUS" stroke="#00D2BE" strokeWidth={2} name="Russell" />
                      <Line type="monotone" dataKey="PIA" stroke="#FF8700" strokeWidth={2} strokeDasharray="5 5" name="Piastri" />
                      <Line type="monotone" dataKey="HAM" stroke="#DC143C" strokeWidth={2} strokeDasharray="3 3" name="Hamilton" />
                        <Line type="monotone" dataKey="ANT" stroke="#00D2BE" strokeWidth={2} strokeDasharray="2 2" name="Antonelli" connectNulls={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <p className="text-gray-400">No performance data available</p>
                        <p className="text-sm text-gray-500">Check API connection</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Recent Race Results */}
          <AnimatedPageWrapper delay={1000}>
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Flag className="h-5 w-5 text-green-500" />
                  <span>Latest Race: {recentRaceData?.raceName}</span>
                </CardTitle>
                <CardDescription className="text-gray-400 flex items-center space-x-4">
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
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentRaceData ? (
                    <>
                      <div>
                        <h4 className="font-medium text-gray-300 mb-3">Podium Finishers</h4>
                        <div className="space-y-2">
                          {recentRaceData.podium.map((result, index) => (
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
                            <span>Fastest Lap: {recentRaceData.fastestLap.driver} ({recentRaceData.fastestLap.time})</span>
                          </span>
                        </div>
                        <Badge variant="outline" className="text-gray-300 border-gray-600">
                          {recentRaceData.totalLaps} laps
                        </Badge>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-400">No recent race data available</p>
                      <p className="text-sm text-gray-500">Check API connection</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Weather Impact Analysis */}
          <AnimatedPageWrapper delay={1200}>
            <Card className="bg-gray-800/50 border-gray-700">
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
                <div className="h-80">
                  {weatherData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={weatherData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="condition" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" domain={[0, 6]} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1F2937', 
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#F3F4F6'
                        }}
                        formatter={(value, name) => [`${value.toFixed(1)}`, `Avg Position - ${name}`]}
                      />
                      <Legend />
                      <Bar dataKey="avgPosition.VER" fill="#EF4444" name="Verstappen" />
                      <Bar dataKey="avgPosition.LEC" fill="#DC143C" name="Leclerc" />
                      <Bar dataKey="avgPosition.NOR" fill="#FF8700" name="Norris" />
                        <Bar dataKey="avgPosition.RUS" fill="#00D2BE" name="Russell" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <p className="text-gray-400">No weather data available</p>
                        <p className="text-sm text-gray-500">Check API connection</p>
                      </div>
                    </div>
                  )}
                </div>
                {weatherData.length > 0 && (
                  <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                    {weatherData.map((condition, index) => (
                      <div key={condition.condition} className="p-2 rounded-lg bg-gray-700/30">
                        <div className="font-medium text-white">{condition.condition}</div>
                        <div className="text-sm text-gray-400">{condition.races} races</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </AnimatedPageWrapper>
        </div>

        {/* Quick Actions */}
        <AnimatedPageWrapper delay={1400}>
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