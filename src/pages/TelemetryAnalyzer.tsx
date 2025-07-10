
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, Gauge, Zap, Settings, Users, BarChart3 } from "lucide-react";

const TelemetryAnalyzer = () => {
  const [selectedSeason, setSelectedSeason] = useState("");
  const [selectedGP, setSelectedGP] = useState("");
  const [selectedSession, setSelectedSession] = useState("");
  const [selectedDriver, setSelectedDriver] = useState("");
  const [showData, setShowData] = useState(false);

  const seasons = ["2024", "2023", "2022", "2021"];
  const grandPrix = ["Bahrain GP", "Saudi Arabia GP", "Australia GP", "Japan GP", "Miami GP"];
  const sessions = ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"];
  const drivers = ["VER", "LEC", "HAM", "RUS", "PER", "SAI", "NOR", "PIA"];

  const handleAnalyze = () => {
    setShowData(true);
  };

  const mockTelemetryData = {
    speed: [320, 315, 310, 305, 298, 285, 270, 250, 240, 260, 280, 300, 315, 320],
    throttle: [100, 95, 90, 85, 80, 70, 60, 45, 30, 50, 70, 85, 95, 100],
    brake: [0, 0, 5, 15, 30, 45, 60, 80, 90, 70, 40, 20, 5, 0],
    gear: [8, 8, 7, 6, 5, 4, 3, 2, 2, 3, 4, 5, 6, 7]
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-green-600 rounded-lg">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Telemetry Data Analyzer</h1>
          </div>
          <p className="text-gray-400 text-lg">
            Analyze and visualize telemetry data for drivers across different sessions with detailed lap-by-lap insights.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Controls Section */}
          <div className="lg:col-span-1">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Settings className="h-5 w-5 text-green-500" />
                  <span>Session Selection</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Choose session and driver for analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Season</label>
                  <Select value={selectedSeason} onValueChange={setSelectedSeason}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select season" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {seasons.map((season) => (
                        <SelectItem key={season} value={season} className="text-white hover:bg-gray-600">
                          {season}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Grand Prix</label>
                  <Select value={selectedGP} onValueChange={setSelectedGP}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select GP" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {grandPrix.map((gp) => (
                        <SelectItem key={gp} value={gp} className="text-white hover:bg-gray-600">
                          {gp}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Session</label>
                  <Select value={selectedSession} onValueChange={setSelectedSession}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select session" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {sessions.map((session) => (
                        <SelectItem key={session} value={session} className="text-white hover:bg-gray-600">
                          {session}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Driver</label>
                  <Select value={selectedDriver} onValueChange={setSelectedDriver}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select driver" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {drivers.map((driver) => (
                        <SelectItem key={driver} value={driver} className="text-white hover:bg-gray-600">
                          {driver}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handleAnalyze}
                  disabled={!selectedSeason || !selectedGP || !selectedSession || !selectedDriver}
                  className="w-full bg-green-600 hover:bg-green-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Analyze Telemetry
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Data Visualization Section */}
          <div className="lg:col-span-3">
            {showData ? (
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-green-500" />
                    <span>Telemetry Analysis - {selectedDriver}</span>
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    {selectedSeason} • {selectedGP} • {selectedSession}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-4 bg-gray-700/50">
                      <TabsTrigger value="overview" className="text-white data-[state=active]:bg-green-600">Overview</TabsTrigger>
                      <TabsTrigger value="speed" className="text-white data-[state=active]:bg-green-600">Speed</TabsTrigger>
                      <TabsTrigger value="throttle" className="text-white data-[state=active]:bg-green-600">Throttle</TabsTrigger>
                      <TabsTrigger value="comparison" className="text-white data-[state=active]:bg-green-600">Compare</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="mt-6">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center p-4 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-lg border border-blue-600/20">
                          <Gauge className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                          <div className="text-lg font-bold text-blue-400">320</div>
                          <div className="text-sm text-gray-300">Max Speed (km/h)</div>
                        </div>
                        
                        <div className="text-center p-4 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-lg border border-green-600/20">
                          <Activity className="h-6 w-6 text-green-400 mx-auto mb-2" />
                          <div className="text-lg font-bold text-green-400">1:24.567</div>
                          <div className="text-sm text-gray-300">Best Lap Time</div>
                        </div>
                        
                        <div className="text-center p-4 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-lg border border-purple-600/20">
                          <Zap className="h-6 w-6 text-purple-400 mx-auto mb-2" />
                          <div className="text-lg font-bold text-purple-400">92%</div>
                          <div className="text-sm text-gray-300">Avg Throttle</div>
                        </div>
                        
                        <div className="text-center p-4 bg-gradient-to-br from-red-600/20 to-red-800/20 rounded-lg border border-red-600/20">
                          <Users className="h-6 w-6 text-red-400 mx-auto mb-2" />
                          <div className="text-lg font-bold text-red-400">15</div>
                          <div className="text-sm text-gray-300">Laps Completed</div>
                        </div>
                      </div>

                      <div className="h-64 bg-gray-700/30 rounded-lg flex items-center justify-center">
                        <div className="text-center">
                          <Activity className="h-16 w-16 text-gray-500 mx-auto mb-4" />
                          <div className="text-gray-400">Telemetry Visualization</div>
                          <div className="text-sm text-gray-500">Speed, throttle, brake, and gear data would be displayed here</div>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="speed" className="mt-6">
                      <div className="h-80 bg-gray-700/30 rounded-lg flex items-center justify-center">
                        <div className="text-center">
                          <Gauge className="h-16 w-16 text-blue-500 mx-auto mb-4" />
                          <div className="text-gray-400">Speed Analysis</div>
                          <div className="text-sm text-gray-500">Detailed speed telemetry chart would be displayed here</div>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="throttle" className="mt-6">
                      <div className="h-80 bg-gray-700/30 rounded-lg flex items-center justify-center">
                        <div className="text-center">
                          <Zap className="h-16 w-16 text-green-500 mx-auto mb-4" />
                          <div className="text-gray-400">Throttle Analysis</div>
                          <div className="text-sm text-gray-500">Throttle and brake application data would be displayed here</div>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="comparison" className="mt-6">
                      <div className="h-80 bg-gray-700/30 rounded-lg flex items-center justify-center">
                        <div className="text-center">
                          <Users className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                          <div className="text-gray-400">Driver Comparison</div>
                          <div className="text-sm text-gray-500">Side-by-side driver telemetry comparison would be displayed here</div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <Activity className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">No Telemetry Data Loaded</CardTitle>
                  <CardDescription className="text-gray-500">
                    Select a season, Grand Prix, session, and driver to analyze telemetry data.
                  </CardDescription>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TelemetryAnalyzer;
