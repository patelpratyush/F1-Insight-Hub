import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const races2025 = [
  { id: "bahrain", name: "Bahrain Grand Prix", date: "2025-03-16", location: "Sakhir" },
  { id: "saudi-arabia", name: "Saudi Arabian Grand Prix", date: "2025-03-23", location: "Jeddah" },
  { id: "australia", name: "Australian Grand Prix", date: "2025-04-06", location: "Melbourne" },
  { id: "china", name: "Chinese Grand Prix", date: "2025-04-20", location: "Shanghai" },
  { id: "miami", name: "Miami Grand Prix", date: "2025-05-04", location: "Miami" },
  { id: "emilia-romagna", name: "Emilia Romagna Grand Prix", date: "2025-05-18", location: "Imola" },
  { id: "monaco", name: "Monaco Grand Prix", date: "2025-05-25", location: "Monte Carlo" },
  { id: "spain", name: "Spanish Grand Prix", date: "2025-06-08", location: "Barcelona" },
  { id: "canada", name: "Canadian Grand Prix", date: "2025-06-15", location: "Montreal" },
  { id: "austria", name: "Austrian Grand Prix", date: "2025-06-29", location: "Spielberg" },
  { id: "britain", name: "British Grand Prix", date: "2025-07-06", location: "Silverstone" },
  { id: "hungary", name: "Hungarian Grand Prix", date: "2025-07-20", location: "Budapest" },
  { id: "belgium", name: "Belgian Grand Prix", date: "2025-07-27", location: "Spa" },
  { id: "netherlands", name: "Dutch Grand Prix", date: "2025-08-31", location: "Zandvoort" },
  { id: "italy", name: "Italian Grand Prix", date: "2025-09-07", location: "Monza" },
  { id: "azerbaijan", name: "Azerbaijan Grand Prix", date: "2025-09-21", location: "Baku" },
  { id: "singapore", name: "Singapore Grand Prix", date: "2025-10-05", location: "Singapore" },
  { id: "japan", name: "Japanese Grand Prix", date: "2025-10-12", location: "Suzuka" },
  { id: "qatar", name: "Qatar Grand Prix", date: "2025-11-02", location: "Lusail" },
  { id: "usa", name: "United States Grand Prix", date: "2025-11-09", location: "Austin" },
  { id: "mexico", name: "Mexican Grand Prix", date: "2025-11-16", location: "Mexico City" },
  { id: "brazil", name: "Brazilian Grand Prix", date: "2025-11-30", location: "São Paulo" },
  { id: "las-vegas", name: "Las Vegas Grand Prix", date: "2025-12-07", location: "Las Vegas" },
  { id: "abu-dhabi", name: "Abu Dhabi Grand Prix", date: "2025-12-14", location: "Abu Dhabi" }
];

interface RaceSelectProps {
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
}

export const RaceSelect = ({ value, onValueChange, placeholder = "Select a race" }: RaceSelectProps) => {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {races2025.map((race) => (
          <SelectItem key={race.id} value={race.id}>
            <div className="flex flex-col">
              <span className="font-medium">{race.name}</span>
              <span className="text-sm text-muted-foreground">
                {race.location} • {new Date(race.date).toLocaleDateString()}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export { races2025 };