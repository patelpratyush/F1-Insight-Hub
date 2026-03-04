import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useDrivers, type Driver } from "@/hooks/useF1Metadata";

interface DriverSelectProps {
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  dark?: boolean;
  drivers?: Driver[];
  year?: number;
}

export const DriverSelect = ({
  value,
  onValueChange,
  placeholder = "Select a driver",
  className = "",
  dark = false,
  drivers: driversProp,
  year,
}: DriverSelectProps) => {
  const { data: fetchedDrivers } = useDrivers(year);
  const drivers = driversProp || fetchedDrivers || [];

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
        {drivers.map((driver) => (
          <SelectItem key={driver.id} value={driver.id} className={itemClass}>
            <div className="flex items-center space-x-2">
              <span className="font-medium">{driver.id}</span>
              <span className={dark ? "text-gray-400" : "text-gray-600"}>
                - {driver.name}
              </span>
              {driver.team && (
                <span
                  className={`text-xs ${dark ? "text-gray-500" : "text-gray-500"}`}
                >
                  {driver.number ? `#${driver.number} - ` : ""}{driver.team}
                </span>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default DriverSelect;
