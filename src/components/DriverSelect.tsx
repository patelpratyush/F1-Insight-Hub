import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { drivers2025 } from "@/data/drivers2025";

interface DriverSelectProps {
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  dark?: boolean;
}

export const DriverSelect = ({
  value,
  onValueChange,
  placeholder = "Select a driver",
  className = "",
  dark = false,
}: DriverSelectProps) => {
  const triggerClass = dark
    ? "w-full bg-[#111111] border-white/10 text-white rounded-full h-12"
    : "w-full";
  const contentClass = dark ? "bg-[#111111] border-white/10 rounded-2xl" : "";
  const itemClass = dark
    ? "text-white focus:bg-white/10 focus:text-white hover:bg-white/10 rounded-xl"
    : "";

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className={`${triggerClass} ${className}`}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent className={contentClass}>
        {drivers2025.map((driver) => (
          <SelectItem key={driver.id} value={driver.id} className={itemClass}>
            <div className="flex items-center space-x-2">
              <span className="font-medium">{driver.id}</span>
              <span className={dark ? "text-gray-400" : "text-gray-600"}>
                - {driver.name}
              </span>
              <span
                className={`text-xs ${dark ? "text-gray-500" : "text-gray-500"}`}
              >
                #{driver.number} - {driver.team}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default DriverSelect;
