import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTracks, type Track } from "@/hooks/useF1Metadata";

interface RaceSelectProps {
  value?: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  tracks?: Track[];
  year?: number;
}

export const RaceSelect = ({
  value,
  onValueChange,
  placeholder = "Select a race",
  tracks: tracksProp,
  year,
}: RaceSelectProps) => {
  const { data: fetchedTracks } = useTracks(year);
  const tracks = tracksProp || fetchedTracks || [];

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {tracks.map((track) => (
          <SelectItem key={track.race_name} value={track.race_name}>
            <div className="flex flex-col">
              <span className="font-medium">{track.race_name}</span>
              <span className="text-sm text-muted-foreground">
                {track.location} &bull;{" "}
                {new Date(track.date).toLocaleDateString()}
              </span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

export default RaceSelect;
