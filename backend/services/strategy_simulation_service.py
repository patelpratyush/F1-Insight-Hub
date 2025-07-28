#!/usr/bin/env python3
"""
F1 Race Strategy Simulation Service
Advanced Monte Carlo simulation engine for F1 race strategy optimization
"""

import uuid
import numpy as np
import pandas as pd
import random
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import os
import json

logger = logging.getLogger(__name__)

@dataclass
class TireCompound:
    """Tire compound characteristics"""
    name: str
    color: str
    base_lap_time: float  # seconds slower than fastest compound
    degradation_rate: float  # seconds per lap degradation
    optimal_window: Tuple[int, int]  # (min_laps, max_laps)
    weather_multiplier: Dict[str, float]  # weather condition multipliers

@dataclass
class PitStop:
    """Pit stop data"""
    lap: int
    stint_number: int
    old_tire: str
    new_tire: str
    pit_time: float
    reason: str  # "strategy", "safety_car", "damage"

@dataclass
class Stint:
    """Racing stint information"""
    stint_number: int
    tire_compound: str
    start_lap: int
    end_lap: int
    laps: int
    avg_lap_time: str
    degradation_level: str
    fuel_corrected_time: float
    tire_performance: Dict[str, float]

@dataclass
class StrategyResult:
    """Complete strategy simulation result"""
    strategy_id: str
    driver: str
    track: str
    weather: str
    total_race_time: str
    total_seconds: float
    predicted_position: int
    confidence: float
    efficiency_score: float
    stints: List[Stint]
    pit_stops: List[PitStop]
    timeline: List[Dict]
    optimization_metrics: Dict
    risk_analysis: Dict

class F1StrategySimulator:
    """Advanced F1 Race Strategy Simulation Engine"""
    
    def __init__(self):
        """Initialize the strategy simulator"""
        self.tire_compounds = self._initialize_tire_compounds()
        self.track_characteristics = self._initialize_track_data()
        self.driver_ratings = self._load_driver_ratings()
        self.team_pit_stop_times = self._initialize_pit_stop_data()
        
    def _initialize_tire_compounds(self) -> Dict[str, TireCompound]:
        """Initialize tire compound characteristics"""
        return {
            "Soft": TireCompound(
                name="Soft",
                color="red",
                base_lap_time=0.0,  # Fastest compound
                degradation_rate=0.08,  # High degradation
                optimal_window=(8, 18),
                weather_multiplier={"dry": 1.0, "light_rain": 1.15, "wet": 1.8, "mixed": 1.25}
            ),
            "Medium": TireCompound(
                name="Medium", 
                color="yellow",
                base_lap_time=0.3,  # 0.3s slower than soft
                degradation_rate=0.05,  # Medium degradation
                optimal_window=(15, 30),
                weather_multiplier={"dry": 1.0, "light_rain": 1.12, "wet": 1.6, "mixed": 1.2}
            ),
            "Hard": TireCompound(
                name="Hard",
                color="white", 
                base_lap_time=0.6,  # 0.6s slower than soft
                degradation_rate=0.03,  # Low degradation
                optimal_window=(25, 45),
                weather_multiplier={"dry": 1.0, "light_rain": 1.1, "wet": 1.4, "mixed": 1.15}
            ),
            "Intermediate": TireCompound(
                name="Intermediate",
                color="green",
                base_lap_time=2.5,  # Much slower in dry
                degradation_rate=0.12,
                optimal_window=(10, 25),
                weather_multiplier={"dry": 1.8, "light_rain": 0.95, "wet": 1.3, "mixed": 1.0}
            ),
            "Wet": TireCompound(
                name="Wet",
                color="blue",
                base_lap_time=4.0,  # Very slow in dry
                degradation_rate=0.15,
                optimal_window=(8, 20),
                weather_multiplier={"dry": 2.5, "light_rain": 1.2, "wet": 1.0, "mixed": 1.1}
            )
        }
    
    def _initialize_track_data(self) -> Dict[str, Dict]:
        """Initialize track-specific characteristics"""
        return {
            "Monaco": {
                "lap_distance": 3.337,
                "total_laps": 78,
                "pit_loss": 23.5,
                "overtaking_difficulty": 0.95,
                "tire_wear_factor": 0.8,
                "safety_car_probability": 0.65,
                "drs_zones": 1
            },
            "Silverstone": {
                "lap_distance": 5.891,
                "total_laps": 52,
                "pit_loss": 18.2,
                "overtaking_difficulty": 0.3,
                "tire_wear_factor": 1.2,
                "safety_car_probability": 0.25,
                "drs_zones": 3
            },
            "Monza": {
                "lap_distance": 5.793,
                "total_laps": 53,
                "pit_loss": 19.8,
                "overtaking_difficulty": 0.2,
                "tire_wear_factor": 0.9,
                "safety_car_probability": 0.15,
                "drs_zones": 3
            },
            "Spa-Francorchamps": {
                "lap_distance": 7.004,
                "total_laps": 44,
                "pit_loss": 22.1,
                "overtaking_difficulty": 0.25,
                "tire_wear_factor": 1.1,
                "safety_car_probability": 0.35,
                "drs_zones": 2
            },
            "Suzuka": {
                "lap_distance": 5.807,
                "total_laps": 53,
                "pit_loss": 20.5,
                "overtaking_difficulty": 0.6,
                "tire_wear_factor": 1.15,
                "safety_car_probability": 0.3,
                "drs_zones": 2
            }
        }
    
    def _load_driver_ratings(self) -> Dict[str, Dict]:
        """Load driver-specific ratings and characteristics for 2025 F1 grid"""
        return {
            # Red Bull Racing - Max + Yuki (Pérez replaced by Tsunoda)
            "VER": {"skill": 0.98, "consistency": 0.95, "tire_management": 0.92, "wet_weather": 0.96},
            "TSU": {"skill": 0.84, "consistency": 0.82, "tire_management": 0.81, "wet_weather": 0.83},
            
            # Ferrari - Lewis Hamilton joins Ferrari!
            "HAM": {"skill": 0.96, "consistency": 0.94, "tire_management": 0.95, "wet_weather": 0.98},
            "LEC": {"skill": 0.94, "consistency": 0.88, "tire_management": 0.87, "wet_weather": 0.91},
            
            # Mercedes - Kimi Antonelli debuts
            "RUS": {"skill": 0.91, "consistency": 0.92, "tire_management": 0.89, "wet_weather": 0.88},
            "ANT": {"skill": 0.82, "consistency": 0.80, "tire_management": 0.78, "wet_weather": 0.75},  # Rookie
            
            # McLaren
            "NOR": {"skill": 0.92, "consistency": 0.89, "tire_management": 0.88, "wet_weather": 0.87},
            "PIA": {"skill": 0.87, "consistency": 0.88, "tire_management": 0.84, "wet_weather": 0.82},
            
            # Aston Martin
            "ALO": {"skill": 0.95, "consistency": 0.93, "tire_management": 0.94, "wet_weather": 0.95},
            "STR": {"skill": 0.83, "consistency": 0.81, "tire_management": 0.80, "wet_weather": 0.79},
            
            # Alpine - Pierre + Franco (Ocon moved to Haas)
            "GAS": {"skill": 0.88, "consistency": 0.87, "tire_management": 0.85, "wet_weather": 0.86},
            "COL": {"skill": 0.82, "consistency": 0.79, "tire_management": 0.77, "wet_weather": 0.75},  # Young talent
            
            # Racing Bulls (formerly RB) - Liam + Isack
            "LAW": {"skill": 0.83, "consistency": 0.81, "tire_management": 0.79, "wet_weather": 0.80},
            "HAD": {"skill": 0.79, "consistency": 0.76, "tire_management": 0.74, "wet_weather": 0.72},  # Rookie
            
            # Williams - Carlos Sainz joins
            "SAI": {"skill": 0.88, "consistency": 0.90, "tire_management": 0.86, "wet_weather": 0.85},
            "ALB": {"skill": 0.85, "consistency": 0.86, "tire_management": 0.82, "wet_weather": 0.81},
            
            # Haas - Esteban + Oliver (Ocon joins, Hülkenberg to Kick Sauber)
            "OCO": {"skill": 0.86, "consistency": 0.85, "tire_management": 0.83, "wet_weather": 0.84},
            "BEA": {"skill": 0.81, "consistency": 0.78, "tire_management": 0.76, "wet_weather": 0.74},  # Rookie
            
            # Kick Sauber - Nico + Gabriel (Hülkenberg joins)
            "HUL": {"skill": 0.86, "consistency": 0.87, "tire_management": 0.84, "wet_weather": 0.82},
            "BOR": {"skill": 0.80, "consistency": 0.77, "tire_management": 0.75, "wet_weather": 0.73}   # Rookie
        }
    
    def _initialize_pit_stop_data(self) -> Dict[str, Dict]:
        """Initialize team-specific pit stop performance for 2025 F1 season"""
        return {
            "Red Bull Racing": {"avg_time": 2.3, "consistency": 0.95, "error_rate": 0.02},
            "Ferrari": {"avg_time": 2.5, "consistency": 0.88, "error_rate": 0.05},
            "Mercedes": {"avg_time": 2.7, "consistency": 0.92, "error_rate": 0.03},
            "McLaren": {"avg_time": 2.6, "consistency": 0.90, "error_rate": 0.04},
            "Aston Martin": {"avg_time": 2.8, "consistency": 0.87, "error_rate": 0.06},
            "Alpine": {"avg_time": 2.9, "consistency": 0.85, "error_rate": 0.07},
            "Racing Bulls": {"avg_time": 2.7, "consistency": 0.88, "error_rate": 0.05},  # Formerly RB/AlphaTauri
            "Williams": {"avg_time": 3.1, "consistency": 0.82, "error_rate": 0.08},
            "Haas": {"avg_time": 3.2, "consistency": 0.80, "error_rate": 0.09},
            "Kick Sauber": {"avg_time": 3.0, "consistency": 0.83, "error_rate": 0.08}  # Formerly Alfa Romeo
        }
    
    def simulate_race_strategy(
        self,
        driver: str,
        track: str,
        weather: str,
        tire_strategy: str,
        safety_car_probability: float = 30.0,
        qualifying_position: int = 10,
        team: str = "Red Bull Racing",
        temperature: float = 25.0,
        monte_carlo_iterations: int = 500
    ) -> StrategyResult:
        """
        Simulate a complete race strategy using Monte Carlo methods
        
        Args:
            driver: Driver code (e.g., 'VER')
            track: Track name
            weather: Weather condition
            tire_strategy: Tire strategy (e.g., 'Soft-Medium-Hard')
            safety_car_probability: Probability of safety car (0-100)
            qualifying_position: Starting grid position
            team: Team name for pit stop performance
            temperature: Track temperature
            monte_carlo_iterations: Number of simulation iterations
        
        Returns:
            StrategyResult with complete race simulation data
        """
        logger.info(f"Simulating race strategy for {driver} at {track}")
        
        # Get track and tire data
        track_data = self.track_characteristics.get(track, self.track_characteristics["Monaco"])
        tire_sequence = tire_strategy.split("-")
        driver_rating = self.driver_ratings.get(driver, {"skill": 0.85, "consistency": 0.85, "tire_management": 0.85, "wet_weather": 0.85})
        team_pit_data = self.team_pit_stop_times.get(team, {"avg_time": 2.8, "consistency": 0.85, "error_rate": 0.06})
        
        # Run Monte Carlo simulation
        simulation_results = []
        for _ in range(monte_carlo_iterations):
            result = self._simulate_single_race(
                driver, track_data, tire_sequence, weather, safety_car_probability,
                qualifying_position, driver_rating, team_pit_data, temperature
            )
            simulation_results.append(result)
        
        # Aggregate results
        avg_time = np.mean([r['total_seconds'] for r in simulation_results])
        position_distribution = [r['position'] for r in simulation_results]
        avg_position = np.mean(position_distribution)
        position_confidence = 1.0 - (np.std(position_distribution) / 20.0)  # Normalize by grid size
        
        # Build detailed result
        best_simulation = min(simulation_results, key=lambda x: x['total_seconds'])
        
        stints = self._build_stint_analysis(best_simulation['stints'], tire_sequence)
        pit_stops = self._build_pit_stop_analysis(best_simulation['pit_stops'])
        timeline = self._build_race_timeline(best_simulation['lap_times'], pit_stops)
        
        strategy_result = StrategyResult(
            strategy_id=str(uuid.uuid4()),
            driver=driver,
            track=track,
            weather=weather,
            total_race_time=self._format_race_time(avg_time),
            total_seconds=avg_time,
            predicted_position=int(round(avg_position)),
            confidence=max(0.6, min(0.98, position_confidence)),
            efficiency_score=self._calculate_efficiency_score(avg_time, track_data, tire_sequence),
            stints=stints,
            pit_stops=pit_stops,
            timeline=timeline,
            optimization_metrics=self._calculate_optimization_metrics(simulation_results),
            risk_analysis=self._calculate_risk_analysis(simulation_results, weather, safety_car_probability)
        )
        
        logger.info(f"Strategy simulation completed: {strategy_result.predicted_position} position, {strategy_result.efficiency_score:.1f}% efficiency")
        return strategy_result
    
    def _simulate_single_race(
        self, driver: str, track_data: Dict, tire_sequence: List[str], 
        weather: str, safety_car_prob: float, start_pos: int,
        driver_rating: Dict, team_pit_data: Dict, temperature: float
    ) -> Dict:
        """Simulate a single race iteration"""
        
        total_laps = track_data['total_laps']
        pit_loss = track_data['pit_loss']
        
        # Initialize race state
        current_position = start_pos
        total_time = 0.0
        lap_times = []
        stints = []
        pit_stops = []
        current_tire = tire_sequence[0]
        stint_start = 1
        stint_number = 1
        
        # Calculate optimal pit windows
        pit_windows = self._calculate_pit_windows(tire_sequence, total_laps)
        
        for lap in range(1, total_laps + 1):
            # Check if pit stop is needed
            if stint_number < len(tire_sequence) and lap in pit_windows[stint_number - 1]:
                # Execute pit stop
                pit_time = self._simulate_pit_stop(team_pit_data, weather)
                old_tire = current_tire
                current_tire = tire_sequence[stint_number]
                
                # Record stint
                stint_laps = lap - stint_start
                stints.append({
                    'stint': stint_number,
                    'tire': old_tire,
                    'start_lap': stint_start,
                    'end_lap': lap - 1,
                    'laps': stint_laps,
                    'avg_lap_time': np.mean(lap_times[stint_start-1:lap-1]) if lap_times else 90.0
                })
                
                # Record pit stop
                pit_stops.append({
                    'lap': lap,
                    'stint': stint_number,
                    'old_tire': old_tire,
                    'new_tire': current_tire,
                    'pit_time': pit_time,
                    'reason': 'strategy'
                })
                
                total_time += pit_time
                stint_start = lap + 1
                stint_number += 1
            
            # Simulate lap time
            base_lap_time = 90.0  # Base lap time in seconds
            lap_time = self._calculate_lap_time(
                base_lap_time, current_tire, lap - stint_start + 1, weather, 
                driver_rating, temperature, track_data
            )
            
            # Safety car check
            if random.random() < (safety_car_prob / 100.0) / total_laps:
                lap_time += random.uniform(20, 40)  # Safety car adds time
            
            lap_times.append(lap_time)
            total_time += lap_time
        
        # Record final stint
        if stint_start <= total_laps:
            stints.append({
                'stint': stint_number,
                'tire': current_tire,
                'start_lap': stint_start,
                'end_lap': total_laps,
                'laps': total_laps - stint_start + 1,
                'avg_lap_time': np.mean(lap_times[stint_start-1:]) if lap_times else 90.0
            })
        
        # Calculate final position (simplified)
        time_penalty = (start_pos - 1) * 0.3  # Starting position penalty/advantage
        final_position = max(1, min(20, start_pos + random.randint(-3, 3) + int(time_penalty)))
        
        return {
            'total_seconds': total_time,
            'position': final_position,
            'stints': stints,
            'pit_stops': pit_stops,
            'lap_times': lap_times
        }
    
    def _calculate_pit_windows(self, tire_sequence: List[str], total_laps: int) -> List[range]:
        """Calculate optimal pit stop windows for each stint"""
        windows = []
        laps_per_stint = total_laps // len(tire_sequence)
        
        for i, tire in enumerate(tire_sequence[:-1]):  # Exclude last tire
            tire_data = self.tire_compounds[tire]
            optimal_min, optimal_max = tire_data.optimal_window
            
            # Calculate pit window based on tire optimal window
            stint_start = i * laps_per_stint + 1
            window_start = stint_start + max(8, optimal_min)
            window_end = min(stint_start + laps_per_stint + 5, stint_start + optimal_max)
            
            windows.append(range(window_start, window_end + 1))
        
        return windows
    
    def _simulate_pit_stop(self, team_data: Dict, weather: str) -> float:
        """Simulate pit stop time with variability"""
        base_time = team_data['avg_time']
        consistency = team_data['consistency']
        error_rate = team_data['error_rate']
        
        # Add variability based on team consistency
        variation = np.random.normal(0, (1 - consistency) * 0.5)
        pit_time = base_time + variation
        
        # Weather penalty
        weather_multiplier = {"dry": 1.0, "light_rain": 1.1, "wet": 1.3, "mixed": 1.15}
        pit_time *= weather_multiplier.get(weather, 1.0)
        
        # Chance of error (longer pit stop)
        if random.random() < error_rate:
            pit_time += random.uniform(3, 8)  # Major error
        
        return max(2.0, pit_time)  # Minimum 2 seconds
    
    def _calculate_lap_time(
        self, base_time: float, tire: str, tire_age: int, weather: str,
        driver_rating: Dict, temperature: float, track_data: Dict
    ) -> float:
        """Calculate realistic lap time based on multiple factors"""
        
        tire_data = self.tire_compounds[tire]
        
        # Base tire performance
        lap_time = base_time + tire_data.base_lap_time
        
        # Tire degradation
        degradation = tire_data.degradation_rate * tire_age
        lap_time += degradation
        
        # Weather impact
        weather_mult = tire_data.weather_multiplier.get(weather, 1.0)
        lap_time *= weather_mult
        
        # Driver skill impact
        skill_factor = (2.0 - driver_rating['skill'])  # Better drivers have lower times
        lap_time *= skill_factor
        
        # Tire management skill
        if tire_age > 15:  # Older tires benefit more from tire management
            management_factor = (2.0 - driver_rating['tire_management'])
            lap_time *= (management_factor * 0.3 + 0.7)
        
        # Temperature effects
        optimal_temp = 25.0
        temp_deviation = abs(temperature - optimal_temp) / 30.0
        lap_time += temp_deviation * 0.5
        
        # Track-specific tire wear
        wear_factor = track_data.get('tire_wear_factor', 1.0)
        if tire_age > 10:
            lap_time += (tire_age - 10) * 0.02 * wear_factor
        
        # Add random variation (driver/car inconsistency)
        consistency = driver_rating['consistency']
        variation = np.random.normal(0, (1 - consistency) * 0.3)
        lap_time += variation
        
        return max(60.0, lap_time)  # Minimum reasonable lap time
    
    def _build_stint_analysis(self, raw_stints: List[Dict], tire_sequence: List[str]) -> List[Stint]:
        """Build detailed stint analysis"""
        stints = []
        for stint_data in raw_stints:
            stint = Stint(
                stint_number=stint_data['stint'],
                tire_compound=stint_data['tire'],
                start_lap=stint_data['start_lap'],
                end_lap=stint_data['end_lap'],
                laps=stint_data['laps'],
                avg_lap_time=self._format_lap_time(stint_data['avg_lap_time']),
                degradation_level=self._categorize_degradation(stint_data['laps'], stint_data['tire']),
                fuel_corrected_time=stint_data['avg_lap_time'] - (stint_data['laps'] * 0.03),  # Fuel correction
                tire_performance=self._analyze_tire_performance(stint_data)
            )
            stints.append(stint)
        return stints
    
    def _build_pit_stop_analysis(self, raw_pit_stops: List[Dict]) -> List[PitStop]:
        """Build detailed pit stop analysis"""
        pit_stops = []
        for stop_data in raw_pit_stops:
            pit_stop = PitStop(
                lap=stop_data['lap'],
                stint_number=stop_data['stint'],
                old_tire=stop_data['old_tire'],
                new_tire=stop_data['new_tire'],
                pit_time=stop_data['pit_time'],
                reason=stop_data['reason']
            )
            pit_stops.append(pit_stop)
        return pit_stops
    
    def _build_race_timeline(self, lap_times: List[float], pit_stops: List[PitStop]) -> List[Dict]:
        """Build interactive race timeline data"""
        timeline = []
        cumulative_time = 0.0
        
        for lap, lap_time in enumerate(lap_times, 1):
            cumulative_time += lap_time
            
            # Check if there's a pit stop on this lap
            pit_stop = next((ps for ps in pit_stops if ps.lap == lap), None)
            
            timeline_entry = {
                'lap': lap,
                'lap_time': self._format_lap_time(lap_time),
                'cumulative_time': self._format_race_time(cumulative_time),
                'is_pit_lap': pit_stop is not None,
                'pit_stop': asdict(pit_stop) if pit_stop else None,
                'relative_time': cumulative_time
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    def _categorize_degradation(self, stint_laps: int, tire_compound: str) -> str:
        """Categorize tire degradation level"""
        tire_data = self.tire_compounds[tire_compound]
        optimal_min, optimal_max = tire_data.optimal_window
        
        if stint_laps <= optimal_min:
            return "Low"
        elif stint_laps <= optimal_max:
            return "Medium" 
        else:
            return "High"
    
    def _analyze_tire_performance(self, stint_data: Dict) -> Dict[str, float]:
        """Analyze tire performance metrics"""
        return {
            'grip_level': max(0.1, 1.0 - (stint_data['laps'] * 0.02)),
            'consistency': max(0.3, 1.0 - (stint_data['laps'] * 0.015)),
            'temperature_sensitivity': 0.8 if stint_data['tire'] == 'Soft' else 0.6
        }
    
    def _calculate_efficiency_score(self, race_time: float, track_data: Dict, tire_strategy: List[str]) -> float:
        """Calculate strategy efficiency score (0-100)"""
        # Baseline: 3-stop soft-medium-hard strategy
        baseline_time = track_data['total_laps'] * 90.0 + (len(tire_strategy) - 1) * track_data['pit_loss']
        
        efficiency = max(0, (baseline_time - race_time) / baseline_time * 100)
        return min(100, max(0, efficiency + 70))  # Scale to 70-100 range
    
    def _calculate_optimization_metrics(self, simulation_results: List[Dict]) -> Dict:
        """Calculate strategy optimization metrics"""
        times = [r['total_seconds'] for r in simulation_results]
        positions = [r['position'] for r in simulation_results]
        
        return {
            'time_consistency': 1.0 - (np.std(times) / np.mean(times)),
            'position_stability': 1.0 - (np.std(positions) / 20.0),
            'best_case_time': min(times),
            'worst_case_time': max(times),
            'median_position': np.median(positions),
            'podium_probability': len([p for p in positions if p <= 3]) / len(positions)
        }
    
    def _calculate_risk_analysis(self, simulation_results: List[Dict], weather: str, safety_car_prob: float) -> Dict:
        """Calculate strategy risk analysis"""
        positions = [r['position'] for r in simulation_results]
        
        return {
            'weather_risk': 'High' if weather in ['wet', 'mixed'] else 'Medium' if weather == 'light_rain' else 'Low',
            'safety_car_risk': 'High' if safety_car_prob > 50 else 'Medium' if safety_car_prob > 25 else 'Low',
            'position_volatility': np.std(positions),
            'dnf_probability': len([p for p in positions if p > 18]) / len(positions),
            'points_probability': len([p for p in positions if p <= 10]) / len(positions),
            'strategy_robustness': 1.0 - (np.std(positions) / 20.0)
        }
    
    def _format_lap_time(self, seconds: float) -> str:
        """Format lap time as M:SS.SSS"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    
    def _format_race_time(self, seconds: float) -> str:
        """Format race time as H:MM:SS.SSS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:06.3f}"
    
    def compare_strategies(
        self, driver: str, track: str, weather: str, strategies: List[str],
        safety_car_probability: float = 30.0, qualifying_position: int = 10
    ) -> Dict[str, StrategyResult]:
        """Compare multiple tire strategies"""
        results = {}
        for strategy in strategies:
            result = self.simulate_race_strategy(
                driver, track, weather, strategy, safety_car_probability, qualifying_position
            )
            results[strategy] = result
        return results
    
    def optimize_strategy(
        self, driver: str, track: str, weather: str, constraints: Dict = None
    ) -> Tuple[str, StrategyResult]:
        """Find optimal strategy given constraints"""
        # Common F1 strategies to test
        common_strategies = [
            "Soft-Medium-Hard",
            "Medium-Hard-Hard",
            "Soft-Soft-Medium", 
            "Medium-Medium-Hard",
            "Hard-Hard-Medium",
            "Soft-Medium-Medium"
        ]
        
        if weather in ['wet', 'mixed']:
            common_strategies.extend([
                "Intermediate-Soft-Medium",
                "Wet-Intermediate-Medium",
                "Intermediate-Intermediate-Soft"
            ])
        
        best_strategy = None
        best_result = None
        best_score = float('inf')
        
        for strategy in common_strategies:
            try:
                result = self.simulate_race_strategy(driver, track, weather, strategy)
                # Score based on position and time (lower is better)
                score = result.predicted_position * 1000 + result.total_seconds
                
                if score < best_score:
                    best_score = score
                    best_strategy = strategy
                    best_result = result
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed: {e}")
                continue
        
        return best_strategy, best_result

# Global service instance
strategy_simulator = F1StrategySimulator()