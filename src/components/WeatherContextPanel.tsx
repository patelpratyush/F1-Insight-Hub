import {
  Cloud,
  CloudRain,
  Droplets,
  Eye,
  Info,
  Sun,
  Thermometer,
  TrendingUp,
  Wind,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";

interface WeatherData {
  condition: string;
  temperature: number | null;
  humidity: number | null;
  wind_speed: number | null;
  track_temperature: number | null;
  rainfall: boolean | null;
}

interface WeatherContextData {
  success: boolean;
  race: string;
  session: string;
  weather: WeatherData;
  impact_analysis: {
    temperature_effect: string;
    wind_impact: string;
    grip_level: string;
    tire_strategy: string;
  };
  tire_strategy: {
    influence: string;
    recommendation: string;
  };
  driver_ratings: Record<string, number>;
  insights: {
    grip_level: string;
    performance_factors: string[];
  };
}

interface WeatherContextPanelProps {
  race: string;
  session: string;
  onUpdate?: (weatherData: WeatherContextData) => void;
}

const WeatherContextPanel: React.FC<WeatherContextPanelProps> = ({
  race,
  session,
  onUpdate,
}) => {
  const [weatherData, setWeatherData] = useState<WeatherContextData | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchWeatherContext = async () => {
    if (!race || !session) return;

    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/telemetry/weather-context`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          race,
          session,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to fetch weather context: ${response.statusText}`,
        );
      }

      const data = await response.json();
      setWeatherData(data);
      onUpdate?.(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch weather context",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWeatherContext();
  }, [race, session]);

  const getWeatherIcon = (condition: string) => {
    switch (condition.toLowerCase()) {
      case "wet":
      case "light rain":
        return <CloudRain className="h-5 w-5 text-blue-500" />;
      case "hot":
        return <Sun className="h-5 w-5 text-orange-500" />;
      case "cold":
        return <Cloud className="h-5 w-5 text-gray-500" />;
      default:
        return <Sun className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getConditionColor = (condition: string) => {
    switch (condition.toLowerCase()) {
      case "wet":
        return "bg-blue-100 text-blue-800";
      case "light rain":
        return "bg-blue-50 text-blue-700";
      case "hot":
        return "bg-orange-100 text-orange-800";
      case "cold":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-green-100 text-green-800";
    }
  };

  const getDriverRatingColor = (rating: number) => {
    if (rating >= 9) return "text-green-600 font-bold";
    if (rating >= 8) return "text-green-500";
    if (rating >= 7) return "text-yellow-600";
    return "text-red-500";
  };

  if (loading) {
    return (
      <Card className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent shadow-none rounded-[40px] overflow-hidden">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            Weather Context
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-sm text-gray-600">
              Loading weather data...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent shadow-none rounded-[40px] overflow-hidden text-center justify-center p-8">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2 justify-center">
            <Cloud className="h-5 w-5 text-gray-400" />
            Weather Context
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-600 text-sm mb-2">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchWeatherContext}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!weatherData) return null;

  const topDrivers = Object.entries(weatherData.driver_ratings)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <Card className="bg-transparent border-t border-l border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent shadow-none rounded-[40px] overflow-hidden">
      <CardHeader>
        <CardTitle className="text-white flex items-center space-x-2">
          {getWeatherIcon(weatherData.weather.condition)}
          <span>Weather Context</span>
        </CardTitle>
        <CardDescription className="text-gray-400 flex items-center justify-between">
          <span>
            {weatherData.race} • {weatherData.session}
          </span>
          <Badge className={getConditionColor(weatherData.weather.condition)}>
            {weatherData.weather.condition}
          </Badge>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Weather Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {weatherData.weather.temperature && (
            <div className="text-center p-4 bg-gradient-to-br from-red-600/20 to-red-800/20 rounded-lg border border-red-600/20">
              <Thermometer className="h-6 w-6 text-red-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-red-400">
                {weatherData.weather.temperature.toFixed(1)}°C
              </div>
              <div className="text-sm text-gray-300">Air Temp</div>
            </div>
          )}

          {weatherData.weather.track_temperature && (
            <div className="text-center p-4 bg-gradient-to-br from-orange-600/20 to-orange-800/20 rounded-lg border border-orange-600/20">
              <Thermometer className="h-6 w-6 text-orange-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-orange-400">
                {weatherData.weather.track_temperature.toFixed(1)}°C
              </div>
              <div className="text-sm text-gray-300">Track Temp</div>
            </div>
          )}

          {weatherData.weather.humidity && (
            <div className="text-center p-4 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-lg border border-blue-600/20">
              <Droplets className="h-6 w-6 text-blue-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-blue-400">
                {weatherData.weather.humidity.toFixed(0)}%
              </div>
              <div className="text-sm text-gray-300">Humidity</div>
            </div>
          )}

          {weatherData.weather.wind_speed && (
            <div className="text-center p-4 bg-gradient-to-br from-gray-600/20 to-gray-800/20 rounded-lg border border-gray-600/20">
              <Wind className="h-6 w-6 text-gray-400 mx-auto mb-2" />
              <div className="text-lg font-bold text-gray-400">
                {weatherData.weather.wind_speed.toFixed(1)} km/h
              </div>
              <div className="text-sm text-gray-300">Wind</div>
            </div>
          )}
        </div>

        {/* Impact Summary */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4 text-blue-400" />
            <span className="text-sm font-medium text-white">
              Track Conditions
            </span>
          </div>
          <p className="text-sm text-gray-300 bg-white/5 p-4 rounded-2xl">
            {weatherData.insights.grip_level}
          </p>
        </div>

        {/* Tire Strategy */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            <span className="text-sm font-medium text-white">
              Tire Strategy
            </span>
          </div>
          <div className="bg-green-500/10 border border-green-500/20 p-4 rounded-2xl space-y-1">
            <p className="text-sm font-medium text-green-400">
              {weatherData.tire_strategy.influence}
            </p>
            <p className="text-sm text-green-300">
              {weatherData.tire_strategy.recommendation}
            </p>
          </div>
        </div>

        {/* Expandable Driver Ratings */}
        <div className="space-y-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 w-full justify-start p-0 text-white hover:text-blue-400"
          >
            <Info className="h-4 w-4 text-blue-400" />
            Weather Performance Ratings
            <span className="text-xs text-gray-400 ml-auto">
              ({expanded ? "Hide" : "Show"})
            </span>
          </Button>

          {expanded && topDrivers.length > 0 && (
            <div className="bg-white/5 rounded-[24px] p-6">
              <div className="grid grid-cols-2 gap-4">
                {topDrivers.map(([driver, rating]) => (
                  <div
                    key={driver}
                    className="flex justify-between items-center bg-white/5 px-4 py-3 rounded-full border border-white/5"
                  >
                    <span className="text-sm font-semibold text-white">
                      {driver}
                    </span>
                    <span
                      className={`text-sm font-bold ${getDriverRatingColor(rating)}`}
                    >
                      {rating.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Performance Factors */}
        {expanded && (
          <div className="space-y-3">
            <div className="bg-white/5 rounded-[24px] p-6">
              <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-yellow-400" />
                Performance Factors
              </h4>
              <div className="space-y-3">
                {weatherData.insights.performance_factors.map(
                  (factor, index) => (
                    <div
                      key={index}
                      className="text-sm text-gray-300 bg-white/5 p-4 rounded-xl border border-white/5 border-l-4 border-l-yellow-400"
                    >
                      {factor}
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WeatherContextPanel;
