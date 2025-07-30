
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Flag, Timer, Zap, Users, Trophy, Loader2 } from "lucide-react";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorDisplay from "@/components/ui/error-display";
import DataWrapper from "@/components/ui/data-wrapper";
import useApiCall from "@/hooks/useApiCall";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";
import { trackOptions } from "@/data/tracks2025";

const RacePredictor = () => {
  const [selectedTrack, setSelectedTrack] = useState("");
  const [weather, setWeather] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [inputError, setInputError] = useState("");

  useEffect(() => {
    setIsVisible(true);
  }, []);

  // Use centralized track data - all 2025 F1 tracks with circuit details
  const tracks = trackOptions;

  const weatherConditions = [
    { value: "clear", label: "Clear", description: "Normal dry race, fastest pace", color: "bg-yellow-500" },
    { value: "overcast", label: "Overcast", description: "Cooler track, moderate grip", color: "bg-gray-400" },
    { value: "light_rain", label: "Light Rain", description: "Intermediate tires, variable grip", color: "bg-blue-400" },
    { value: "heavy_rain", label: "Heavy Rain", description: "Full wets, slow pace, higher risk", color: "bg-blue-600" },
    { value: "mixed", label: "Mixed Conditions", description: "Switching between dry and wet", color: "bg-purple-500" }
  ];

  // Realistic 2025 season driver performance based on current championship standings
  const getRealisticRacePredictions = () => {
    const drivers = [
      // McLaren - Currently dominating 
      { code: 'PIA', name: 'Oscar Piastri', team: 'McLaren', basePerf: 95, consistency: 90 },
      { code: 'NOR', name: 'Lando Norris', team: 'McLaren', basePerf: 93, consistency: 88 },
      
      // Red Bull - Still strong but not dominant
      { code: 'VER', name: 'Max Verstappen', team: 'Red Bull Racing', basePerf: 92, consistency: 95 },
      { code: 'TSU', name: 'Yuki Tsunoda', team: 'Red Bull Racing', basePerf: 82, consistency: 75 },
      
      // Mercedes - Competitive 
      { code: 'RUS', name: 'George Russell', team: 'Mercedes', basePerf: 87, consistency: 85 },
      { code: 'ANT', name: 'Andrea Kimi Antonelli', team: 'Mercedes', basePerf: 78, consistency: 70 },
      
      // Ferrari - Mid-pack
      { code: 'LEC', name: 'Charles Leclerc', team: 'Ferrari', basePerf: 85, consistency: 82 },
      { code: 'HAM', name: 'Lewis Hamilton', team: 'Ferrari', basePerf: 83, consistency: 88 },
      
      // Williams - Decent midfield
      { code: 'ALB', name: 'Alexander Albon', team: 'Williams', basePerf: 75, consistency: 80 },
      { code: 'SAI', name: 'Carlos Sainz', team: 'Williams', basePerf: 77, consistency: 85 },
      
      // Aston Martin - Struggling (realistic for 2025)
      { code: 'STR', name: 'Lance Stroll', team: 'Aston Martin', basePerf: 65, consistency: 65 },
      { code: 'ALO', name: 'Fernando Alonso', team: 'Aston Martin', basePerf: 68, consistency: 82 },
      
      // Other teams
      { code: 'GAS', name: 'Pierre Gasly', team: 'Alpine', basePerf: 72, consistency: 75 },
      { code: 'COL', name: 'Franco Colapinto', team: 'Alpine', basePerf: 70, consistency: 65 },
      { code: 'OCO', name: 'Esteban Ocon', team: 'Haas', basePerf: 71, consistency: 73 },
      { code: 'BEA', name: 'Oliver Bearman', team: 'Haas', basePerf: 69, consistency: 68 },
      { code: 'HUL', name: 'Nico Hulkenberg', team: 'Kick Sauber', basePerf: 74, consistency: 78 },
      { code: 'BOR', name: 'Gabriel Bortoleto', team: 'Kick Sauber', basePerf: 67, consistency: 70 },
      { code: 'HAD', name: 'Isack Hadjar', team: 'Racing Bulls', basePerf: 70, consistency: 72 },
      { code: 'LAW', name: 'Liam Lawson', team: 'Racing Bulls', basePerf: 72, consistency: 74 }
    ];

    // Apply weather and track modifiers
    const weatherModifiers = {
      'clear': { skill: 1.0, consistency: 1.0 },
      'overcast': { skill: 0.98, consistency: 1.02 },
      'light_rain': { skill: 1.1, consistency: 0.8 }, // Skill drivers benefit
      'heavy_rain': { skill: 1.2, consistency: 0.6 }, // Even more skill-dependent
      'mixed': { skill: 1.05, consistency: 0.9 }
    };

    const weatherMod = weatherModifiers[weather] || weatherModifiers['clear'];
    
    // Calculate performance with randomness for realistic variation
    const predictions = drivers.map(driver => {
      const weatherAdjustedPerf = driver.basePerf * weatherMod.skill;
      const consistencyFactor = driver.consistency * weatherMod.consistency;
      
      // Add realistic randomness (±5 points variation)
      const randomFactor = (Math.random() - 0.5) * 10;
      const finalPerf = Math.max(0, Math.min(100, weatherAdjustedPerf + randomFactor));
      
      // Confidence based on consistency and conditions
      const confidence = Math.round(Math.min(95, consistencyFactor + (weather === 'clear' ? 10 : -5)));
      
      return {
        ...driver,
        performance: finalPerf,
        confidence: confidence
      };
    });

    // Sort by performance and assign positions
    const sortedPredictions = predictions
      .sort((a, b) => b.performance - a.performance)
      .map((driver, index) => ({
        pos: index + 1,
        driver: driver.code,
        name: driver.name,
        team: driver.team,
        confidence: driver.confidence,
        gap: index === 0 ? '0.000' : `+${(Math.random() * 30 + index * 2).toFixed(3)}`
      }));

    return {
      predictions: sortedPredictions,
      statistics: {
        average_confidence: Math.round(predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length),
        fastest_lap: { driver: sortedPredictions[Math.floor(Math.random() * 3)].driver, time: '1:24.567' },
        average_gap: '12.4'
      }
    };
  };

  // API call for race prediction with improved backend
  const raceApi = useApiCall(async () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/predict/race`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        race_name: selectedTrack,
        weather: weather,
        temperature: weather === 'clear' ? 25.0 : weather === 'overcast' ? 20.0 : 18.0
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: Failed to generate race predictions`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Race prediction failed');
    }
    
    // Transform API response to match UI expectations
    const transformedPredictions = data.predictions.map((pred, index) => ({
      pos: pred.predicted_position,
      driver: pred.driver_code,
      name: pred.driver_name,
      team: pred.team.replace(' Honda RBPT', '').replace(' Mercedes', '').replace('Scuderia ', '').replace('BWT ', '').replace(' Aramco Mercedes', '').replace('Visa Cash App RB F1 Team', 'RB').replace('MoneyGram Haas F1 Team', 'Haas').replace('Kick Sauber F1 Team', 'Kick Sauber'),
      confidence: Math.round(pred.confidence),
      gap: pred.gap_to_winner
    }));
    
    return {
      predictions: transformedPredictions,
      statistics: data.statistics
    };
  }, { maxRetries: 2, retryDelay: 2000 });

  const handlePredict = () => {
    // Input validation
    if (!selectedTrack || !weather) {
      setInputError("Please select both track and weather conditions");
      return;
    }
    
    setInputError("");
    raceApi.execute();
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-6xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
            <div className="mb-8">
              <div className={`flex items-center space-x-3 mb-4 transition-all duration-1000 delay-300 transform ${
                isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
              }`}>
                <div className="p-3 bg-blue-600 rounded-lg shadow-lg hover:shadow-blue-500/25 transition-all duration-300 hover:scale-110">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-white">Race Result Predictor</h1>
              </div>
              <div className={`transition-all duration-1000 delay-500 transform ${
                isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
              }`}>
                <p className="text-gray-400 text-lg">
                  Predict final positions for all drivers in an upcoming race based on qualifying results and race conditions.
                </p>
                <div className="mt-2 text-sm text-gray-500">
                  🏎️ ML-powered predictions • 20 drivers • Real-time analysis
                </div>
              </div>
            </div>
          </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Input Section */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-1">
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
                        <SelectItem key={track.name} value={track.name} className="text-white hover:bg-gray-600">
                          {track.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weather</label>
                  <Select value={weather} onValueChange={setWeather}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select weather">
                        {weather && weatherConditions.find(w => w.value === weather) && (
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${weatherConditions.find(w => w.value === weather)?.color} flex-shrink-0`}></div>
                            <span>{weatherConditions.find(w => w.value === weather)?.label}</span>
                          </div>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600 min-w-[280px] max-h-[300px] z-50">
                      {weatherConditions.map((condition) => (
                        <SelectItem key={condition.value} value={condition.value} className="text-white hover:bg-gray-600 py-3">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${condition.color} flex-shrink-0`}></div>
                            <div className="flex flex-col">
                              <span className="font-medium">{condition.label}</span>
                              <span className="text-xs text-gray-400">{condition.description}</span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
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
                  disabled={!selectedTrack || !weather || raceApi.loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-6"
                  size="lg"
                >
                  {raceApi.loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Predicting...
                    </>
                  ) : (
                    <>
                      <Zap className="mr-2 h-4 w-4" />
                      Predict Results
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Results Section */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-3">
            <DataWrapper
              loading={raceApi.loading}
              error={raceApi.error}
              data={raceApi.data}
              onRetry={raceApi.retry}
              isRetrying={raceApi.isRetrying}
              loadingMessage="Generating race predictions for entire grid..."
              errorTitle="Race Prediction Failed"
              errorVariant="card"
              minHeight="min-h-96"
              fallbackContent={
                <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                  <CardContent className="text-center">
                    <Flag className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                    <CardTitle className="text-gray-400 mb-2">No Race Predictions</CardTitle>
                    <CardDescription className="text-gray-500">
                      Select a track and weather conditions to generate AI-powered race predictions for the entire grid.
                    </CardDescription>
                  </CardContent>
                </Card>
              }
            >
            {raceApi.data?.predictions ? (
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
                  <StaggeredAnimation
                    delay={300}
                    staggerDelay={100}
                    className="space-y-3"
                  >
                    {raceApi.data.predictions.map((driver, index) => (
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
                  </StaggeredAnimation>

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 rounded-lg border border-yellow-600/20">
                      <Users className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-yellow-400">20</div>
                      <div className="text-sm text-gray-300">Drivers</div>
                    </div>
                    
                    <div className="text-center p-4 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-lg border border-green-600/20">
                      <Timer className="h-6 w-6 text-green-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-green-400">{raceApi.data?.statistics?.average_confidence || 87}%</div>
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
            ) : null}
            </DataWrapper>
          </AnimatedPageWrapper>
        </div>
      </div>
    </div>
  );
};

export default RacePredictor;
