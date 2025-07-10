import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, MapPin, Clock, Flag } from "lucide-react";
import { Link } from "react-router-dom";
import { races2025 } from "./RaceSelect";

export const UpcomingRaceCard = () => {
  const [timeLeft, setTimeLeft] = useState("");
  const [nextRace, setNextRace] = useState(races2025[0]);

  useEffect(() => {
    // Find the next upcoming race
    const now = new Date();
    const upcoming = races2025.find(race => new Date(race.date) > now) || races2025[0];
    setNextRace(upcoming);
  }, []);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date();
      const raceDate = new Date(nextRace.date);
      const difference = raceDate.getTime() - now.getTime();

      if (difference > 0) {
        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((difference / 1000 / 60) % 60);
        
        setTimeLeft(`${days}d ${hours}h ${minutes}m`);
      } else {
        setTimeLeft("Race in progress or completed");
      }
    };

    calculateTimeLeft();
    const timer = setInterval(calculateTimeLeft, 60000); // Update every minute

    return () => clearInterval(timer);
  }, [nextRace]);

  return (
    <Card className="w-full max-w-2xl mx-auto bg-gradient-to-br from-background to-muted/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5" />
            Next Race
          </CardTitle>
          <Badge variant="secondary">2025 Season</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-bold">{nextRace.name}</h3>
          <div className="flex items-center justify-center gap-4 text-muted-foreground">
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span>{nextRace.location}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{new Date(nextRace.date).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="text-center p-4 bg-primary/10 rounded-lg">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Clock className="h-5 w-5" />
            <span className="font-medium">Time Until Race</span>
          </div>
          <div className="text-3xl font-bold text-primary">{timeLeft}</div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button asChild className="flex-1">
            <Link to="/predictor">
              Predict Driver Performance
            </Link>
          </Button>
          <Button asChild variant="outline" className="flex-1">
            <Link to="/race-predictor">
              Predict Race Results
            </Link>
          </Button>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button asChild variant="secondary" className="flex-1">
            <Link to="/telemetry">
              Analyze Telemetry
            </Link>
          </Button>
          <Button asChild variant="secondary" className="flex-1">
            <Link to="/strategy">
              Simulate Strategy
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};