
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Zap, Clock, Gauge, Target, Timer, TrendingUp } from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";
import StaggeredAnimation from "@/components/StaggeredAnimation";

const StrategySimulator = () => {
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedTrack, setSelectedTrack] = useState("");
  const [tireStrategy, setTireStrategy] = useState("");
  const [safetyCarProbability, setSafetyCarProbability] = useState([30]);
  const [weather, setWeather] = useState("");
  const [simulation, setSimulation] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const drivers = ["VER", "LEC", "HAM", "RUS", "PER", "SAI", "NOR", "PIA"];
  const tracks = ["Monaco", "Silverstone", "Monza", "Spa-Francorchamps", "Suzuka"];
  const strategies = [
    "Soft-Medium-Hard",
    "Medium-Hard-Hard", 
    "Soft-Soft-Medium",
    "Medium-Medium-Hard",
    "Hard-Hard-Medium"
  ];

  const handleSimulate = () => {
    // Mock simulation results
    const totalTime = "1:42:35.678";
    const stints = [
      { stint: 1, tire: "Soft", laps: 15, avgLapTime: "1:24.5", degradation: "High" },
      { stint: 2, tire: "Medium", laps: 25, avgLapTime: "1:25.2", degradation: "Medium" },
      { stint: 3, tire: "Hard", laps: 18, avgLapTime: "1:26.1", degradation: "Low" }
    ];
    
    setSimulation({
      totalTime,
      stints,
      position: 3,
      efficiency: 85
    });
  };

  const getTireColor = (tire) => {
    switch(tire) {
      case "Soft": return "bg-red-500";
      case "Medium": return "bg-yellow-500"; 
      case "Hard": return "bg-white";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-yellow-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="container mx-auto max-w-7xl relative z-10">
        {/* Header */}
        <AnimatedPageWrapper delay={100}>
          <div className="mb-8">
            <div className={`flex items-center space-x-3 mb-4 transition-all duration-1000 delay-300 transform ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'
            }`}>
              <div className="p-3 bg-purple-600 rounded-lg shadow-lg hover:shadow-purple-500/25 transition-all duration-300 hover:scale-110">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">Race Strategy Simulator</h1>
            </div>
            <div className={`transition-all duration-1000 delay-500 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
            }`}>
              <p className="text-gray-400 text-lg">
                Simulate different pit stop strategies and compare outcomes using advanced race modeling algorithms.
              </p>
              <div className="mt-2 text-sm text-gray-500">
                ⚡ Strategy optimization • 🏁 Pit stop timing • 🛞 Tire degradation modeling
              </div>
            </div>
          </div>
        </AnimatedPageWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Strategy Configuration */}
          <AnimatedPageWrapper delay={600} className="lg:col-span-1 space-y-6">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Target className="h-5 w-5 text-purple-500" />
                  <span>Strategy Setup</span>
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Configure race parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Track</label>
                  <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select track" />
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">Tire Strategy</label>
                  <Select value={tireStrategy} onValueChange={setTireStrategy}>
                    <SelectTrigger className="bg-gray-700 border-gray-600 text-white">
                      <SelectValue placeholder="Select strategy" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-700 border-gray-600">
                      {strategies.map((strategy) => (
                        <SelectItem key={strategy} value={strategy} className="text-white hover:bg-gray-600">
                          {strategy}
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

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-300">Safety Car Probability</label>
                  <div className="px-2">
                    <Slider
                      value={safetyCarProbability}
                      onValueChange={setSafetyCarProbability}
                      max={100}
                      step={5}
                      className="w-full"
                    />
                  </div>
                  <div className="text-center text-sm text-gray-400">{safetyCarProbability[0]}%</div>
                </div>

                <Button 
                  onClick={handleSimulate}
                  disabled={!selectedDriver || !selectedTrack || !tireStrategy || !weather}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white mt-6"
                  size="lg"
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Run Simulation
                </Button>
              </CardContent>
            </Card>
          </AnimatedPageWrapper>

          {/* Simulation Results */}
          <AnimatedPageWrapper delay={800} className="lg:col-span-3">
            {simulation ? (
              <div className="space-y-6">
                {/* Overview Stats */}
                <StaggeredAnimation
                  delay={300}
                  staggerDelay={150}
                  className="grid grid-cols-1 md:grid-cols-4 gap-4"
                >
                  {[
                  <Card key="time" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Clock className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-blue-400">{simulation.totalTime}</div>
                      <div className="text-sm text-gray-300">Total Race Time</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="position" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Target className="h-6 w-6 text-green-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-green-400">P{simulation.position}</div>
                      <div className="text-sm text-gray-300">Predicted Position</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="efficiency" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <TrendingUp className="h-6 w-6 text-purple-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-purple-400">{simulation.efficiency}%</div>
                      <div className="text-sm text-gray-300">Strategy Efficiency</div>
                    </CardContent>
                  </Card>,
                  
                  <Card key="pitstops" className="bg-gray-800/50 border-gray-700">
                    <CardContent className="p-4 text-center">
                      <Gauge className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                      <div className="text-lg font-bold text-yellow-400">3</div>
                      <div className="text-sm text-gray-300">Pit Stops</div>
                    </CardContent>
                  </Card>
                  ]}
                </StaggeredAnimation>

                {/* Stint Breakdown */}
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <Timer className="h-5 w-5 text-purple-500" />
                      <span>Stint Analysis</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Detailed breakdown of each racing stint
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {simulation.stints.map((stint, index) => (
                        <div key={index} className="flex items-center p-4 bg-gray-700/30 rounded-lg">
                          <div className="flex items-center space-x-4 flex-1">
                            <div className="text-center">
                              <div className="text-sm text-gray-400">Stint</div>
                              <div className="text-lg font-bold text-white">{stint.stint}</div>
                            </div>
                            
                            <div className={`w-4 h-4 rounded-full ${getTireColor(stint.tire)}`}></div>
                            <div>
                              <div className="font-medium text-white">{stint.tire} Compound</div>
                              <div className="text-sm text-gray-400">{stint.laps} laps</div>
                            </div>
                          </div>
                          
                          <div className="text-right space-y-1">
                            <div className="text-white font-medium">{stint.avgLapTime}</div>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${
                                stint.degradation === 'High' ? 'text-red-400 border-red-400' :
                                stint.degradation === 'Medium' ? 'text-yellow-400 border-yellow-400' :
                                'text-green-400 border-green-400'
                              }`}
                            >
                              {stint.degradation} Deg
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Strategy Timeline */}
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white">Strategy Timeline</CardTitle>
                    <CardDescription className="text-gray-400">
                      Visual representation of pit stops and tire changes
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-32 bg-gray-700/30 rounded-lg flex items-center justify-center">
                      <div className="text-center">
                        <Timer className="h-12 w-12 text-gray-500 mx-auto mb-2" />
                        <div className="text-gray-400">Timeline Visualization</div>
                        <div className="text-sm text-gray-500">Interactive stint timeline would be displayed here</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-gray-800/50 border-gray-700 h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <Zap className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <CardTitle className="text-gray-400 mb-2">No Simulation Run</CardTitle>
                  <CardDescription className="text-gray-500">
                    Configure your strategy parameters and run a simulation to see predicted outcomes.
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

export default StrategySimulator;
