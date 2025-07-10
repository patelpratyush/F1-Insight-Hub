
import { Link } from "react-router-dom";
import { Trophy, TrendingUp, Activity, Zap, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const Index = () => {
  const modules = [
    {
      title: "Driver Performance Predictor",
      description: "Predict how a selected driver will perform in the next race based on historical data",
      icon: Trophy,
      color: "from-red-500 to-red-600",
      features: ["Qualifying position prediction", "Podium probability", "Historical analysis"],
      path: "/predictor"
    },
    {
      title: "Race Result Predictor",
      description: "Predict final positions for all drivers in an upcoming race",
      icon: TrendingUp,
      color: "from-blue-500 to-blue-600",
      features: ["Full grid predictions", "Confidence scores", "Weather impact analysis"],
      path: "/race-predictor"
    },
    {
      title: "Telemetry Data Analyzer",
      description: "Analyze and visualize telemetry data for drivers in any session",
      icon: Activity,
      color: "from-green-500 to-green-600",
      features: ["Lap-by-lap analysis", "Driver comparisons", "Real-time visualizations"],
      path: "/telemetry"
    },
    {
      title: "Race Strategy Simulator",
      description: "Simulate different pit stop strategies and compare outcomes",
      icon: Zap,
      color: "from-purple-500 to-purple-600",
      features: ["Pit stop optimization", "Tire strategy analysis", "Monte Carlo simulation"],
      path: "/strategy"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-600/20 to-transparent"></div>
        <div className="container mx-auto px-6 py-20">
          <div className="text-center space-y-6">
            <div className="inline-flex items-center space-x-2 bg-red-600/10 px-4 py-2 rounded-full border border-red-600/20">
              <Trophy className="h-5 w-5 text-red-500" />
              <span className="text-sm font-medium text-red-400">Formula 1 Analytics</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-white via-red-200 to-red-400 bg-clip-text text-transparent">
              F1 Insight Hub
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
              Advanced Formula 1 analytics platform powered by machine learning and real-time telemetry data
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-6">
              <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white px-8 py-6 text-lg">
                Get Started
                <ChevronRight className="ml-2 h-5 w-5" />
              </Button>
              <div className="text-sm text-gray-400">
                Powered by Fast-F1 • Real-time data • ML predictions
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modules Grid */}
      <div className="container mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Analytics Modules
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Four powerful tools to analyze and predict Formula 1 performance
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {modules.map((module, index) => {
            const Icon = module.icon;
            return (
              <Link key={index} to={module.path} className="group">
                <Card className="bg-gray-800/50 border-gray-700 hover:border-red-500/50 transition-all duration-300 hover:scale-105 h-full backdrop-blur-sm">
                  <CardHeader className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className={`p-3 rounded-lg bg-gradient-to-r ${module.color} shadow-lg`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-red-400 transition-colors" />
                    </div>
                    <CardTitle className="text-xl text-white group-hover:text-red-400 transition-colors">
                      {module.title}
                    </CardTitle>
                    <CardDescription className="text-gray-300 text-base leading-relaxed">
                      {module.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {module.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center text-gray-400 text-sm">
                          <div className="w-1.5 h-1.5 bg-red-500 rounded-full mr-3"></div>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-gray-800/30 backdrop-blur-sm border-y border-gray-700">
        <div className="container mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
            <div className="space-y-2">
              <div className="text-3xl font-bold text-red-400">20+</div>
              <div className="text-gray-400">Racing Seasons</div>
            </div>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-red-400">400+</div>
              <div className="text-gray-400">Grand Prix</div>
            </div>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-red-400">10</div>
              <div className="text-gray-400">Racing Teams</div>
            </div>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-red-400">Real-time</div>
              <div className="text-gray-400">Data Analysis</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
