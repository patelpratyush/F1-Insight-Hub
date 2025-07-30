
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Trophy, TrendingUp, Target, Zap, Cloud, Users } from "lucide-react";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorDisplay from "@/components/ui/error-display";
import DataWrapper from "@/components/ui/data-wrapper";
import useApiCall from "@/hooks/useApiCall";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { drivers2025 } from "@/data/drivers2025";
import { trackNames } from "@/data/tracks2025";

const DriverPredictor = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [inputError, setInputError] = useState("");

  useEffect(() => {
    setIsVisible(true);
  }, []);

  // Use centralized data
  const drivers = drivers2025;
  const tracks = trackNames; // All 2025 F1 tracks

  // API call for driver prediction with error handling
  const predictionApi = useApiCall(async () => {
    const selectedDriverData = drivers.find(d => d.code === selectedDriver);
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
      throw new Error(`HTTP ${response.status}: Failed to generate prediction`);
    }

    const data = await response.json();
    
    if (!data.success && data.message) {
      throw new Error(data.message);
    }
    
    // Calculate podium probability based on race position prediction
    const podiumProbability = data.predicted_race_position <= 3 ? 
      Math.min(95, data.race_confidence * 100 + (4 - data.predicted_race_position) * 10) : 
      Math.max(5, (21 - data.predicted_race_position) * 3);
    
    return {
      qualifying: data.predicted_qualifying_position,
      race: data.predicted_race_position,
      podiumProbability: podiumProbability,
      qualifyingConfidence: data.qualifying_confidence,
      raceConfidence: data.race_confidence
    };
  }, { maxRetries: 2, retryDelay: 1500 });

  const handlePredict = () => {
    // Input validation
    if (!selectedDriver || !selectedTrack || !weather) {
      setInputError("Please select driver, track, and weather conditions");
      return;
    }
    
    setInputError("");
    predictionApi.execute();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-6xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className={`flex items-center space-x-3 mb-4 transition-all duration-1000 delay-300 transform ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
            }`}>
              <div className="p-3 bg-red-600 rounded-lg shadow-lg hover:shadow-red-500/25 transition-all duration-300 hover:scale-110">
                <Trophy className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">Driver Performance Predictor</h1>
            </div>
            <div className={`transition-all duration-1000 delay-500 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
            }`}>
              <p className="text-gray-400 text-lg">
                Gradient Boosting Machine Learning model trained on 2024-2025 F1 data that predicts race results based on past performance, qualifying times, and structured F1 data.
              </p>
              <div className="mt-2 text-sm text-gray-500">
                🏎️ 738 race records • 27 drivers • 25 races • Updated for 2025 season transfers
              </div>
            </div>
          </div>
        </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-1">
            <div className="space-y-6">
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
                      <SelectValue placeholder="Select a driver">
                        {selectedDriver && (
                          <span>
                            {drivers.find(d => d.id === selectedDriver)?.name || selectedDriver}
                          </span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {drivers.map((driver) => (
                        <SelectItem key={driver.id} value={driver.id} className="text-white hover:bg-gray-600">
                          <div className="flex flex-col">
                            <span className="font-medium">{driver.name}</span>
                            <span className="text-xs text-gray-400">#{driver.number} - {driver.team}</span>
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
                      <SelectValue placeholder="Select weather">
                        {weather && (
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${
                              weather === 'clear' ? 'bg-yellow-500' :
                              weather === 'overcast' ? 'bg-gray-400' :
                              weather === 'light_rain' ? 'bg-blue-400' :
                              weather === 'heavy_rain' ? 'bg-blue-600' :
                              weather === 'mixed' ? 'bg-purple-500' : 'bg-gray-500'
                            } flex-shrink-0`}></div>
                            <span>
                              {weather === 'clear' ? 'Clear' :
                               weather === 'overcast' ? 'Overcast' :
                               weather === 'light_rain' ? 'Light Rain' :
                               weather === 'heavy_rain' ? 'Heavy Rain' :
                               weather === 'mixed' ? 'Mixed Conditions' : weather}
                            </span>
                          </div>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600 min-w-[280px] max-h-[300px] z-50">
                      <SelectItem value="clear" className="text-white hover:bg-gray-600 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-yellow-500 rounded-full flex-shrink-0"></div>
                          <div className="flex flex-col">
                            <span className="font-medium">Clear</span>
                            <span className="text-xs text-gray-400">Normal dry race, fastest pace</span>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="overcast" className="text-white hover:bg-gray-600 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full flex-shrink-0"></div>
                          <div className="flex flex-col">
                            <span className="font-medium">Overcast</span>
                            <span className="text-xs text-gray-400">Cooler track, moderate grip</span>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="light_rain" className="text-white hover:bg-gray-600 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-400 rounded-full flex-shrink-0"></div>
                          <div className="flex flex-col">
                            <span className="font-medium">Light Rain</span>
                            <span className="text-xs text-gray-400">Intermediate tires, variable grip</span>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="heavy_rain" className="text-white hover:bg-gray-600 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0"></div>
                          <div className="flex flex-col">
                            <span className="font-medium">Heavy Rain</span>
                            <span className="text-xs text-gray-400">Full wets, slow pace, higher risk</span>
                          </div>
                        </div>
                      </SelectItem>
                      <SelectItem value="mixed" className="text-white hover:bg-gray-600 py-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-purple-500 rounded-full flex-shrink-0"></div>
                          <div className="flex flex-col">
                            <span className="font-medium">Mixed Conditions</span>
                            <span className="text-xs text-gray-400">Switching between dry and wet</span>
                          </div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {inputError && (
                  <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm">{inputError}</p>
                  </div>
                )}
                
                <Button 
                  onClick={handlePredict}
                  disabled={!selectedDriver || !selectedTrack || !weather || predictionApi.loading}
                  className="w-full bg-red-600 hover:bg-red-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className={`mr-2 h-4 w-4 ${predictionApi.loading ? 'animate-spin' : ''}`} />
                  {predictionApi.loading ? 'Generating...' : 'Generate Prediction'}
                </Button>
              </CardContent>
            </Card>
            </div>
          </AnimatedPageWrapper>

          {/* Results Section */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-2">
            <DataWrapper
              loading={predictionApi.loading}
              error={predictionApi.error}
              data={predictionApi.data}
              onRetry={predictionApi.retry}
              isRetrying={predictionApi.isRetrying}
              loadingMessage="Generating AI prediction..."
              errorTitle="Prediction Failed"
              errorVariant="card"
              minHeight="min-h-96"
              fallbackContent={
                <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                  <CardContent className="text-center">
                    <Trophy className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                    <CardTitle className="text-gray-400 mb-2">No Prediction Generated</CardTitle>
                    <CardDescription className="text-gray-500">
                      Select a driver, track, and weather conditions to generate a performance prediction.
                    </CardDescription>
                  </CardContent>
                </Card>
              }
            >
            {predictionApi.data ? (
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
                    <StaggeredAnimation
                      delay={300}
                      staggerDelay={150}
                      className="grid grid-cols-1 md:grid-cols-3 gap-6"
                    >
                      {[
                        {
                          title: "Qualifying Position",
                          gradient: "from-blue-600/20 to-blue-800/20",
                          border: "border-blue-600/20",
                          textColor: "text-blue-400"
                        },
                        {
                          title: "Race Position",
                          gradient: "from-green-600/20 to-green-800/20",
                          border: "border-green-600/20",
                          textColor: "text-green-400"
                        },
                        {
                          title: "Podium Probability",
                          gradient: "from-purple-600/20 to-purple-800/20", 
                          border: "border-purple-600/20",
                          textColor: "text-purple-400"
                        }
                      ].map((item, index) => {
                        const prediction = predictionApi.data;
                        const actualItem = {
                          ...item,
                          value: item.title === "Qualifying Position" ? `P${prediction.qualifying}` :
                                 item.title === "Race Position" ? `P${prediction.race}` :
                                 `${Math.round(prediction.podiumProbability)}%`,
                          confidence: item.title === "Qualifying Position" ? (prediction.qualifyingConfidence ? (prediction.qualifyingConfidence * 100).toFixed(0) : 75) :
                                     item.title === "Race Position" ? (prediction.raceConfidence ? (prediction.raceConfidence * 100).toFixed(0) : 65) :
                                     "Top 3 finish chance"
                        };
                        return (
                          <div 
                            key={index}
                            className={`text-center p-6 bg-gradient-to-br ${actualItem.gradient} rounded-xl border ${actualItem.border} transform transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-${actualItem.textColor.split('-')[1]}-500/10`}
                          >
                            <div className={`text-3xl font-bold ${actualItem.textColor} mb-2 animate-pulse`}>
                              {actualItem.value}
                            </div>
                            <div className="text-gray-300 font-medium">{actualItem.title}</div>
                            <div className="text-sm text-gray-400 mt-2">
                              {actualItem.title === "Podium Probability" ? actualItem.confidence : `Confidence: ${actualItem.confidence}%`}
                            </div>
                          </div>
                        );
                      })}
                    </StaggeredAnimation>

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
                          <Badge variant="outline" className={`${predictionApi.data.race <= predictionApi.data.qualifying ? 'text-green-400 border-green-400' : 'text-red-400 border-red-400'}`}>
                            {predictionApi.data.race <= predictionApi.data.qualifying ? 'Gains positions' : 'Loses positions'}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Overall Confidence</span>
                          <Badge variant="outline" className="text-blue-400 border-blue-400">
                            {Math.round(((predictionApi.data.qualifyingConfidence || 0.75) + (predictionApi.data.raceConfidence || 0.65)) / 2 * 100)}%
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : null}
            </DataWrapper>
          </AnimatedPageWrapper>
        </div>
      </div>
    </div>
  );
};

export default DriverPredictor;
