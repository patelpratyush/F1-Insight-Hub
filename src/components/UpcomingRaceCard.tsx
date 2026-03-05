import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, MapPin, Clock, Flag } from "lucide-react";
import { Link } from "react-router-dom";
import { useTracks } from "@/hooks/useF1Metadata";
import {
  formatRaceDate,
  getCurrentSeasonYear,
} from "@/lib/season";

export const UpcomingRaceCard = () => {
  const [timeLeft, setTimeLeft] = useState("");
  const currentYear = getCurrentSeasonYear();
  const { data: tracks } = useTracks(currentYear);

  const nextRace = (() => {
    if (!tracks?.length) return null;
    const now = new Date();
    return tracks.find((t) => new Date(t.date) > now) || tracks[0];
  })();

  useEffect(() => {
    if (!nextRace) return;

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
    const timer = setInterval(calculateTimeLeft, 60000);
    return () => clearInterval(timer);
  }, [nextRace]);

  if (!nextRace) return null;

  return (
    <Card className="w-full max-w-2xl mx-auto bg-gradient-to-br from-background to-muted/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5" />
            Next Race
          </CardTitle>
          <Badge variant="secondary">{currentYear} Season</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-bold">{nextRace.race_name}</h3>
          <div className="flex items-center justify-center gap-4 text-muted-foreground">
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span>{nextRace.location}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>{formatRaceDate(nextRace.date)}</span>
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
