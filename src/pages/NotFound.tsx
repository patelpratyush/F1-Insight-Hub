import { useLocation, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Home, ArrowLeft } from "lucide-react";
import AnimatedPageWrapper from "@/components/AnimatedPageWrapper";

const NotFound = () => {
  const location = useLocation();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex items-center justify-center p-6 overflow-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -right-4 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-8 w-64 h-64 bg-yellow-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto">
        <AnimatedPageWrapper delay={100}>
          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="text-center p-12">
              <div className={`transition-all duration-1000 delay-300 transform ${
                isVisible ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-8 opacity-0 scale-95'
              }`}>
                <div className="p-4 bg-red-600/20 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                  <AlertTriangle className="h-10 w-10 text-red-400 animate-pulse" />
                </div>
                
                <h1 className="text-6xl font-bold text-red-400 mb-4 animate-pulse">
                  404
                </h1>
                
                <h2 className="text-2xl font-semibold text-white mb-4">
                  Page Not Found
                </h2>
                
                <p className="text-gray-400 text-lg mb-2">
                  The page you're looking for doesn't exist in our F1 analytics platform.
                </p>
                
                <p className="text-sm text-gray-500 mb-8">
                  Route: <code className="bg-gray-700 px-2 py-1 rounded">{location.pathname}</code>
                </p>
              </div>

              <div className={`flex flex-col sm:flex-row gap-4 justify-center transition-all duration-1000 delay-700 transform ${
                isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
              }`}>
                <Link to="/">
                  <Button 
                    size="lg"
                    className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 transform transition-all duration-300 hover:scale-105"
                  >
                    <Home className="mr-2 h-5 w-5" />
                    Back to Home
                  </Button>
                </Link>
                
                <Button 
                  variant="outline"
                  size="lg"
                  onClick={() => window.history.back()}
                  className="border-gray-600 text-gray-300 hover:text-white hover:bg-gray-700 px-8 py-3 transform transition-all duration-300 hover:scale-105"
                >
                  <ArrowLeft className="mr-2 h-5 w-5" />
                  Go Back
                </Button>
              </div>

              <div className={`mt-8 text-xs text-gray-500 transition-all duration-1000 delay-1000 transform ${
                isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
              }`}>
                🏎️ F1 Insight Hub - Advanced Formula 1 Analytics
              </div>
            </CardContent>
          </Card>
        </AnimatedPageWrapper>
      </div>
    </div>
  );
};

export default NotFound;
