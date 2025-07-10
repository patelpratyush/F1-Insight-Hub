import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RaceSelect } from "./RaceSelect";
import { DriverSelect } from "./DriverSelect";
import { Loader2, TrendingUp } from "lucide-react";
import { toast } from "sonner";

interface PredictionFormProps {
  title: string;
  onPredict: (data: PredictionData) => Promise<void>;
  isLoading?: boolean;
}

export interface PredictionData {
  race: string;
  driver: string;
  weather: string;
  tireStrategy: string;
}

export const PredictionForm = ({ title, onPredict, isLoading = false }: PredictionFormProps) => {
  const [race, setRace] = useState("");
  const [driver, setDriver] = useState("");
  const [weather, setWeather] = useState("");
  const [tireStrategy, setTireStrategy] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!race || !driver || !weather || !tireStrategy) {
      toast.error("Please fill in all fields");
      return;
    }

    const data: PredictionData = {
      race,
      driver,
      weather,
      tireStrategy,
    };

    try {
      await onPredict(data);
      toast.success("Prediction generated successfully!");
    } catch (error) {
      toast.error("Failed to generate prediction");
      console.error("Prediction error:", error);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="race">Grand Prix</Label>
            <RaceSelect 
              value={race} 
              onValueChange={setRace}
              placeholder="Select a 2025 Grand Prix"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="driver">Driver</Label>
            <DriverSelect 
              value={driver} 
              onValueChange={setDriver}
              placeholder="Select a driver"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="weather">Weather Conditions</Label>
            <Select value={weather} onValueChange={setWeather}>
              <SelectTrigger>
                <SelectValue placeholder="Select weather conditions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dry">Dry</SelectItem>
                <SelectItem value="wet">Wet</SelectItem>
                <SelectItem value="mixed">Mixed</SelectItem>
                <SelectItem value="overcast">Overcast</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tire-strategy">Tire Strategy</Label>
            <Select value={tireStrategy} onValueChange={setTireStrategy}>
              <SelectTrigger>
                <SelectValue placeholder="Select tire strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="soft-medium-hard">Soft-Medium-Hard</SelectItem>
                <SelectItem value="medium-hard">Medium-Hard</SelectItem>
                <SelectItem value="soft-hard">Soft-Hard</SelectItem>
                <SelectItem value="hard-medium">Hard-Medium</SelectItem>
                <SelectItem value="one-stop-hard">One Stop (Hard)</SelectItem>
                <SelectItem value="one-stop-medium">One Stop (Medium)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={isLoading}
            size="lg"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating Prediction...
              </>
            ) : (
              "Generate Prediction"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};