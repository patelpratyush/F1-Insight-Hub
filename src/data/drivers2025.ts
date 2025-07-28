/**
 * Complete 2025 F1 Driver Grid - Centralized driver data
 * Used across all components for consistency
 */

export interface Driver {
  id: string;
  name: string;
  team: string;
  number: number;
  teamColor?: string;
}

export const drivers2025: Driver[] = [
  // McLaren
  { id: "PIA", name: "Oscar Piastri", team: "McLaren", number: 81, teamColor: "#FF8700" },
  { id: "NOR", name: "Lando Norris", team: "McLaren", number: 4, teamColor: "#FF8700" },
  
  // Ferrari
  { id: "LEC", name: "Charles Leclerc", team: "Ferrari", number: 16, teamColor: "#DC143C" },
  { id: "HAM", name: "Lewis Hamilton", team: "Ferrari", number: 44, teamColor: "#DC143C" },
  
  // Mercedes
  { id: "RUS", name: "George Russell", team: "Mercedes", number: 63, teamColor: "#00D2BE" },
  { id: "ANT", name: "Kimi Antonelli", team: "Mercedes", number: 12, teamColor: "#00D2BE" },
  
  // Red Bull Racing
  { id: "VER", name: "Max Verstappen", team: "Red Bull Racing", number: 1, teamColor: "#0600EF" },
  { id: "TSU", name: "Yuki Tsunoda", team: "Red Bull Racing", number: 22, teamColor: "#0600EF" },
  
  // Williams
  { id: "ALB", name: "Alexander Albon", team: "Williams", number: 23, teamColor: "#005AFF" },
  { id: "SAI", name: "Carlos Sainz", team: "Williams", number: 55, teamColor: "#005AFF" },
  
  // Kick Sauber
  { id: "HUL", name: "Nico Hülkenberg", team: "Kick Sauber", number: 27, teamColor: "#52E252" },
  { id: "BOR", name: "Gabriel Bortoleto", team: "Kick Sauber", number: 5, teamColor: "#52E252" },
  
  // Racing Bulls
  { id: "LAW", name: "Liam Lawson", team: "Racing Bulls", number: 30, teamColor: "#6692FF" },
  { id: "HAD", name: "Isack Hadjar", team: "Racing Bulls", number: 6, teamColor: "#6692FF" },
  
  // Aston Martin
  { id: "STR", name: "Lance Stroll", team: "Aston Martin", number: 18, teamColor: "#006F62" },
  { id: "ALO", name: "Fernando Alonso", team: "Aston Martin", number: 14, teamColor: "#006F62" },
  
  // Haas
  { id: "OCO", name: "Esteban Ocon", team: "Haas", number: 31, teamColor: "#FFFFFF" },
  { id: "BEA", name: "Oliver Bearman", team: "Haas", number: 38, teamColor: "#FFFFFF" },
  
  // Alpine
  { id: "GAS", name: "Pierre Gasly", team: "Alpine", number: 10, teamColor: "#0090FF" },
  { id: "COL", name: "Franco Colapinto", team: "Alpine", number: 43, teamColor: "#0090FF" }
];

// Helper function to get driver by ID
export const getDriverById = (id: string): Driver | undefined => {
  return drivers2025.find(driver => driver.id === id);
};

// Helper function to get drivers by team
export const getDriversByTeam = (team: string): Driver[] => {
  return drivers2025.filter(driver => driver.team === team);
};

// Helper function to get all team names
export const getTeamNames = (): string[] => {
  return Array.from(new Set(drivers2025.map(driver => driver.team)));
};

// Driver codes only (for backward compatibility with components that only need codes)
export const driverCodes = drivers2025.map(driver => driver.id);

export default drivers2025;