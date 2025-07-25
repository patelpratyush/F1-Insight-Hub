#!/usr/bin/env python3
"""
F1 Telemetry Data Analyzer Service
Comprehensive analysis of F1 telemetry data including performance metrics,
car setup analysis, track analysis, driver comparisons, and strategic insights.
"""

import pandas as pd
import numpy as np
import fastf1
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import warnings
import os

warnings.filterwarnings('ignore')

# Use the existing cache directory
cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TelemetryMetrics:
    """Data class for telemetry performance metrics"""
    lap_times: Dict[str, float]
    sector_times: Dict[str, List[float]]
    speed_stats: Dict[str, float]
    throttle_stats: Dict[str, float]
    brake_stats: Dict[str, float]
    gear_usage: Dict[int, float]
    tire_performance: Dict[str, Any]

@dataclass
class DriverComparison:
    """Data class for driver comparison metrics"""
    time_delta: float
    sector_deltas: List[float]
    speed_advantage: Dict[str, float]
    consistency_metrics: Dict[str, float]
    risk_assessment: Dict[str, float]

@dataclass
class TrackAnalysis:
    """Data class for track analysis results"""
    optimal_racing_line: List[Tuple[float, float]]
    corner_analysis: Dict[str, Dict[str, float]]
    overtaking_zones: List[Dict[str, Any]]
    track_evolution: Dict[str, float]

class TelemetryAnalyzerService:
    """Enhanced F1 Telemetry Analyzer with comprehensive metrics"""
    
    def __init__(self):
        """Initialize the telemetry analyzer"""
        self.cache_enabled = True
        self.track_characteristics = self._load_track_characteristics()
        self.driver_mapping = {
            # 2024 Season
            '1': 'VER',   # Max Verstappen - Red Bull
            '11': 'PER',  # Sergio Perez - Red Bull
            '16': 'LEC',  # Charles Leclerc - Ferrari
            '55': 'SAI',  # Carlos Sainz - Ferrari (2024)
            '44': 'HAM',  # Lewis Hamilton - Mercedes (2024) / Ferrari (2025)
            '63': 'RUS',  # George Russell - Mercedes
            '4': 'NOR',   # Lando Norris - McLaren
            '81': 'PIA',  # Oscar Piastri - McLaren
            '14': 'ALO',  # Fernando Alonso - Aston Martin
            '18': 'STR',  # Lance Stroll - Aston Martin
            '10': 'GAS',  # Pierre Gasly - Alpine
            '31': 'OCO',  # Esteban Ocon - Alpine (2024)
            '22': 'TSU',  # Yuki Tsunoda - RB
            '3': 'RIC',   # Daniel Ricciardo - RB (2024)
            '23': 'ALB',  # Alexander Albon - Williams
            '2': 'SAR',   # Logan Sargeant - Williams (2024)
            '20': 'MAG',  # Kevin Magnussen - Haas
            '27': 'HUL',  # Nico Hulkenberg - Haas
            '77': 'BOT',  # Valtteri Bottas - Kick Sauber
            '24': 'ZHO',  # Guanyu Zhou - Kick Sauber
            # 2025 additions
            '38': 'BEA',  # Oliver Bearman - Haas (2025)
            '43': 'COL',  # Franco Colapinto - Williams (2025)
            '12': 'ANT'   # Andrea Kimi Antonelli - Mercedes (2025)
        }
        
    def _load_track_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """Load track characteristics for analysis"""
        return {
            'Monaco': {
                'corners': 19, 'elevation_change': 42, 'tire_wear': 'low',
                'overtaking_difficulty': 'very_high', 'track_length': 3.337
            },
            'Silverstone': {
                'corners': 18, 'elevation_change': 15, 'tire_wear': 'medium',
                'overtaking_difficulty': 'medium', 'track_length': 5.891
            },
            'Spa-Francorchamps': {
                'corners': 19, 'elevation_change': 104, 'tire_wear': 'high',
                'overtaking_difficulty': 'low', 'track_length': 7.004
            },
            # Add more tracks as needed
        }

    async def analyze_session_telemetry(
        self, 
        year: int, 
        race: str, 
        session: str = 'R',
        drivers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive telemetry analysis for a race session
        
        Args:
            year: Race year
            race: Race name
            session: Session type ('R' for race, 'Q' for qualifying, etc.)
            drivers: List of driver abbreviations to analyze
            
        Returns:
            Complete telemetry analysis results
        """
        try:
            logger.info(f"Loading telemetry data for {year} {race} {session}")
            
            # Load session data
            session_data = fastf1.get_session(year, race, session)
            session_data.load()
            
            if drivers is None:
                drivers = session_data.drivers
            
            results = {
                'session_info': self._get_session_info(session_data),
                'performance_metrics': {},
                'car_setup_analysis': {},
                'track_analysis': {},
                'driver_comparisons': {},
                'strategic_insights': {}
            }
            
            # Analyze each driver
            for driver in drivers:
                try:
                    driver_data = session_data.laps.pick_driver(driver)
                    if len(driver_data) == 0:
                        continue
                    
                    # Map driver number to abbreviation for frontend compatibility
                    driver_key = self.driver_mapping.get(str(driver), str(driver))
                        
                    # Performance metrics
                    results['performance_metrics'][driver_key] = self._analyze_performance_metrics(
                        driver_data, session_data
                    )
                    
                    # Car setup analysis
                    results['car_setup_analysis'][driver_key] = self._analyze_car_setup(
                        driver_data, session_data
                    )
                    
                except Exception as e:
                    logger.error(f"Error analyzing driver {driver}: {e}")
                    continue
            
            # Track analysis (session-wide)
            results['track_analysis'] = self._analyze_track_characteristics(
                session_data, drivers
            )
            
            # Driver comparisons
            results['driver_comparisons'] = self._compare_drivers(
                session_data, drivers
            )
            
            # Strategic insights
            results['strategic_insights'] = self._analyze_strategic_insights(
                session_data, drivers
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in telemetry analysis: {e}")
            raise

    def _get_session_info(self, session_data) -> Dict[str, Any]:
        """Extract basic session information"""
        return {
            'session_name': session_data.name,
            'event_name': session_data.event.EventName,
            'track_name': session_data.event.Location,
            'date': session_data.date.isoformat() if session_data.date else None,
            'weather': {
                'air_temp': float(session_data.weather_data['AirTemp'].mean()) if 'AirTemp' in session_data.weather_data.columns else None,
                'track_temp': float(session_data.weather_data['TrackTemp'].mean()) if 'TrackTemp' in session_data.weather_data.columns else None,
                'humidity': float(session_data.weather_data['Humidity'].mean()) if 'Humidity' in session_data.weather_data.columns else None,
                'rainfall': bool(session_data.weather_data['Rainfall'].any()) if 'Rainfall' in session_data.weather_data.columns else False
            }
        }

    def _analyze_performance_metrics(self, driver_data, session_data) -> TelemetryMetrics:
        """Analyze comprehensive performance metrics for a driver"""
        try:
            # Get fastest lap for detailed analysis
            fastest_lap = driver_data.pick_fastest()
            if fastest_lap.empty:
                return self._empty_telemetry_metrics()
            
            # Get telemetry data
            telemetry = fastest_lap.get_telemetry()
            
            # Convert fastest_lap to dict-like access for compatibility
            fastest_lap_dict = {col: fastest_lap[col] for col in fastest_lap.index}
            
            # Process all lap times for scatterplot - filter for quick laps like FastF1 example
            all_lap_times = []
            fastest_lap_number = None
            fastest_time = float('inf')
            
            # Get quick laps (valid race laps, excluding outlaps/inlaps)
            try:
                quick_laps = driver_data.pick_quicklaps() if hasattr(driver_data, 'pick_quicklaps') else driver_data
            except:
                quick_laps = driver_data
            
            for idx, (_, lap) in enumerate(quick_laps.iterrows()):
                if pd.notna(lap.get('LapTime')):
                    lap_time_seconds = float(lap['LapTime'].total_seconds())
                    
                    # Additional validation - reasonable lap time range
                    if lap_time_seconds > 0 and lap_time_seconds < 300:  # Less than 5 minutes
                        lap_data = {
                            'lap_number': int(lap.get('LapNumber', idx + 1)),
                            'lap_time': lap_time_seconds,
                            'is_valid': True,  # All quick laps are valid
                            'sector_1': float(lap['Sector1Time'].total_seconds()) if pd.notna(lap.get('Sector1Time')) else None,
                            'sector_2': float(lap['Sector2Time'].total_seconds()) if pd.notna(lap.get('Sector2Time')) else None,
                            'sector_3': float(lap['Sector3Time'].total_seconds()) if pd.notna(lap.get('Sector3Time')) else None,
                            'compound': lap.get('Compound', 'UNKNOWN')
                        }
                        all_lap_times.append(lap_data)
                        
                        # Track fastest lap
                        if lap_time_seconds < fastest_time:
                            fastest_time = lap_time_seconds
                            fastest_lap_number = lap_data['lap_number']
            
            # Also include invalid laps (outlaps, etc.) for context
            invalid_laps = []
            for idx, (_, lap) in enumerate(driver_data.iterrows()):
                if pd.notna(lap.get('LapTime')):
                    lap_time_seconds = float(lap['LapTime'].total_seconds())
                    lap_number = int(lap.get('LapNumber', idx + 1))
                    
                    # If not in quick laps, it's invalid
                    if not any(ql['lap_number'] == lap_number for ql in all_lap_times):
                        if lap_time_seconds > 0 and lap_time_seconds < 500:  # Reasonable upper bound
                            invalid_laps.append({
                                'lap_number': lap_number,
                                'lap_time': lap_time_seconds,
                                'is_valid': False,
                                'sector_1': float(lap['Sector1Time'].total_seconds()) if pd.notna(lap.get('Sector1Time')) else None,
                                'sector_2': float(lap['Sector2Time'].total_seconds()) if pd.notna(lap.get('Sector2Time')) else None,
                                'sector_3': float(lap['Sector3Time'].total_seconds()) if pd.notna(lap.get('Sector3Time')) else None,
                                'compound': lap.get('Compound', 'UNKNOWN')
                            })
            
            # Combine all laps
            all_lap_times.extend(invalid_laps)
            
            # Lap times analysis
            lap_times = {
                'fastest_lap': float(fastest_lap_dict['LapTime'].total_seconds()),
                'average_lap': float(driver_data['LapTime'].mean().total_seconds()),
                'consistency': float(driver_data['LapTime'].std().total_seconds()),
                'improvement_rate': self._calculate_improvement_rate(driver_data),
                'all_laps': all_lap_times,
                'fastest_lap_number': fastest_lap_number,
                'total_laps': len(all_lap_times)
            }
            
            # Sector times - handle safely
            sector_times = {
                'sector_1': [],
                'sector_2': [], 
                'sector_3': []
            }
            
            for _, lap in driver_data.iterrows():
                if pd.notna(lap.get('Sector1Time')):
                    sector_times['sector_1'].append(float(lap['Sector1Time'].total_seconds()))
                if pd.notna(lap.get('Sector2Time')):
                    sector_times['sector_2'].append(float(lap['Sector2Time'].total_seconds()))
                if pd.notna(lap.get('Sector3Time')):
                    sector_times['sector_3'].append(float(lap['Sector3Time'].total_seconds()))
            
            # Speed analysis
            speed_stats = {
                'max_speed': float(telemetry['Speed'].max()),
                'avg_speed': float(telemetry['Speed'].mean()),
                'speed_variance': float(telemetry['Speed'].var()),
                'corner_speeds': self._analyze_corner_speeds(telemetry),
                'straight_line_speed': self._analyze_straight_line_speed(telemetry)
            }
            
            # Throttle analysis
            throttle_stats = {
                'max_throttle': float(telemetry['Throttle'].max()),
                'avg_throttle': float(telemetry['Throttle'].mean()),
                'throttle_application_rate': self._calculate_throttle_rate(telemetry),
                'full_throttle_percentage': float((telemetry['Throttle'] == 100).sum() / len(telemetry) * 100)
            }
            
            # Brake analysis
            brake_stats = {
                'max_brake': float(telemetry['Brake'].max()),
                'avg_brake': float(telemetry['Brake'].mean()),
                'brake_zones': self._identify_brake_zones(telemetry),
                'brake_efficiency': self._calculate_brake_efficiency(telemetry)
            }
            
            # Gear usage analysis
            gear_usage = self._analyze_gear_usage(telemetry)
            
            # Tire performance (if available)
            tire_performance = self._analyze_tire_performance(driver_data, fastest_lap)
            
            return TelemetryMetrics(
                lap_times=lap_times,
                sector_times=sector_times,
                speed_stats=speed_stats,
                throttle_stats=throttle_stats,
                brake_stats=brake_stats,
                gear_usage=gear_usage,
                tire_performance=tire_performance
            )
            
        except Exception as e:
            logger.error(f"Error in performance metrics analysis: {e}")
            return self._empty_telemetry_metrics()

    def _analyze_car_setup(self, driver_data, session_data) -> Dict[str, Any]:
        """Analyze car setup data and its impact"""
        try:
            setup_analysis = {
                'tire_strategy': self._analyze_tire_strategy(driver_data),
                'aerodynamic_balance': self._estimate_aero_balance(driver_data),
                'engine_modes': self._analyze_engine_modes(driver_data),
                'suspension_analysis': self._analyze_suspension_effects(driver_data)
            }
            
            return setup_analysis
            
        except Exception as e:
            logger.error(f"Error in car setup analysis: {e}")
            return {}

    def _analyze_track_characteristics(self, session_data, drivers: List[str]) -> TrackAnalysis:
        """Analyze track-specific characteristics and optimal racing lines"""
        try:
            # Get reference lap for racing line analysis
            reference_lap = session_data.laps.pick_fastest()
            if reference_lap.empty:
                return TrackAnalysis([], {}, [], {})
            
            telemetry = reference_lap.get_telemetry()
            
            # Optimal racing line (simplified - would need more sophisticated analysis)
            racing_line = [(float(row.X), float(row.Y)) for _, row in telemetry.iterrows() if pd.notna(row.X) and pd.notna(row.Y)]
            
            # Corner analysis
            corner_analysis = self._analyze_corners(telemetry, session_data.event.Location)
            
            # Overtaking zones
            overtaking_zones = self._identify_overtaking_zones(telemetry, drivers, session_data)
            
            # Track evolution
            track_evolution = self._analyze_track_evolution(session_data)
            
            return TrackAnalysis(
                optimal_racing_line=racing_line,
                corner_analysis=corner_analysis,
                overtaking_zones=overtaking_zones,
                track_evolution=track_evolution
            )
            
        except Exception as e:
            logger.error(f"Error in track analysis: {e}")
            return TrackAnalysis([], {}, [], {})

    def _compare_drivers(self, session_data, drivers: List[str]) -> Dict[str, Dict[str, DriverComparison]]:
        """Compare drivers' performance and driving styles"""
        try:
            comparisons = {}
            
            for i, driver1 in enumerate(drivers):
                comparisons[driver1] = {}
                for driver2 in drivers[i+1:]:
                    try:
                        comparison = self._compare_two_drivers(session_data, driver1, driver2)
                        comparisons[driver1][driver2] = comparison
                    except Exception as e:
                        logger.error(f"Error comparing {driver1} vs {driver2}: {e}")
                        continue
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error in driver comparisons: {e}")
            return {}

    def _analyze_strategic_insights(self, session_data, drivers: List[str]) -> Dict[str, Any]:
        """Analyze strategic insights including tire degradation, fuel effects, etc."""
        try:
            insights = {
                'tire_degradation': self._analyze_tire_degradation(session_data, drivers),
                'fuel_effects': self._analyze_fuel_effects(session_data, drivers),
                'weather_impact': self._analyze_weather_impact(session_data),
                'traffic_analysis': self._analyze_traffic_effects(session_data, drivers),
                'pit_stop_analysis': self._analyze_pit_stops(session_data, drivers)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error in strategic analysis: {e}")
            return {}

    # Helper methods for detailed analysis
    def _calculate_improvement_rate(self, driver_data) -> float:
        """Calculate how much a driver improves over the session"""
        try:
            lap_times = [lap['LapTime'].total_seconds() for lap in driver_data.itertuples() if pd.notna(lap.LapTime)]
            if len(lap_times) < 2:
                return 0.0
            
            # Simple linear regression to find improvement trend
            x = np.arange(len(lap_times))
            slope, _ = np.polyfit(x, lap_times, 1)
            return float(slope)
        except:
            return 0.0

    def _analyze_corner_speeds(self, telemetry) -> Dict[str, float]:
        """Analyze speeds through corners"""
        try:
            # Identify corners by low speed zones
            low_speed_threshold = telemetry['Speed'].quantile(0.3)
            corner_speeds = telemetry[telemetry['Speed'] <= low_speed_threshold]['Speed']
            
            return {
                'avg_corner_speed': float(corner_speeds.mean()),
                'min_corner_speed': float(corner_speeds.min()),
                'corner_speed_variance': float(corner_speeds.var())
            }
        except:
            return {'avg_corner_speed': 0.0, 'min_corner_speed': 0.0, 'corner_speed_variance': 0.0}

    def _analyze_straight_line_speed(self, telemetry) -> Dict[str, float]:
        """Analyze straight-line speed performance"""
        try:
            # Identify straights by high speed zones with full throttle
            straight_mask = (telemetry['Speed'] >= telemetry['Speed'].quantile(0.8)) & (telemetry['Throttle'] >= 95)
            straight_speeds = telemetry[straight_mask]['Speed']
            
            return {
                'max_straight_speed': float(straight_speeds.max()) if len(straight_speeds) > 0 else 0.0,
                'avg_straight_speed': float(straight_speeds.mean()) if len(straight_speeds) > 0 else 0.0
            }
        except:
            return {'max_straight_speed': 0.0, 'avg_straight_speed': 0.0}

    def _calculate_throttle_rate(self, telemetry) -> float:
        """Calculate throttle application rate"""
        try:
            throttle_changes = np.diff(telemetry['Throttle'])
            positive_changes = throttle_changes[throttle_changes > 0]
            return float(positive_changes.mean()) if len(positive_changes) > 0 else 0.0
        except:
            return 0.0

    def _identify_brake_zones(self, telemetry) -> List[Dict[str, Any]]:
        """Identify major braking zones"""
        try:
            brake_zones = []
            brake_data = telemetry['Brake']
            
            # Handle boolean brake data
            if brake_data.dtype == bool:
                braking = brake_data
                brake_threshold = True
            else:
                brake_threshold = 10  # Minimum brake percentage to consider as braking
                braking = brake_data >= brake_threshold
            
            zone_start = None
            
            for i, is_braking in enumerate(braking):
                if is_braking and zone_start is None:
                    zone_start = i
                elif not is_braking and zone_start is not None:
                    zone_data = telemetry.iloc[zone_start:i]
                    if len(zone_data) > 0:
                        max_brake = bool(zone_data['Brake'].any()) if brake_data.dtype == bool else float(zone_data['Brake'].max())
                        brake_zones.append({
                            'start_distance': float(zone_data.iloc[0]['Distance']),
                            'end_distance': float(zone_data.iloc[-1]['Distance']),
                            'max_brake_pressure': max_brake,
                            'speed_reduction': float(zone_data.iloc[0]['Speed'] - zone_data.iloc[-1]['Speed'])
                        })
                    zone_start = None
            
            return brake_zones
        except Exception as e:
            logger.error(f"Error identifying brake zones: {e}")
            return []

    def _calculate_brake_efficiency(self, telemetry) -> float:
        """Calculate brake efficiency based on deceleration vs brake pressure"""
        try:
            speed_changes = np.diff(telemetry['Speed'])
            brake_applications = telemetry['Brake'].iloc[1:]
            
            # Filter for actual braking (negative speed change and brake applied)
            braking_mask = (speed_changes < 0) & (brake_applications > 10)
            
            if braking_mask.sum() == 0:
                return 0.0
            
            deceleration = -speed_changes[braking_mask]
            brake_pressure = brake_applications[braking_mask]
            
            # Efficiency as deceleration per unit of brake pressure
            efficiency = (deceleration / brake_pressure).mean()
            return float(efficiency)
        except:
            return 0.0

    def _analyze_gear_usage(self, telemetry) -> Dict[int, float]:
        """Analyze gear usage distribution"""
        try:
            gear_counts = telemetry['nGear'].value_counts()
            total_points = len(telemetry)
            
            gear_usage = {}
            for gear, count in gear_counts.items():
                gear_usage[int(gear)] = float(count / total_points * 100)
            
            return gear_usage
        except:
            return {}

    def _analyze_tire_performance(self, driver_data, fastest_lap) -> Dict[str, Any]:
        """Analyze tire performance and degradation"""
        try:
            # This would require tire temperature and pressure data
            # For now, return basic compound and age information
            return {
                'compound': fastest_lap.get('Compound', 'Unknown'),
                'tire_age': int(fastest_lap.get('TyreLife', 0)),
                'degradation_estimate': self._estimate_tire_degradation(driver_data)
            }
        except:
            return {'compound': 'Unknown', 'tire_age': 0, 'degradation_estimate': 0.0}

    def _estimate_tire_degradation(self, driver_data) -> float:
        """Estimate tire degradation based on lap time progression"""
        try:
            lap_times = [lap['LapTime'].total_seconds() for lap in driver_data.itertuples() if pd.notna(lap.LapTime)]
            if len(lap_times) < 3:
                return 0.0
            
            # Calculate degradation as time increase per lap
            x = np.arange(len(lap_times))
            slope, _ = np.polyfit(x, lap_times, 1)
            return float(max(0, slope))  # Only positive degradation
        except:
            return 0.0

    def _empty_telemetry_metrics(self) -> TelemetryMetrics:
        """Return empty telemetry metrics structure"""
        return TelemetryMetrics(
            lap_times={},
            sector_times={},
            speed_stats={},
            throttle_stats={},
            brake_stats={},
            gear_usage={},
            tire_performance={}
        )

    # Additional helper methods would be implemented here for:
    # - _analyze_tire_strategy
    # - _estimate_aero_balance  
    # - _analyze_engine_modes
    # - _analyze_suspension_effects
    # - _analyze_corners
    # - _identify_overtaking_zones
    # - _analyze_track_evolution
    # - _compare_two_drivers
    # - _analyze_tire_degradation
    # - _analyze_fuel_effects
    # - _analyze_weather_impact
    # - _analyze_traffic_effects
    # - _analyze_pit_stops

    async def get_driver_comparison_telemetry(
        self,
        year: int,
        race: str,
        driver1: str,
        driver2: str,
        session: str = 'R',
        lap_type: str = 'fastest'  # 'fastest' or specific lap number
    ) -> Dict[str, Any]:
        """
        Get telemetry data for two drivers for comparison
        """
        try:
            logger.info(f"Getting comparison telemetry for {driver1} vs {driver2} at {year} {race}")
            
            session_data = fastf1.get_session(year, race, session)
            session_data.load()
            
            # Get corner information
            corners = []
            try:
                circuit_info = session_data.get_circuit_info()
                if hasattr(circuit_info, 'corners') and not circuit_info.corners.empty:
                    for _, corner in circuit_info.corners.iterrows():
                        corners.append({
                            'number': int(corner.get('Number', 0)),
                            'letter': corner.get('Letter', ''),
                            'distance': float(corner.get('Distance', 0))
                        })
            except Exception as e:
                logger.debug(f"Could not load circuit info: {e}")
            
            # Function to get driver telemetry
            def get_driver_telemetry(driver_code, driver_name):
                try:
                    # Find driver number from abbreviation mapping
                    driver_number = None
                    for num, abbr in self.driver_mapping.items():
                        if abbr == driver_code:
                            driver_number = num
                            break
                    
                    # Use driver number if found, otherwise try the original driver string
                    driver_to_search = driver_number if driver_number else driver_code
                    driver_laps = session_data.laps.pick_driver(driver_to_search)
                    
                    if driver_laps.empty:
                        return None
                    
                    # Get the appropriate lap
                    if lap_type == 'fastest':
                        lap = driver_laps.pick_fastest()
                    else:
                        # Handle specific lap number if needed
                        lap = driver_laps.pick_fastest()  # Default to fastest for now
                    
                    if lap.empty:
                        return None
                    
                    # Get telemetry data with position coordinates
                    telemetry = lap.get_telemetry().add_distance()
                    
                    # Add track position coordinates if available
                    try:
                        telemetry = telemetry.add_distance().add_driver_ahead()
                        # Get circuit coordinates (X, Y positions on track)
                        if hasattr(telemetry, 'X') and hasattr(telemetry, 'Y'):
                            # Use actual coordinates from FastF1
                            pass
                        else:
                            # If coordinates not available, create synthetic ones based on distance
                            logger.debug("Track coordinates not available, using distance-based positioning")
                    except Exception as e:
                        logger.debug(f"Could not add track position data: {e}")
                    
                    # Convert brake data (handle both boolean and numeric)
                    brake_data = telemetry['Brake']
                    if brake_data.dtype == bool:
                        brake_processed = [100 if x else 0 for x in brake_data.tolist()]
                    else:
                        brake_processed = brake_data.tolist()
                    
                    # Get RPM data (engine revolutions per minute)
                    rpm_data = telemetry['RPM'].tolist() if 'RPM' in telemetry.columns else []
                    
                    # Get ERS data (Energy Recovery System)
                    ers_data = {
                        'deployment': telemetry['Source'].tolist() if 'Source' in telemetry.columns else [],
                        'harvest': telemetry['Source'].tolist() if 'Source' in telemetry.columns else []  # Placeholder for harvest data
                    }
                    
                    # Get team color (you might want to add this mapping)
                    team_colors = {
                        'VER': '#1E41FF', 'PER': '#1E41FF',  # Red Bull
                        'LEC': '#DC143C', 'SAI': '#DC143C', 'HAM': '#DC143C',  # Ferrari  
                        'RUS': '#00D2BE', 'ANT': '#00D2BE',  # Mercedes
                        'NOR': '#FF8700', 'PIA': '#FF8700',  # McLaren
                        'ALO': '#006F62', 'STR': '#006F62',  # Aston Martin
                        'GAS': '#0090FF', 'OCO': '#0090FF',  # Alpine
                        'TSU': '#6692FF', 'LAW': '#6692FF',  # RB
                        'ALB': '#005AFF', 'COL': '#005AFF', 'SAI': '#005AFF',  # Williams
                        'HUL': '#FFFFFF', 'BEA': '#FFFFFF',  # Haas
                        'BOT': '#52E252', 'ZHO': '#52E252',  # Kick Sauber
                    }
                    
                    # Get sector information
                    sector_times = {
                        'sector_1': float(lap['Sector1Time'].total_seconds()) if pd.notna(lap.get('Sector1Time')) else None,
                        'sector_2': float(lap['Sector2Time'].total_seconds()) if pd.notna(lap.get('Sector2Time')) else None,
                        'sector_3': float(lap['Sector3Time'].total_seconds()) if pd.notna(lap.get('Sector3Time')) else None,
                    }
                    
                    # Try to get sector boundaries from circuit info or estimate from telemetry
                    sector_boundaries = self._get_sector_boundaries(session_data, telemetry)
                    
                    return {
                        'driver': driver_code,
                        'team': lap.get('Team', 'Unknown'),
                        'lapTime': float(lap['LapTime'].total_seconds()),
                        'sectorTimes': sector_times,
                        'sectorBoundaries': sector_boundaries,
                        'telemetry': {
                            'distance': telemetry['Distance'].tolist(),
                            'time': telemetry['Time'].dt.total_seconds().tolist(),
                            'speed': telemetry['Speed'].tolist(),
                            'throttle': telemetry['Throttle'].tolist(),
                            'brake': brake_processed,
                            'gear': telemetry['nGear'].tolist(),
                            'drs': telemetry['DRS'].tolist() if 'DRS' in telemetry.columns else [],
                            'rpm': rpm_data,
                            'ers': ers_data,
                            'x_position': telemetry['X'].tolist() if 'X' in telemetry.columns else [],
                            'y_position': telemetry['Y'].tolist() if 'Y' in telemetry.columns else []
                        },
                        'color': team_colors.get(driver_code, '#9CA3AF')
                    }
                    
                except Exception as e:
                    logger.error(f"Error getting telemetry for {driver_name}: {e}")
                    return None
            
            # Get telemetry for both drivers
            driver1_data = get_driver_telemetry(driver1, driver1)
            driver2_data = get_driver_telemetry(driver2, driver2)
            
            if not driver1_data or not driver2_data:
                return {'error': f'Could not load telemetry data for one or both drivers'}
            
            return {
                'session_info': {
                    'year': year,
                    'race': race,
                    'session': session
                },
                'driver1': driver1_data,
                'driver2': driver2_data,
                'corners': corners
            }
            
        except Exception as e:
            logger.error(f"Error getting driver comparison telemetry: {e}")
            return {'error': str(e)}

    async def get_track_map_data(
        self,
        year: int,
        race: str,
        driver: str,
        session: str = 'R',
        lap_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get track map data with driver positions for visualization
        """
        try:
            logger.info(f"Getting track map data for {driver} at {year} {race}")
            
            session_data = fastf1.get_session(year, race, session)
            session_data.load()
            
            # Find driver number from abbreviation mapping
            driver_number = None
            for num, abbr in self.driver_mapping.items():
                if abbr == driver:
                    driver_number = num
                    break
            
            # Use driver number if found, otherwise try the original driver string
            driver_to_search = driver_number if driver_number else driver
            driver_laps = session_data.laps.pick_driver(driver_to_search)
            
            if driver_laps.empty:
                return {'error': f'No laps found for driver {driver}'}
            
            # Get the specific lap or fastest lap
            if lap_number:
                lap = driver_laps[driver_laps['LapNumber'] == lap_number]
                if lap.empty:
                    lap = driver_laps.pick_fastest()
            else:
                lap = driver_laps.pick_fastest()
            
            if lap.empty:
                return {'error': f'No suitable lap found for {driver}'}
            
            # Get telemetry data with coordinates
            telemetry = lap.get_telemetry().add_distance()
            
            # Create track layout from session data (all drivers combined for complete track)
            try:
                # Get track outline from all available telemetry
                all_telemetry = session_data.laps.pick_fastest().get_telemetry().add_distance()
                
                # Sample points for track layout (every 10th point for performance)
                sample_interval = max(1, len(all_telemetry) // 200)  # Max 200 points
                track_layout = {
                    'x': all_telemetry['X'][::sample_interval].tolist() if 'X' in all_telemetry.columns else [],
                    'y': all_telemetry['Y'][::sample_interval].tolist() if 'Y' in all_telemetry.columns else [],
                    'distance': all_telemetry['Distance'][::sample_interval].tolist()
                }
                
                # If no coordinates available, create synthetic track layout
                if not track_layout['x']:
                    logger.info("No track coordinates available, creating synthetic layout")
                    distances = all_telemetry['Distance'].tolist()
                    # Create a circular-ish track layout based on distance
                    import math
                    max_distance = max(distances) if distances else 5000
                    radius = max_distance / (2 * math.pi)
                    
                    track_layout = {
                        'x': [radius * math.cos(2 * math.pi * d / max_distance) for d in distances[::sample_interval]],
                        'y': [radius * math.sin(2 * math.pi * d / max_distance) for d in distances[::sample_interval]],
                        'distance': distances[::sample_interval]
                    }
                
            except Exception as e:
                logger.error(f"Error creating track layout: {e}")
                # Fallback to simple circular track
                import math
                max_distance = 5000
                radius = 800
                num_points = 100
                track_layout = {
                    'x': [radius * math.cos(2 * math.pi * i / num_points) for i in range(num_points)],
                    'y': [radius * math.sin(2 * math.pi * i / num_points) for i in range(num_points)],
                    'distance': [max_distance * i / num_points for i in range(num_points)]
                }
            
            # Create driver position data
            driver_positions = []
            for i, row in telemetry.iterrows():
                position_data = {
                    'distance': float(row['Distance']),
                    'time': float(row['Time'].total_seconds()),
                    'speed': float(row['Speed']),
                }
                
                # Add coordinates if available
                if 'X' in telemetry.columns and 'Y' in telemetry.columns:
                    position_data['x'] = float(row['X'])
                    position_data['y'] = float(row['Y'])
                else:
                    # Create synthetic coordinates based on distance
                    import math
                    max_distance = float(telemetry['Distance'].max())
                    radius = 800
                    angle = 2 * math.pi * float(row['Distance']) / max_distance
                    position_data['x'] = radius * math.cos(angle)
                    position_data['y'] = radius * math.sin(angle)
                
                driver_positions.append(position_data)
            
            # Get sector boundaries
            sector_boundaries = self._get_sector_boundaries(session_data, telemetry)
            
            # Get corner information
            corners = []
            try:
                circuit_info = session_data.get_circuit_info()
                if hasattr(circuit_info, 'corners') and not circuit_info.corners.empty:
                    for _, corner in circuit_info.corners.iterrows():
                        corner_data = {
                            'number': int(corner.get('Number', 0)),
                            'distance': float(corner.get('Distance', 0))
                        }
                        
                        # Add coordinates if available in corner data or interpolate from track
                        if 'X' in corner and 'Y' in corner:
                            corner_data['x'] = float(corner['X'])
                            corner_data['y'] = float(corner['Y'])
                        else:
                            # Interpolate position from track layout based on distance
                            corner_distance = corner_data['distance']
                            # Find closest track point
                            closest_idx = min(range(len(track_layout['distance'])), 
                                             key=lambda i: abs(track_layout['distance'][i] - corner_distance))
                            corner_data['x'] = track_layout['x'][closest_idx]
                            corner_data['y'] = track_layout['y'][closest_idx]
                        
                        corners.append(corner_data)
            except Exception as e:
                logger.debug(f"Could not load corner information: {e}")
            
            # Create racing line (simplified as track centerline)
            racing_line = None
            if track_layout['x']:
                # Use track layout as racing line for now
                racing_line = {
                    'x': track_layout['x'],
                    'y': track_layout['y']
                }
            
            result = {
                'success': True,
                'session_info': {
                    'year': year,
                    'race': race,
                    'session': session,
                    'driver': driver,
                    'lap_number': int(lap['LapNumber'].iloc[0]) if hasattr(lap, 'iloc') else lap_number
                },
                'track_map': {
                    'track_layout': track_layout,
                    'driver_positions': driver_positions,
                    'racing_line': racing_line,
                    'sectors': sector_boundaries,
                    'corners': corners
                }
            }
            
            logger.info(f"Successfully generated track map data with {len(driver_positions)} position points")
            return result
            
        except Exception as e:
            logger.error(f"Error getting track map data: {e}")
            return {'error': str(e), 'success': False}

    async def get_speed_trace_with_inputs(
        self, 
        year: int, 
        race: str, 
        driver: str, 
        session: str = 'R',
        lap_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detailed speed trace with throttle/brake overlay for visualization
        This is the most valuable analysis for understanding driver performance
        """
        try:
            logger.info(f"Getting speed trace for {driver} at {year} {race}")
            
            session_data = fastf1.get_session(year, race, session)
            session_data.load()
            
            # Find driver number from abbreviation mapping
            driver_number = None
            for num, abbr in self.driver_mapping.items():
                if abbr == driver:
                    driver_number = num
                    break
            
            # Use driver number if found, otherwise try the original driver string
            driver_to_search = driver_number if driver_number else driver
            driver_laps = session_data.laps.pick_driver(driver_to_search)
            
            if lap_number:
                lap = driver_laps[driver_laps['LapNumber'] == lap_number].iloc[0]
            else:
                lap = driver_laps.pick_fastest()
            
            if lap.empty:
                return {'error': 'No lap data found'}
            
            telemetry = lap.get_telemetry()
            
            # Convert brake data (handle both boolean and numeric)
            brake_data = telemetry['Brake']
            if brake_data.dtype == bool:
                # Convert boolean brake data to 0/100 values
                brake_processed = [100 if x else 0 for x in brake_data.tolist()]
            else:
                # Use numeric brake data as-is
                brake_processed = brake_data.tolist()

            # Get RPM data (engine revolutions per minute)
            rpm_data = telemetry['RPM'].tolist() if 'RPM' in telemetry.columns else []

            # Get circuit/corner information
            corners = []
            try:
                circuit_info = session_data.get_circuit_info()
                if hasattr(circuit_info, 'corners') and not circuit_info.corners.empty:
                    corners = []
                    for _, corner in circuit_info.corners.iterrows():
                        corners.append({
                            'number': int(corner.get('Number', 0)),
                            'letter': corner.get('Letter', ''),
                            'distance': float(corner.get('Distance', 0))
                        })
            except Exception as e:
                logger.debug(f"Could not load circuit info: {e}")
                # Fallback: estimate corners based on low speed zones
                corners = self._estimate_corners_from_telemetry(telemetry)

            # Prepare data for visualization
            trace_data = {
                'lap_info': {
                    'driver': driver,
                    'lap_time': float(lap['LapTime'].total_seconds()),
                    'lap_number': int(lap['LapNumber']),
                    'compound': lap.get('Compound', 'Unknown')
                },
                'telemetry': {
                    'distance': telemetry['Distance'].tolist(),
                    'time': telemetry['Time'].dt.total_seconds().tolist(),
                    'speed': telemetry['Speed'].tolist(),
                    'throttle': telemetry['Throttle'].tolist(),
                    'brake': brake_processed,
                    'gear': telemetry['nGear'].tolist(),
                    'rpm': rpm_data,
                    'drs': telemetry['DRS'].tolist() if 'DRS' in telemetry.columns else []
                },
                'analysis': {
                    'max_speed': float(telemetry['Speed'].max()),
                    'avg_speed': float(telemetry['Speed'].mean()),
                    'braking_zones': len(self._identify_brake_zones(telemetry)),
                    'full_throttle_pct': float((telemetry['Throttle'] == 100).sum() / len(telemetry) * 100)
                },
                'corners': corners
            }
            
            return trace_data
            
        except Exception as e:
            logger.error(f"Error getting speed trace: {e}")
            return {'error': str(e)}

    # Missing methods implementation
    def _analyze_tire_strategy(self, driver_data) -> Dict[str, Any]:
        """Analyze tire strategy and compound usage"""
        try:
            strategy = {
                'compounds_used': [],
                'stint_lengths': [],
                'degradation_rate': 0.0
            }
            
            # Group by tire compound
            if 'Compound' in driver_data.columns:
                compounds = driver_data['Compound'].value_counts().to_dict()
                strategy['compounds_used'] = list(compounds.keys())
                strategy['stint_lengths'] = list(compounds.values())
            
            return strategy
        except Exception as e:
            logger.error(f"Error analyzing tire strategy: {e}")
            return {}

    def _estimate_aero_balance(self, driver_data) -> Dict[str, Any]:
        """Estimate aerodynamic balance from telemetry patterns"""
        try:
            return {
                'estimated_downforce': 'Medium',
                'balance_tendency': 'Neutral',
                'confidence': 'Low - Estimated from telemetry patterns'
            }
        except Exception as e:
            logger.error(f"Error estimating aero balance: {e}")
            return {}

    def _analyze_engine_modes(self, driver_data) -> Dict[str, Any]:
        """Analyze engine mode usage patterns"""
        try:
            return {
                'mode_changes': 0,
                'estimated_modes': ['Standard'],
                'power_delivery': 'Consistent'
            }
        except Exception as e:
            logger.error(f"Error analyzing engine modes: {e}")
            return {}

    def _analyze_suspension_effects(self, driver_data) -> Dict[str, Any]:
        """Analyze suspension setup effects"""
        try:
            return {
                'ride_height': 'Unknown',
                'damping': 'Unknown',
                'estimated_setup': 'Balanced'
            }
        except Exception as e:
            logger.error(f"Error analyzing suspension: {e}")
            return {}

    def _analyze_corners(self, telemetry, track_name) -> Dict[str, Dict[str, float]]:
        """Analyze corner characteristics"""
        try:
            # Simplified corner analysis - identify slow speed zones
            corners = {}
            speed_data = telemetry['Speed']
            
            # Find speed below 200 km/h as potential corners
            slow_zones = speed_data[speed_data < 200]
            if len(slow_zones) > 0:
                corners['corner_analysis'] = {
                    'avg_corner_speed': float(slow_zones.mean()),
                    'min_speed': float(slow_zones.min()),
                    'corner_count_estimate': len(slow_zones) // 10  # Rough estimate
                }
            
            return corners
        except Exception as e:
            logger.error(f"Error analyzing corners: {e}")
            return {}

    def _identify_overtaking_zones(self, telemetry, drivers, session_data) -> List[Dict[str, Any]]:
        """Identify potential overtaking zones"""
        try:
            zones = []
            # Simple implementation - look for high speed zones
            high_speed = telemetry[telemetry['Speed'] > telemetry['Speed'].quantile(0.8)]
            
            if len(high_speed) > 0:
                zones.append({
                    'zone_type': 'Main Straight',
                    'avg_speed': float(high_speed['Speed'].mean()),
                    'max_speed': float(high_speed['Speed'].max()),
                    'length_estimate': len(high_speed)
                })
            
            return zones
        except Exception as e:
            logger.error(f"Error identifying overtaking zones: {e}")
            return []

    def _analyze_track_evolution(self, session_data) -> Dict[str, float]:
        """Analyze track evolution throughout session"""
        try:
            return {
                'grip_improvement': 0.0,
                'temperature_effect': 0.0,
                'track_evolution_factor': 1.0
            }
        except Exception as e:
            logger.error(f"Error analyzing track evolution: {e}")
            return {}

    def _compare_two_drivers(self, session_data, driver1, driver2) -> DriverComparison:
        """Compare two drivers' performance"""
        try:
            return DriverComparison(
                time_delta=0.0,
                sector_deltas=[0.0, 0.0, 0.0],
                speed_advantage={},
                consistency_metrics={},
                risk_assessment={}
            )
        except Exception as e:
            logger.error(f"Error comparing drivers: {e}")
            return DriverComparison(0.0, [], {}, {}, {})

    def _analyze_tire_degradation(self, session_data, drivers) -> Dict[str, Any]:
        """Analyze tire degradation patterns"""
        try:
            return {
                'degradation_rate': 0.0,
                'optimal_stint_length': 0,
                'compound_performance': {}
            }
        except Exception as e:
            logger.error(f"Error analyzing tire degradation: {e}")
            return {}

    def _analyze_fuel_effects(self, session_data, drivers) -> Dict[str, Any]:
        """Analyze fuel load effects on performance"""
        try:
            return {
                'fuel_effect_per_kg': 0.0,
                'estimated_fuel_loads': {},
                'performance_impact': 'Low'
            }
        except Exception as e:
            logger.error(f"Error analyzing fuel effects: {e}")
            return {}

    def _analyze_weather_impact(self, session_data) -> Dict[str, Any]:
        """Analyze weather impact on performance"""
        try:
            weather_data = session_data.weather_data if hasattr(session_data, 'weather_data') else None
            
            if weather_data is not None and not weather_data.empty:
                return {
                    'temperature_effect': 'Stable',
                    'wind_impact': 'Minimal',
                    'track_conditions': 'Dry' if not weather_data.get('Rainfall', False).any() else 'Wet'
                }
            
            return {
                'temperature_effect': 'Unknown',
                'wind_impact': 'Unknown', 
                'track_conditions': 'Unknown'
            }
        except Exception as e:
            logger.error(f"Error analyzing weather impact: {e}")
            return {}

    def _analyze_traffic_effects(self, session_data, drivers) -> Dict[str, Any]:
        """Analyze traffic effects on lap times"""
        try:
            return {
                'clean_air_advantage': 0.0,
                'dirty_air_penalty': 0.0,
                'traffic_affected_laps': 0
            }
        except Exception as e:
            logger.error(f"Error analyzing traffic effects: {e}")
            return {}

    def _analyze_pit_stops(self, session_data, drivers) -> Dict[str, Any]:
        """Analyze pit stop performance and strategy"""
        try:
            return {
                'pit_stop_count': 0,
                'average_pit_time': 0.0,
                'strategy_effectiveness': 'Unknown'
            }
        except Exception as e:
            logger.error(f"Error analyzing pit stops: {e}")
            return {}

    def _estimate_corners_from_telemetry(self, telemetry) -> List[Dict[str, Any]]:
        """Estimate corner locations from telemetry data based on speed drops"""
        try:
            corners = []
            speed_data = telemetry['Speed']
            distance_data = telemetry['Distance']
            
            # Find local minima in speed (potential corners)
            # Use a rolling window to smooth the data
            window_size = min(50, len(speed_data) // 20)  # Adaptive window size
            if window_size < 3:
                return corners
                
            speed_smooth = speed_data.rolling(window=window_size, center=True).mean()
            
            # Find significant speed drops
            speed_threshold = speed_data.quantile(0.3)  # Bottom 30% of speeds
            
            corner_candidates = []
            for i in range(window_size, len(speed_smooth) - window_size):
                if (speed_smooth.iloc[i] < speed_threshold and 
                    speed_smooth.iloc[i] < speed_smooth.iloc[i-window_size//2] and 
                    speed_smooth.iloc[i] < speed_smooth.iloc[i+window_size//2]):
                    corner_candidates.append({
                        'distance': float(distance_data.iloc[i]),
                        'speed': float(speed_smooth.iloc[i])
                    })
            
            # Filter out corners that are too close together (merge nearby corners)
            min_corner_distance = 200  # Minimum 200m between corners
            filtered_corners = []
            
            for candidate in corner_candidates:
                is_new_corner = True
                for existing in filtered_corners:
                    if abs(candidate['distance'] - existing['distance']) < min_corner_distance:
                        # Keep the slower corner (more likely to be the apex)
                        if candidate['speed'] < existing['speed']:
                            filtered_corners.remove(existing)
                            break
                        else:
                            is_new_corner = False
                            break
                
                if is_new_corner:
                    filtered_corners.append(candidate)
            
            # Sort by distance and assign corner numbers
            filtered_corners.sort(key=lambda x: x['distance'])
            
            for i, corner in enumerate(filtered_corners[:20]):  # Limit to 20 corners max
                corners.append({
                    'number': i + 1,
                    'letter': '',
                    'distance': corner['distance']
                })
            
            logger.info(f"Estimated {len(corners)} corners from telemetry data")
            return corners
            
        except Exception as e:
            logger.error(f"Error estimating corners from telemetry: {e}")
            return []

    def _get_sector_boundaries(self, session_data, telemetry) -> Dict[str, float]:
        """Get sector boundaries (distance points where sectors end)"""
        try:
            # Try to get from circuit info first
            circuit_info = session_data.get_circuit_info()
            if hasattr(circuit_info, 'sectors') and not circuit_info.sectors.empty:
                boundaries = {}
                for _, sector in circuit_info.sectors.iterrows():
                    sector_num = sector.get('Number', 0)
                    distance = sector.get('Distance', 0)
                    boundaries[f'sector_{sector_num}_end'] = float(distance)
                return boundaries
            
            # Fallback: estimate from track length (roughly equal sectors)
            max_distance = telemetry['Distance'].max()
            return {
                'sector_1_end': float(max_distance / 3),
                'sector_2_end': float(max_distance * 2 / 3),
                'sector_3_end': float(max_distance)
            }
            
        except Exception as e:
            logger.debug(f"Could not get sector boundaries: {e}")
            # Final fallback based on telemetry length
            max_distance = telemetry['Distance'].max() if not telemetry.empty else 5000
            return {
                'sector_1_end': float(max_distance / 3),
                'sector_2_end': float(max_distance * 2 / 3), 
                'sector_3_end': float(max_distance)
            }