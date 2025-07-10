
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Trophy, TrendingUp, Target, Zap, Cloud, Users } from "lucide-react";

const DriverPredictor = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [prediction, setPrediction] = useState(null);

  const drivers = [
    { code: "VER", name: "Max Verstappen", team: "Red Bull Racing" },
    { code: "LEC", name: "Charles Leclerc", team: "Ferrari" },
    { code: "HAM", name: "Lewis Hamilton", team: "Mercedes" },
    { code: "RUS", name: "George Russell", team: "Mercedes" },
    { code: "PER", name: "Sergio Pérez", team: "Red Bull Racing" },
    { code: "SAI", name: "Carlos Sainz", team: "Ferrari" },
    { code: "NOR", name: "Lando Norris", team: "McLaren" },
    { code: "PIA", name: "Oscar Piastri", team: "McLaren" },
  ];

  const tracks = [
    "Bahrain International Circuit",
    "Jeddah Corniche Circuit", 
    "Albert Park Circuit",
    "Suzuka International Racing Course",
    "Miami International Autodrome",
    "Imola Circuit",
    "Monaco Street Circuit",
    "Circuit de Barcelona-Catalunya",
    "Circuit Gilles Villeneuve",
    "Red Bull Ring",
    "Silverstone Circuit",
    "Hungaroring"
  ];

  const handlePredict = () => {
    // Simulate prediction logic
    const qualifyingPosition = Math.floor(Math.random() * 10) + 1;
    const racePosition = Math.floor(Math.random() * 10) + 1;
    const podiumProbability = Math.floor(Math.random() * 100);
    
    setPrediction({
      qualifying: qualifyingPosition,
      race: racePosition,
      podiumProbability: podiumProbability
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-3 bg-red-600 rounded-lg">
              <Trophy className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Driver Performance Predictor</h1>
          </div>
          <p className="text-gray-400 text-lg">
            Predict how a selected driver will perform in the next race based on historical data and machine learning algorithms.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Users className="h-5 w-5 text-red-500" />
                  <span>Race Parameters</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Select driver and race conditions for prediction
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Driver</label>
                  <Select value={selectedDriver} onValueChange={setSelectedDriver}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select a driver" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {drivers.map((driver) => (
                        <SelectItem key={driver.code} value={driver.code} className="text-white hover:bg-gray-600">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{driver.code}</span>
                            <span className="text-gray-400">- {driver.name}</span>
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
                      <SelectValue placeholder="Select a track" />
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weather Conditions</label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select weather" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      <SelectItem value="dry" className="text-white hover:bg-gray-600">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                          <span>Dry</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="wet" className="text-white hover:bg-gray-600">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span>Wet</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="mixed" className="text-white hover:bg-gray-600">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                          <span>Mixed</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handlePredict}
                  disabled={!selectedDriver || !selectedTrack || !weather}
                  className="w-full bg-red-600 hover:bg-red-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Generate Prediction
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {prediction ? (
              <div className="space-y-6">
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <Target className="h-5 w-5 text-green-500" />
                      <span>Prediction Results</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      AI-generated performance prediction for {selectedDriver} at {selectedTrack}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center p-6 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-xl border border-blue-600/20">
                        <div className="text-3xl font-bold text-blue-400 mb-2">P{prediction.qualifying}</div>
                        <div className="text-gray-300 font-medium">Qualifying Position</div>
                        <div className="text-sm text-gray-400 mt-2">Predicted grid position</div>
                      </div>
                      
                      <div className="text-center p-6 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-xl border border-green-600/20">
                        <div className="text-3xl font-bold text-green-400 mb-2">P{prediction.race}</div>
                        <div className="text-gray-300 font-medium">Race Position</div>
                        <div className="text-sm text-gray-400 mt-2">Predicted finish</div>
                      </div>
                      
                      <div className="text-center p-6 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-xl border border-purple-600/20">
                        <div className="text-3xl font-bold text-purple-400 mb-2">{prediction.podiumProbability}%</div>
                        <div className="text-gray-300 font-medium">Podium Probability</div>
                        <div className="text-sm text-gray-400 mt-2">Top 3 finish chance</div>
                      </div>
                    </div>

                    <div className="mt-8 p-4 bg-gray-700/30 rounded-lg">
                      <h4 className="text-white font-medium mb-3 flex items-center">
                        <TrendingUp className="h-4 w-4 mr-2 text-red-500" />
                        Performance Insights
                      </h4>
                      <div className="space-y-2 text-sm text-gray-300">
                        <div className="flex items-center justify-between">
                          <span>Historical Performance at Track</span>
                          <Badge variant="outline" className="text-green-400 border-green-400">Strong</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Weather Adaptation</span>
                          <Badge variant="outline" className="text-yellow-400 border-yellow-400">Moderate</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Team Performance Trend</span>
                          <Badge variant="outline" className="text-green-400 border-green-400">Improving</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Confidence Level</span>
                          <Badge variant="outline" className="text-blue-400 border-blue-400">85%</Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <Trophy className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">No Prediction Generated</CardTitle>
                  <CardDescription className="text-gray-500">
                    Select a driver, track, and weather conditions to generate a performance prediction.
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

export default DriverPredictor;
