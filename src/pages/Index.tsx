
import { Link, useNavigate } from "react-router-dom";
import { Trophy, TrendingUp, Activity, Zap, ChevronRight, BarChart3, Users, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useState, useEffect } from "react";

const Index = () => {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [activeCard, setActiveCard] = useState<number | null>(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleGetStarted = () => {
    navigate('/telemetry');
  };

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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-600/20 to-transparent"></div>
        <div className="container mx-auto px-6 py-20 relative z-10">
          <div className={`text-center space-y-8 transition-all duration-1000 transform ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
          }`}>
            <div className={`inline-flex items-center space-x-2 bg-red-600/10 px-4 py-2 rounded-full border border-red-600/20 transition-all duration-700 delay-300 transform ${
              isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
            }`}>
              <Trophy className="h-5 w-5 text-red-500 animate-pulse" />
              <span className="text-sm font-medium text-red-400">Formula 1 Analytics</span>
            </div>
            
            <h1 className={`text-5xl md:text-7xl font-bold bg-gradient-to-r from-white via-red-200 to-red-400 bg-clip-text text-transparent transition-all duration-1000 delay-500 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
            }`}>
              F1 Insight Hub
            </h1>
            
            <p className={`text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed transition-all duration-1000 delay-700 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
            }`}>
              Advanced Formula 1 analytics platform powered by machine learning and real-time telemetry data
            </p>
            
            <div className={`flex flex-col sm:flex-row gap-6 justify-center items-center pt-8 transition-all duration-1000 delay-1000 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
            }`}>
              <Button 
                size="lg" 
                onClick={handleGetStarted}
                className="bg-red-600 hover:bg-red-700 text-white px-8 py-6 text-lg font-semibold transform transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-red-500/25 relative overflow-hidden group"
              >
                <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-red-500 to-red-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                <span className="relative flex items-center">
                  Get Started
                  <ChevronRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                </span>
              </Button>
              
              <Link to="/predictor">
                <Button 
                  variant="outline" 
                  size="lg"
                  className="border-red-600/50 text-red-400 hover:text-white hover:bg-red-600 hover:border-red-500 px-8 py-6 text-lg font-semibold transform transition-all duration-300 hover:scale-105 backdrop-blur-sm"
                >
                  View Demo
                </Button>
              </Link>
            </div>
            
            <div className={`flex flex-wrap justify-center gap-8 text-sm text-gray-400 pt-6 transition-all duration-1000 delay-1200 transform ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
            }`}>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-red-400" />
                <span>Powered by Fast-F1</span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-blue-400" />
                <span>Real-time data</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-green-400" />
                <span>ML predictions</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modules Grid */}
      <div className="container mx-auto px-6 py-16 relative z-10">
        <div className={`text-center mb-16 transition-all duration-1000 delay-300 transform ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
        }`}>
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
              <div
                key={index}
                className={`transition-all duration-700 transform ${
                  isVisible 
                    ? 'translate-y-0 opacity-100' 
                    : 'translate-y-12 opacity-0'
                }`}
                style={{ transitionDelay: `${800 + index * 200}ms` }}
                onMouseEnter={() => setActiveCard(index)}
                onMouseLeave={() => setActiveCard(null)}
              >
                <Link to={module.path} className="group block">
                  <Card className={`bg-gray-800/50 border-gray-700 hover:border-red-500/50 transition-all duration-300 h-full backdrop-blur-sm relative overflow-hidden transform ${
                    activeCard === index ? 'scale-105 shadow-2xl shadow-red-500/10' : 'hover:scale-102'
                  }`}>
                    {/* Animated background gradient */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${module.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}></div>
                    
                    <CardHeader className="space-y-4 relative z-10">
                      <div className="flex items-center justify-between">
                        <div className={`p-3 rounded-lg bg-gradient-to-r ${module.color} shadow-lg transform transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-red-400 transition-all duration-300 group-hover:translate-x-1" />
                      </div>
                      <CardTitle className="text-xl text-white group-hover:text-red-400 transition-colors duration-300">
                        {module.title}
                      </CardTitle>
                      <CardDescription className="text-gray-300 text-base leading-relaxed group-hover:text-gray-200 transition-colors duration-300">
                        {module.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="relative z-10">
                      <ul className="space-y-3">
                        {module.features.map((feature, featureIndex) => (
                          <li key={featureIndex} className="flex items-center text-gray-400 text-sm group-hover:text-gray-300 transition-colors duration-300">
                            <div className={`w-1.5 h-1.5 bg-red-500 rounded-full mr-3 transform transition-all duration-300 ${
                              activeCard === index ? 'scale-125 bg-red-400' : ''
                            }`}></div>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </Link>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-gray-800/30 backdrop-blur-sm border-y border-gray-700 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-600/5 via-transparent to-blue-600/5"></div>
        <div className="container mx-auto px-6 py-16 relative z-10">
          <div className={`text-center mb-12 transition-all duration-1000 delay-200 transform ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
          }`}>
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-3">
              Trusted by F1 Enthusiasts Worldwide
            </h3>
            <p className="text-gray-400">Comprehensive data coverage and analysis</p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: "20+", label: "Racing Seasons", delay: "400ms" },
              { value: "400+", label: "Grand Prix", delay: "600ms" },
              { value: "10", label: "Racing Teams", delay: "800ms" },
              { value: "Real-time", label: "Data Analysis", delay: "1000ms" }
            ].map((stat, index) => (
              <div
                key={index}
                className={`text-center space-y-3 p-6 rounded-lg bg-gray-800/20 backdrop-blur-sm border border-gray-700/50 hover:border-red-500/30 transition-all duration-500 transform hover:scale-105 ${
                  isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
                }`}
                style={{ transitionDelay: stat.delay }}
              >
                <div className="text-3xl md:text-4xl font-bold text-red-400 animate-pulse">
                  {stat.value}
                </div>
                <div className="text-gray-400 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Call to Action Section */}
      <div className="container mx-auto px-6 py-20 text-center relative z-10">
        <div className={`max-w-4xl mx-auto space-y-8 transition-all duration-1000 delay-600 transform ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
        }`}>
          <h2 className="text-3xl md:text-5xl font-bold text-white">
            Ready to dive into
            <span className="bg-gradient-to-r from-red-400 to-red-600 bg-clip-text text-transparent"> F1 Analytics</span>?
          </h2>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Start exploring advanced telemetry data, race predictions, and performance analytics today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              size="lg"
              onClick={handleGetStarted}
              className="bg-red-600 hover:bg-red-700 text-white px-10 py-4 text-lg font-semibold transform transition-all duration-300 hover:scale-105 hover:shadow-xl group"
            >
              Start Your Analysis
              <ChevronRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
            <Link to="/predictor">
              <Button 
                variant="outline" 
                size="lg"
                className="border-red-600/50 text-red-400 hover:text-white hover:bg-red-600 hover:border-red-500 px-10 py-4 text-lg font-semibold transform transition-all duration-300 hover:scale-105 backdrop-blur-sm"
              >
                Explore Features
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
