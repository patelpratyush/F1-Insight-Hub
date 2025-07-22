
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
  const [isLoading, setIsLoading] = useState(false);

  const drivers = [
    { code: "VER", name: "Max Verstappen", team: "Red Bull", number: 1 },
    { code: "NOR", name: "Lando Norris", team: "McLaren", number: 4 },
    { code: "BOR", name: "Gabriel Bortoleto", team: "Kick Sauber", number: 5 },
    { code: "HAD", name: "Isack Hadjar", team: "Kick Sauber", number: 6 },
    { code: "GAS", name: "Pierre Gasly", team: "Alpine", number: 10 },
    { code: "ANT", name: "Kimi Antonelli", team: "Mercedes", number: 12 },
    { code: "ALO", name: "Fernando Alonso", team: "Aston Martin", number: 14 },
    { code: "LEC", name: "Charles Leclerc", team: "Ferrari", number: 16 },
    { code: "STR", name: "Lance Stroll", team: "Aston Martin", number: 18 },
    { code: "TSU", name: "Yuki Tsunoda", team: "AlphaTauri", number: 22 },
    { code: "ALB", name: "Alexander Albon", team: "Williams", number: 23 },
    { code: "HUL", name: "Nico Hulkenberg", team: "Haas", number: 27 },
    { code: "LAW", name: "Liam Lawson", team: "AlphaTauri", number: 30 },
    { code: "OCO", name: "Esteban Ocon", team: "Alpine", number: 31 },
    { code: "COL", name: "Franco Colapinto", team: "Williams", number: 43 },
    { code: "HAM", name: "Lewis Hamilton", team: "Ferrari", number: 44 },
    { code: "SAI", name: "Carlos Sainz", team: "Williams", number: 55 },
    { code: "RUS", name: "George Russell", team: "Mercedes", number: 63 },
    { code: "PIA", name: "Oscar Piastri", team: "McLaren", number: 81 },
    { code: "BEA", name: "Oliver Bearman", team: "Haas", number: 87 },
  ];

  const tracks = [
    "Bahrain Grand Prix",
    "Saudi Arabian Grand Prix",
    "Australian Grand Prix", 
    "Japanese Grand Prix",
    "Chinese Grand Prix",
    "Miami Grand Prix",
    "Emilia Romagna Grand Prix",
    "Monaco Grand Prix",
    "Canadian Grand Prix",
    "Spanish Grand Prix",
    "Austrian Grand Prix",
    "British Grand Prix",
    "Hungarian Grand Prix",
    "Belgian Grand Prix",
    "Dutch Grand Prix",
    "Italian Grand Prix",
    "Azerbaijan Grand Prix",
    "Singapore Grand Prix",
    "United States Grand Prix",
    "Mexico City Grand Prix",
    "São Paulo Grand Prix",
    "Las Vegas Grand Prix",
    "Qatar Grand Prix",
    "Abu Dhabi Grand Prix"
  ];

  const handlePredict = async () => {
    if (!selectedDriver || !selectedTrack || !weather) {
      alert("Please select driver, track, and weather conditions");
      return;
    }

    const selectedDriverData = drivers.find(d => d.code === selectedDriver);
    setIsLoading(true);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/predict/driver`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver: selectedDriver,
          track: selectedTrack,
          weather: weather.toLowerCase(),
          team: selectedDriverData?.team || "Unknown"
        })
      });

      if (!response.ok) {
        throw new Error('Prediction failed');
      }

      const data = await response.json();
      
      // Calculate podium probability based on race position prediction
      const podiumProbability = data.predicted_race_position <= 3 ? 
        Math.min(95, data.race_confidence * 100 + (4 - data.predicted_race_position) * 10) : 
        Math.max(5, (21 - data.predicted_race_position) * 3);
      
      setPrediction({
        qualifying: data.predicted_qualifying_position,
        race: data.predicted_race_position,
        podiumProbability: podiumProbability,
        qualifyingConfidence: data.qualifying_confidence,
        raceConfidence: data.race_confidence
      });
    } catch (error) {
      console.error('Error making prediction:', error);
      alert('Failed to get prediction. Make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
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
            Gradient Boosting Machine Learning model trained on 2024-2025 F1 data that predicts race results based on past performance, qualifying times, and structured F1 data.
          </p>
          <div className="mt-2 text-sm text-gray-500">
            🏎️ 738 race records • 27 drivers • 25 races • Updated for 2025 season transfers
          </div>
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
                  disabled={!selectedDriver || !selectedTrack || !weather || isLoading}
                  className="w-full bg-red-600 hover:bg-red-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  {isLoading ? 'Generating...' : 'Generate Prediction'}
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
                        <div className="text-sm text-gray-400 mt-2">
                          Confidence: {prediction.qualifyingConfidence ? (prediction.qualifyingConfidence * 100).toFixed(0) : 75}%
                        </div>
                      </div>
                      
                      <div className="text-center p-6 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-xl border border-green-600/20">
                        <div className="text-3xl font-bold text-green-400 mb-2">P{prediction.race}</div>
                        <div className="text-gray-300 font-medium">Race Position</div>
                        <div className="text-sm text-gray-400 mt-2">
                          Confidence: {prediction.raceConfidence ? (prediction.raceConfidence * 100).toFixed(0) : 65}%
                        </div>
                      </div>
                      
                      <div className="text-center p-6 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-xl border border-purple-600/20">
                        <div className="text-3xl font-bold text-purple-400 mb-2">{Math.round(prediction.podiumProbability)}%</div>
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
                          <span>Model Type</span>
                          <Badge variant="outline" className="text-green-400 border-green-400">Gradient Boosting</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Weather Conditions</span>
                          <Badge variant="outline" className="text-blue-400 border-blue-400 capitalize">{weather}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Team Performance</span>
                          <Badge variant="outline" className="text-purple-400 border-purple-400">{drivers.find(d => d.code === selectedDriver)?.team}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Qualifying vs Race</span>
                          <Badge variant="outline" className={`${prediction.race <= prediction.qualifying ? 'text-green-400 border-green-400' : 'text-red-400 border-red-400'}`}>
                            {prediction.race <= prediction.qualifying ? 'Gains positions' : 'Loses positions'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Overall Confidence</span>
                          <Badge variant="outline" className="text-blue-400 border-blue-400">
                            {Math.round((prediction.qualifyingConfidence + prediction.raceConfidence) / 2 * 100)}%
                          </Badge>
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
