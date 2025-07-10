import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const drivers2025 = [
  { id: "VER", name: "Max Verstappen", team: "Red Bull Racing", number: 1 },
  { id: "PER", name: "Sergio Pérez", team: "Red Bull Racing", number: 11 },
  { id: "LEC", name: "Charles Leclerc", team: "Ferrari", number: 16 },
  { id: "SAI", name: "Carlos Sainz", team: "Ferrari", number: 55 },
  { id: "HAM", name: "Lewis Hamilton", team: "Mercedes", number: 44 },
  { id: "RUS", name: "George Russell", team: "Mercedes", number: 63 },
  { id: "NOR", name: "Lando Norris", team: "McLaren", number: 4 },
  { id: "PIA", name: "Oscar Piastri", team: "McLaren", number: 81 },
  { id: "ALO", name: "Fernando Alonso", team: "Aston Martin", number: 14 },
  { id: "STR", name: "Lance Stroll", team: "Aston Martin", number: 18 },
  { id: "OCO", name: "Esteban Ocon", team: "Alpine", number: 31 },
  { id: "GAS", name: "Pierre Gasly", team: "Alpine", number: 10 },
  { id: "TSU", name: "Yuki Tsunoda", team: "AlphaTauri", number: 22 },
  { id: "RIC", name: "Daniel Ricciardo", team: "AlphaTauri", number: 3 },
  { id: "ALB", name: "Alexander Albon", team: "Williams", number: 23 },
  { id: "SAR", name: "Logan Sargeant", team: "Williams", number: 2 },
  { id: "BOT", name: "Valtteri Bottas", team: "Alfa Romeo", number: 77 },
  { id: "ZHO", name: "Zhou Guanyu", team: "Alfa Romeo", number: 24 },
  { id: "MAG", name: "Kevin Magnussen", team: "Haas", number: 20 },
  { id: "HUL", name: "Nico Hülkenberg", team: "Haas", number: 27 }
];

interface DriverSelectProps {
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
}

export const DriverSelect = ({ value, onValueChange, placeholder = "Select a driver" }: DriverSelectProps) => {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {drivers2025.map((driver) => (
          <SelectItem key={driver.id} value={driver.id}>
            <div className="flex justify-between items-center w-full">
              <div className="flex flex-col">
                <span className="font-medium">{driver.name}</span>
                <span className="text-sm text-muted-foreground">{driver.team}</span>
              </div>
              <span className="text-sm font-mono">#{driver.number}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export { drivers2025 };