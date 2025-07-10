
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Flag, Timer, Zap, Users, Trophy } from "lucide-react";

const RacePredictor = () => {
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [predictions, setPredictions] = useState(null);

  const tracks = [
    "Bahrain International Circuit",
    "Jeddah Corniche Circuit", 
    "Albert Park Circuit",
    "Suzuka International Racing Course",
    "Miami International Autodrome",
    "Monaco Street Circuit",
    "Silverstone Circuit"
  ];

  const mockDrivers = [
    { pos: 1, driver: "VER", name: "Max Verstappen", team: "Red Bull Racing", confidence: 92, gap: "Winner" },
    { pos: 2, driver: "LEC", name: "Charles Leclerc", team: "Ferrari", confidence: 85, gap: "+12.4s" },
    { pos: 3, driver: "HAM", name: "Lewis Hamilton", team: "Mercedes", confidence: 78, gap: "+28.7s" },
    { pos: 4, driver: "RUS", name: "George Russell", team: "Mercedes", confidence: 72, gap: "+35.2s" },
    { pos: 5, driver: "PER", name: "Sergio Pérez", team: "Red Bull Racing", confidence: 68, gap: "+42.1s" },
    { pos: 6, driver: "SAI", name: "Carlos Sainz", team: "Ferrari", confidence: 65, gap: "+58.9s" },
    { pos: 7, driver: "NOR", name: "Lando Norris", team: "McLaren", confidence: 61, gap: "+1 lap" },
    { pos: 8, driver: "PIA", name: "Oscar Piastri", team: "McLaren", confidence: 58, gap: "+1 lap" },
  ];

  const handlePredict = () => {
    setPredictions(mockDrivers);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return "text-green-400 border-green-400";
    if (confidence >= 60) return "text-yellow-400 border-yellow-400";
    return "text-red-400 border-red-400";
  };

  const getPositionColor = (pos) => {
    if (pos === 1) return "bg-gradient-to-r from-yellow-500 to-yellow-600";
    if (pos === 2) return "bg-gradient-to-r from-gray-400 to-gray-500";
    if (pos === 3) return "bg-gradient-to-r from-amber-600 to-amber-700";
    return "bg-gradient-to-r from-gray-600 to-gray-700";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-blue-600 rounded-lg">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Race Result Predictor</h1>
          </div>
          <p className="text-gray-400 text-lg">
            Predict final positions for all drivers in an upcoming race based on qualifying results and race conditions.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Flag className="h-5 w-5 text-blue-500" />
                  <span>Race Setup</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Configure race parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Circuit</label>
                  <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select circuit" />
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weather</label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select weather" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      <SelectItem value="dry" className="text-white hover:bg-gray-600">Dry</SelectItem>
                      <SelectItem value="wet" className="text-white hover:bg-gray-600">Wet</SelectItem>
                      <SelectItem value="mixed" className="text-white hover:bg-gray-600">Mixed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handlePredict}
                  disabled={!selectedTrack || !weather}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Predict Results
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-3">
            {predictions ? (
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center space-x-2">
                    <Trophy className="h-5 w-5 text-yellow-500" />
                    <span>Predicted Race Results</span>
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    AI-generated race finish prediction for {selectedTrack}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {predictions.map((driver, index) => (
                      <div 
                        key={driver.driver}
                        className="flex items-center p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors"
                      >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm mr-4 ${getPositionColor(driver.pos)}`}>
                          {driver.pos}
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <span className="font-bold text-white text-lg">{driver.driver}</span>
                            <span className="text-gray-300">{driver.name}</span>
                            <Badge variant="outline" className="text-gray-400 border-gray-500 text-xs">
                              {driver.team}
                            </Badge>
                          </div>
                        </div>

                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div className="text-sm text-gray-400">Gap</div>
                            <div className="text-white font-medium">{driver.gap}</div>
                          </div>
                          
                          <Badge variant="outline" className={`${getConfidenceColor(driver.confidence)} min-w-[60px] justify-center`}>
                            {driver.confidence}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 rounded-lg border border-yellow-600/20">
                      <Users className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-yellow-400">20</div>
                      <div className="text-sm text-gray-300">Drivers</div>
                    </div>
                    
                    <div className="text-center p-4 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-lg border border-green-600/20">
                      <Timer className="h-6 w-6 text-green-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-green-400">87%</div>
                      <div className="text-sm text-gray-300">Avg Confidence</div>
                    </div>
                    
                    <div className="text-center p-4 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-lg border border-blue-600/20">
                      <Flag className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-blue-400">58</div>
                      <div className="text-sm text-gray-300">Race Laps</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <TrendingUp className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">No Predictions Generated</CardTitle>
                  <CardDescription className="text-gray-500">
                    Select a circuit and weather conditions to generate race result predictions.
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

export default RacePredictor;
