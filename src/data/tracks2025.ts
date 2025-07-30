/**
 * F1 2025 Season Track Data
 * Centralized track information for consistent use across all components
 */

export interface F1Track {
  name: string;
  circuit: string;
  location: string;
  country: string;
  round: number;
}

export const tracks2025: F1Track[] = [
  { name: "Bahrain Grand Prix", circuit: "Bahrain International Circuit", location: "Sakhir", country: "Bahrain", round: 1 },
  { name: "Saudi Arabian Grand Prix", circuit: "Jeddah Corniche Circuit", location: "Jeddah", country: "Saudi Arabia", round: 2 },
  { name: "Australian Grand Prix", circuit: "Albert Park Circuit", location: "Melbourne", country: "Australia", round: 3 },
  { name: "Japanese Grand Prix", circuit: "Suzuka International Racing Course", location: "Suzuka", country: "Japan", round: 4 },
  { name: "Chinese Grand Prix", circuit: "Shanghai International Circuit", location: "Shanghai", country: "China", round: 5 },
  { name: "Miami Grand Prix", circuit: "Miami International Autodrome", location: "Miami", country: "United States", round: 6 },
  { name: "Emilia Romagna Grand Prix", circuit: "Autodromo Enzo e Dino Ferrari", location: "Imola", country: "Italy", round: 7 },
  { name: "Monaco Grand Prix", circuit: "Monaco Street Circuit", location: "Monte Carlo", country: "Monaco", round: 8 },
  { name: "Canadian Grand Prix", circuit: "Circuit Gilles Villeneuve", location: "Montreal", country: "Canada", round: 9 },
  { name: "Spanish Grand Prix", circuit: "Circuit de Barcelona-Catalunya", location: "Barcelona", country: "Spain", round: 10 },
  { name: "Austrian Grand Prix", circuit: "Red Bull Ring", location: "Spielberg", country: "Austria", round: 11 },
  { name: "British Grand Prix", circuit: "Silverstone Circuit", location: "Silverstone", country: "United Kingdom", round: 12 },
  { name: "Hungarian Grand Prix", circuit: "Hungaroring", location: "Budapest", country: "Hungary", round: 13 },
  { name: "Belgian Grand Prix", circuit: "Circuit de Spa-Francorchamps", location: "Spa", country: "Belgium", round: 14 },
  { name: "Dutch Grand Prix", circuit: "Circuit Zandvoort", location: "Zandvoort", country: "Netherlands", round: 15 },
  { name: "Italian Grand Prix", circuit: "Autodromo Nazionale di Monza", location: "Monza", country: "Italy", round: 16 },
  { name: "Azerbaijan Grand Prix", circuit: "Baku City Circuit", location: "Baku", country: "Azerbaijan", round: 17 },
  { name: "Singapore Grand Prix", circuit: "Marina Bay Street Circuit", location: "Singapore", country: "Singapore", round: 18 },
  { name: "United States Grand Prix", circuit: "Circuit of the Americas", location: "Austin", country: "United States", round: 19 },
  { name: "Mexico City Grand Prix", circuit: "Autodromo Hermanos Rodriguez", location: "Mexico City", country: "Mexico", round: 20 },
  { name: "São Paulo Grand Prix", circuit: "Autodromo Jose Carlos Pace", location: "São Paulo", country: "Brazil", round: 21 },
  { name: "Las Vegas Grand Prix", circuit: "Las Vegas Strip Circuit", location: "Las Vegas", country: "United States", round: 22 },
  { name: "Qatar Grand Prix", circuit: "Losail International Circuit", location: "Lusail", country: "Qatar", round: 23 },
  { name: "Abu Dhabi Grand Prix", circuit: "Yas Marina Circuit", location: "Abu Dhabi", country: "UAE", round: 24 }
];

// For components that only need track names
export const trackNames = tracks2025.map(track => track.name);

// For components that need name-circuit pairs
export const trackOptions = tracks2025.map(track => ({
  name: track.name,
  circuit: track.circuit,
  location: track.location,
  country: track.country
}));

// Helper function to get track by name
export const getTrackByName = (name: string): F1Track | undefined => {
  return tracks2025.find(track => track.name === name);
};

// Helper function to get circuit name by track name
export const getCircuitByTrackName = (trackName: string): string => {
  const track = getTrackByName(trackName);
  return track ? track.circuit : trackName;
};

export default tracks2025;