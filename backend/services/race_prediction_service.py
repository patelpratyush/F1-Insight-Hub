#!/usr/bin/env python3
"""
Race Prediction Service
Provides full grid race predictions using enhanced ensemble models with weather integration.
"""

import pandas as pd
import numpy as np
import os
import logging
import pickle
from typing import Dict, List, Optional, Tuple
from .enhanced_ensemble_service import enhanced_ensemble_service
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RacePredictionService:
    def __init__(self):
        """Initialize the race prediction service"""
        self.ensemble_service = enhanced_ensemble_service
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'f1_data.csv')
        self.fastf1_cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
        
        # Driver roster for 2025 season
        self.drivers_2025 = {
            # Red Bull Racing - Max + Yuki (Pérez replaced by Tsunoda)
            'VER': {'name': 'Max Verstappen', 'team': 'Red Bull Racing Honda RBPT', 'number': 1},
            'TSU': {'name': 'Yuki Tsunoda', 'team': 'Red Bull Racing Honda RBPT', 'number': 22},
            
            # Ferrari - Lewis Hamilton joins Ferrari!
            'HAM': {'name': 'Lewis Hamilton', 'team': 'Scuderia Ferrari', 'number': 44},
            'LEC': {'name': 'Charles Leclerc', 'team': 'Scuderia Ferrari', 'number': 16},
            
            # Mercedes - Kimi Antonelli debuts
            'RUS': {'name': 'George Russell', 'team': 'Mercedes', 'number': 63},
            'ANT': {'name': 'Kimi Antonelli', 'team': 'Mercedes', 'number': 12},
            
            # McLaren
            'NOR': {'name': 'Lando Norris', 'team': 'McLaren Mercedes', 'number': 4},
            'PIA': {'name': 'Oscar Piastri', 'team': 'McLaren Mercedes', 'number': 81},
            
            # Aston Martin
            'ALO': {'name': 'Fernando Alonso', 'team': 'Aston Martin Aramco Mercedes', 'number': 14},
            'STR': {'name': 'Lance Stroll', 'team': 'Aston Martin Aramco Mercedes', 'number': 18},
            
            # Alpine - Pierre + Franco (Ocon moved to Haas)
            'GAS': {'name': 'Pierre Gasly', 'team': 'BWT Alpine F1 Team', 'number': 10},
            'COL': {'name': 'Franco Colapinto', 'team': 'BWT Alpine F1 Team', 'number': 43},
            
            # Racing Bulls (formerly RB) - Liam + Isack
            'LAW': {'name': 'Liam Lawson', 'team': 'Racing Bulls F1 Team', 'number': 30},
            'HAD': {'name': 'Isack Hadjar', 'team': 'Racing Bulls F1 Team', 'number': 6},
            
            # Williams - Carlos Sainz joins
            'SAI': {'name': 'Carlos Sainz', 'team': 'Williams Mercedes', 'number': 55},
            'ALB': {'name': 'Alexander Albon', 'team': 'Williams Mercedes', 'number': 23},
            
            # Haas - Esteban + Oliver (Ocon joins, Hülkenberg to Kick Sauber)
            'OCO': {'name': 'Esteban Ocon', 'team': 'MoneyGram Haas F1 Team', 'number': 31},
            'BEA': {'name': 'Oliver Bearman', 'team': 'MoneyGram Haas F1 Team', 'number': 38},
            
            # Kick Sauber - Nico + Gabriel (Hülkenberg joins)
            'HUL': {'name': 'Nico Hülkenberg', 'team': 'Kick Sauber F1 Team', 'number': 27},
            'BOR': {'name': 'Gabriel Bortoleto', 'team': 'Kick Sauber F1 Team', 'number': 5}
        }
        
        # Weather impact factors for different conditions
        self.weather_effects = {
            'Dry': {
                'base_multiplier': 1.0,
                'driver_variance': 0.1
            },
            'Light Rain': {
                'base_multiplier': 1.15,
                'driver_variance': 0.25,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO', 'NOR']  # Better in wet
            },
            'Heavy Rain': {
                'base_multiplier': 1.35,
                'driver_variance': 0.4,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO']
            },
            'Wet': {
                'base_multiplier': 1.25,
                'driver_variance': 0.3,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO', 'GAS']
            },
            'Mixed': {
                'base_multiplier': 1.2,
                'driver_variance': 0.35,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO', 'NOR', 'GAS']
            },
            'Dry to Light Rain': {
                'base_multiplier': 1.1,
                'driver_variance': 0.3,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO', 'NOR'],
                'strategy_impact': True  # Affects tire strategy
            },
            'Light Rain to Dry': {
                'base_multiplier': 1.08,
                'driver_variance': 0.28,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO', 'NOR'],
                'strategy_impact': True
            },
            'Dry to Heavy Rain': {
                'base_multiplier': 1.3,
                'driver_variance': 0.45,
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO'],
                'strategy_impact': True,
                'chaos_factor': 0.2  # More unpredictable
            },
            'Variable': {
                'base_multiplier': 1.25,
                'driver_variance': 0.5,  # Highest uncertainty
                'skilled_drivers': ['VER', 'HAM', 'RUS', 'ALO'],
                'strategy_impact': True,
                'chaos_factor': 0.3
            }
        }
        
        # Car/Team performance ratings will be calculated from data
        self.car_performance = {}
        self.driver_performance = {}
        
        # Load historical data for driver form analysis
        self._load_historical_data()
        
        # Load 2025 FastF1 cache data for accurate performance ratings
        self._load_2025_fastf1_data()
    
    def _load_historical_data(self):
        """Load historical F1 data and calculate performance ratings"""
        try:
            if os.path.exists(self.data_file):
                self.historical_data = pd.read_csv(self.data_file)
                logger.info(f"Loaded {len(self.historical_data)} historical records")
                
                # Calculate data-driven performance ratings
                self._calculate_car_performance_ratings()
                self._calculate_driver_performance_ratings()
                
            else:
                logger.warning("Historical data file not found - will rely on 2025 FastF1 data")
                self.historical_data = pd.DataFrame()
                # Don't set fallback ratings here - let 2025 data take priority
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            self.historical_data = pd.DataFrame()
            # Don't set fallback ratings here - let 2025 data take priority
    
    def _load_2025_fastf1_data(self):
        """Load and analyze 2025 FastF1 cache data for accurate performance ratings"""
        try:
            # Use the standardized cache directory
            cache_dir = self.fastf1_cache_dir
            
            if not os.path.exists(cache_dir):
                logger.warning(f"FastF1 cache directory not found: {cache_dir}")
                return
            
            # Look for 2025 race data
            year_2025_dir = os.path.join(cache_dir, '2025')
            if not os.path.exists(year_2025_dir):
                logger.warning("No 2025 FastF1 data found")
                return
            
            race_results = []
            races_processed = 0
            
            # Process each 2025 race
            for race_folder in sorted(os.listdir(year_2025_dir)):
                race_path = os.path.join(year_2025_dir, race_folder)
                if not os.path.isdir(race_path):
                    continue
                    
                # Look for race session data
                for session_folder in sorted(os.listdir(race_path)):
                    if session_folder.endswith('_Race'):
                        session_path = os.path.join(race_path, session_folder)
                        
                        # Load timing app data (most reliable for race results)
                        timing_file = os.path.join(session_path, 'timing_app_data.ff1pkl')
                        if os.path.exists(timing_file):
                            try:
                                with open(timing_file, 'rb') as f:
                                    cache_data = pickle.load(f)
                                
                                if 'data' in cache_data:
                                    timing_data = cache_data['data']
                                    race_name = race_folder.replace('2025-', '').replace('_', ' ')
                                    race_date = race_folder.split('_')[0]
                                    
                                    # Process timing data to extract race results
                                    self._process_fastf1_timing_data(timing_data, race_name, race_date, race_results)
                                    races_processed += 1
                                    logger.info(f"Loaded 2025 race data: {race_name}")
                                    
                            except Exception as e:
                                logger.warning(f"Could not load timing data from {timing_file}: {e}")
                        
                        break  # Only process main race, not sprint
            
            if race_results:
                self.race_2025_results = pd.DataFrame(race_results)
                logger.info(f"Successfully loaded {len(race_results)} driver results from {races_processed} 2025 races")
                
                # Calculate 2025-specific performance ratings
                self._calculate_2025_performance_ratings()
            else:
                logger.warning("No 2025 race results found in FastF1 cache - using fallback ratings")
                self._set_fallback_ratings()
                
        except Exception as e:
            logger.error(f"Error loading 2025 FastF1 data: {e}")
    
    def _process_fastf1_timing_data(self, timing_data, race_name, race_date, race_results):
        """Process FastF1 timing app data to extract race results"""
        try:
            if not hasattr(timing_data, 'empty') or timing_data.empty:
                return
            
            # Group by driver and get their final position and best lap times
            driver_results = {}
            
            for _, row in timing_data.iterrows():
                driver_num = str(row.get('Driver', ''))
                if driver_num and driver_num != 'nan':
                    lap_number = row.get('LapNumber', 0)
                    
                    # Only consider valid race laps (not outlaps, practice, etc.)
                    if pd.notna(lap_number) and lap_number > 0:
                        if driver_num not in driver_results:
                            driver_results[driver_num] = {
                                'lap_times': [],
                                'compounds': [],
                                'stints': []
                            }
                        
                        # Collect lap time if valid
                        lap_time = row.get('LapTime')
                        if pd.notna(lap_time):
                            driver_results[driver_num]['lap_times'].append(lap_time)
                        
                        # Collect tire compound
                        compound = row.get('Compound', '')
                        if compound:
                            driver_results[driver_num]['compounds'].append(compound)
                        
                        # Collect stint info
                        stint = row.get('Stint', 0)
                        if pd.notna(stint):
                            driver_results[driver_num]['stints'].append(stint)
            
            # Map driver numbers to codes and calculate positions
            final_results = []
            for driver_num, data in driver_results.items():
                if data['lap_times']:  # Only include drivers who completed laps
                    # Find driver code from our 2025 roster
                    driver_code = None
                    driver_name = None
                    team = None
                    
                    for code, info in self.drivers_2025.items():
                        if str(info['number']) == driver_num:
                            driver_code = code
                            driver_name = info['name']
                            team = info['team']
                            break
                    
                    if driver_code:
                        # Calculate average lap time for performance assessment
                        avg_lap_time = sum(data['lap_times'], pd.Timedelta(0)) / len(data['lap_times'])
                        best_lap_time = min(data['lap_times']) if data['lap_times'] else pd.Timedelta(0)
                        
                        final_results.append({
                            'driver_code': driver_code,
                            'driver_name': driver_name,
                            'team': team,
                            'avg_lap_time': avg_lap_time,
                            'best_lap_time': best_lap_time,
                            'total_laps': len(data['lap_times']),
                            'compounds_used': len(set(data['compounds'])) if data['compounds'] else 1,
                            'stints': max(data['stints']) if data['stints'] else 1
                        })
            
            # Sort by average lap time to assign positions (fastest first)
            final_results.sort(key=lambda x: x['avg_lap_time'])
            
            # Create race results with positions
            for position, result in enumerate(final_results, 1):
                race_results.append({
                    'race_name': race_name,
                    'race_date': race_date,
                    'driver': result['driver_code'],
                    'driver_name': result['driver_name'],
                    'team': result['team'],
                    'position': position,
                    'grid_position': position,  # Approximation
                    'points': self._calculate_points_for_position(position),
                    'status': 'Finished',
                    'avg_lap_time': result['avg_lap_time'].total_seconds(),
                    'best_lap_time': result['best_lap_time'].total_seconds(),
                    'total_laps': result['total_laps'],
                    'compounds_used': result['compounds_used'],
                    'stints': result['stints']
                })
                
        except Exception as e:
            logger.warning(f"Error processing FastF1 timing data for {race_name}: {e}")
    
    def _process_position_data(self, position_data, race_name, race_date, race_results):
        """Process FastF1 position data to extract race results"""
        try:
            # Position data is typically a DataFrame with driver positions over time
            if hasattr(position_data, 'iloc') and len(position_data) > 0:
                # Get final positions (last recorded positions)
                final_positions = position_data.iloc[-1]
                
                for driver_code, position in final_positions.items():
                    if pd.notna(position) and position > 0:
                        race_results.append({
                            'race_name': race_name,
                            'race_date': race_date,
                            'driver': driver_code,
                            'driver_name': self.drivers_2025.get(driver_code, {}).get('name', driver_code),
                            'team': self.drivers_2025.get(driver_code, {}).get('team', 'Unknown'),
                            'position': int(position),
                            'grid_position': int(position),  # Approximation
                            'points': self._calculate_points_for_position(int(position)),
                            'status': 'Finished'
                        })
        except Exception as e:
            logger.warning(f"Error processing position data for {race_name}: {e}")
    
    def _process_timing_data(self, timing_data, race_name, race_date, race_results):
        """Process FastF1 timing data to extract race results"""
        try:
            # Extended timing data contains detailed lap-by-lap information
            if hasattr(timing_data, 'keys'):
                for driver_code, driver_timing in timing_data.items():
                    if isinstance(driver_timing, dict) and 'Position' in driver_timing:
                        position = driver_timing.get('Position', 0)
                        if position > 0:
                            race_results.append({
                                'race_name': race_name,
                                'race_date': race_date,
                                'driver': driver_code,
                                'driver_name': self.drivers_2025.get(driver_code, {}).get('name', driver_code),
                                'team': self.drivers_2025.get(driver_code, {}).get('team', 'Unknown'),
                                'position': int(position),
                                'grid_position': driver_timing.get('GridPosition', int(position)),
                                'points': self._calculate_points_for_position(int(position)),
                                'status': driver_timing.get('Status', 'Finished')
                            })
        except Exception as e:
            logger.warning(f"Error processing timing data for {race_name}: {e}")
    
    def _calculate_points_for_position(self, position):
        """Calculate F1 points for a given position"""
        points_map = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
        return points_map.get(position, 0)
    
    def _calculate_2025_performance_ratings(self):
        """Calculate performance ratings from actual 2025 race results"""
        if not hasattr(self, 'race_2025_results') or self.race_2025_results.empty:
            logger.warning("No 2025 results available for performance calculation")
            return
        
        try:
            # Calculate team performance from 2025 results
            team_stats = {}
            
            for team in self.race_2025_results['team'].unique():
                if pd.isna(team) or team == '':
                    continue
                    
                team_data = self.race_2025_results[self.race_2025_results['team'] == team]
                
                # Basic performance metrics
                avg_position = team_data['position'].mean()
                avg_grid = team_data['grid_position'].mean()
                avg_points = team_data['points'].mean()
                finish_rate = len(team_data[team_data['position'] > 0]) / len(team_data)
                
                # Calculate pace rating (inverse of average position, normalized)
                # Best team (lowest avg position) gets highest rating
                pace_rating = max(0.5, min(0.95, 1.0 - ((avg_position - 1) / 19) * 0.45))
                
                # Position gain/loss from grid to race
                position_changes = team_data['position'] - team_data['grid_position']
                avg_position_change = position_changes.mean()
                strategy_rating = max(0.5, min(0.95, 0.75 + (avg_position_change * -0.03)))
                
                # Reliability rating
                reliability = max(0.6, min(0.95, finish_rate))
                
                team_stats[team] = {
                    'dry_pace': round(pace_rating, 3),
                    'wet_pace': round(pace_rating * 0.98, 3),  # Slightly lower for wet
                    'strategy': round(strategy_rating, 3),
                    'reliability': round(reliability, 3),
                    'avg_position': round(avg_position, 2),
                    'avg_points': round(avg_points, 2)
                }
            
            self.car_performance = team_stats
            logger.info(f"Calculated 2025 performance ratings for {len(team_stats)} teams")
            
            # Log top teams
            sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['dry_pace'], reverse=True)[:5]
            logger.info("Top 5 teams by 2025 performance:")
            for i, (team, stats) in enumerate(sorted_teams):
                logger.info(f"  {i+1}. {team}: {stats['dry_pace']} pace (avg pos: {stats['avg_position']})")
            
            # Calculate driver performance from 2025 results
            driver_stats = {}
            
            for driver in self.race_2025_results['driver_name'].unique():
                if pd.isna(driver) or driver == '':
                    continue
                    
                driver_data = self.race_2025_results[self.race_2025_results['driver_name'] == driver]
                
                # Basic performance metrics
                avg_position = driver_data['position'].mean()
                avg_grid = driver_data['grid_position'].mean()
                avg_points = driver_data['points'].mean()
                finish_rate = len(driver_data[driver_data['position'] > 0]) / len(driver_data)
                
                # Calculate skill rating
                skill_rating = max(0.5, min(0.95, 1.0 - ((avg_position - 1) / 19) * 0.45))
                
                # Race craft (ability to gain positions)
                position_changes = driver_data['position'] - driver_data['grid_position']
                avg_position_change = position_changes.mean()
                race_craft = max(0.5, min(0.95, 0.75 + (avg_position_change * -0.05)))
                
                driver_stats[driver] = {
                    'overall_skill': round(skill_rating, 3),
                    'wet_skill': round(skill_rating * 0.95, 3),  # Slightly lower for wet
                    'race_craft': round(race_craft, 3),
                    'strategy_execution': round(finish_rate, 3),
                    'avg_position': round(avg_position, 2),
                    'avg_points': round(avg_points, 2)
                }
            
            self.driver_performance = driver_stats
            logger.info(f"Calculated 2025 performance ratings for {len(driver_stats)} drivers")
            
            # Log top drivers
            sorted_drivers = sorted(driver_stats.items(), key=lambda x: x[1]['overall_skill'], reverse=True)[:5]
            logger.info("Top 5 drivers by 2025 performance:")
            for i, (driver, stats) in enumerate(sorted_drivers):
                logger.info(f"  {i+1}. {driver}: {stats['overall_skill']} skill (avg pos: {stats['avg_position']})")
                
        except Exception as e:
            logger.error(f"Error calculating 2025 performance ratings: {e}")
            self._set_fallback_ratings()
    
    def _calculate_car_performance_ratings(self):
        """Calculate car/team performance ratings from historical data"""
        if self.historical_data.empty:
            return
        
        try:
            # Focus on recent performance (2024-2025 seasons)
            recent_data = self.historical_data[self.historical_data['season'] >= 2024].copy()
            
            if recent_data.empty:
                logger.warning("No recent data found, using all available data")
                recent_data = self.historical_data.copy()
            
            # Calculate team performance metrics
            team_stats = {}
            
            for team in recent_data['team'].unique():
                team_data = recent_data[recent_data['team'] == team]
                
                # Dry conditions performance
                dry_data = team_data[team_data['weather'] == 'Dry']
                wet_data = team_data[team_data['weather'] != 'Dry']
                
                # Calculate metrics (normalize to 0-1 scale)
                avg_race_pos = team_data['race_position'].mean()
                avg_quali_pos = team_data['qualifying_position'].mean()
                finish_rate = len(team_data[team_data['status'] == 'Finished']) / len(team_data)
                points_per_race = team_data['points'].mean()
                
                # Calculate pace ratings (inverted since lower position = better)
                # Scale: best team gets ~0.95, worst gets ~0.6
                dry_pace = max(0.6, 1.0 - ((avg_race_pos - 1) / 19) * 0.35) if not dry_data.empty else 0.75
                wet_pace = max(0.6, 1.0 - ((wet_data['race_position'].mean() - 1) / 19) * 0.35) if not wet_data.empty else dry_pace
                
                # Strategy rating based on qualifying vs race position improvement
                pos_changes = team_data['race_position'] - team_data['qualifying_position']
                avg_pos_change = pos_changes.mean()
                strategy_rating = max(0.5, min(0.95, 0.75 + (avg_pos_change * -0.05)))  # Negative change = good strategy
                
                # Reliability rating
                reliability = max(0.6, min(0.95, finish_rate))
                
                team_stats[team] = {
                    'dry_pace': round(dry_pace, 3),
                    'wet_pace': round(wet_pace, 3),
                    'strategy': round(strategy_rating, 3),
                    'reliability': round(reliability, 3),
                    'avg_race_pos': round(avg_race_pos, 2),
                    'avg_quali_pos': round(avg_quali_pos, 2),
                    'points_per_race': round(points_per_race, 2)
                }
            
            self.car_performance = team_stats
            logger.info(f"Calculated performance ratings for {len(team_stats)} teams")
            
            # Log top teams for verification
            sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['dry_pace'], reverse=True)
            logger.info("Top 3 teams by dry pace:")
            for i, (team, stats) in enumerate(sorted_teams[:3]):
                logger.info(f"  {i+1}. {team}: {stats['dry_pace']} (avg pos: {stats['avg_race_pos']})")
                
        except Exception as e:
            logger.error(f"Error calculating car performance ratings: {e}")
            self._set_fallback_car_ratings()
    
    def _calculate_driver_performance_ratings(self):
        """Calculate driver performance ratings from historical data"""
        if self.historical_data.empty:
            return
        
        try:
            # Focus on recent performance (2024-2025 seasons)
            recent_data = self.historical_data[self.historical_data['season'] >= 2024].copy()
            
            if recent_data.empty:
                logger.warning("No recent data found for drivers, using all available data")
                recent_data = self.historical_data.copy()
            
            driver_stats = {}
            
            for driver in recent_data['driver'].unique():
                driver_data = recent_data[recent_data['driver'] == driver]
                
                # Basic performance metrics
                avg_race_pos = driver_data['race_position'].mean()
                avg_quali_pos = driver_data['qualifying_position'].mean()
                finish_rate = len(driver_data[driver_data['status'] == 'Finished']) / len(driver_data)
                points_per_race = driver_data['points'].mean()
                
                # Qualifying vs race performance
                pos_changes = driver_data['race_position'] - driver_data['qualifying_position']
                avg_pos_change = pos_changes.mean()
                
                # Wet weather performance
                dry_data = driver_data[driver_data['weather'] == 'Dry']
                wet_data = driver_data[driver_data['weather'] != 'Dry']
                
                dry_avg = dry_data['race_position'].mean() if not dry_data.empty else avg_race_pos
                wet_avg = wet_data['race_position'].mean() if not wet_data.empty else avg_race_pos
                
                # Calculate skill rating (0-1 scale, inverted from position)
                overall_skill = max(0.5, 1.0 - ((avg_race_pos - 1) / 19) * 0.45)
                wet_skill = max(0.5, 1.0 - ((wet_avg - 1) / 19) * 0.45) if not wet_data.empty else overall_skill
                
                # Race craft (ability to gain positions during race)
                race_craft = max(0.5, min(0.95, 0.75 + (avg_pos_change * -0.03)))
                
                # Strategy execution (how well they execute team strategy)
                strategy_execution = max(0.5, min(0.95, 0.7 + (finish_rate * 0.25)))
                
                driver_stats[driver] = {
                    'overall_skill': round(overall_skill, 3),
                    'wet_skill': round(wet_skill, 3),
                    'race_craft': round(race_craft, 3),
                    'strategy_execution': round(strategy_execution, 3),
                    'avg_race_pos': round(avg_race_pos, 2),
                    'avg_quali_pos': round(avg_quali_pos, 2),
                    'points_per_race': round(points_per_race, 2),
                    'finish_rate': round(finish_rate, 3)
                }
            
            self.driver_performance = driver_stats
            logger.info(f"Calculated performance ratings for {len(driver_stats)} drivers")
            
            # Log top drivers for verification
            sorted_drivers = sorted(driver_stats.items(), key=lambda x: x[1]['overall_skill'], reverse=True)
            logger.info("Top 3 drivers by overall skill:")
            for i, (driver, stats) in enumerate(sorted_drivers[:3]):
                logger.info(f"  {i+1}. {driver}: {stats['overall_skill']} (avg pos: {stats['avg_race_pos']})")
                
        except Exception as e:
            logger.error(f"Error calculating driver performance ratings: {e}")
            self._set_fallback_driver_ratings()
    
    def _set_fallback_ratings(self):
        """Set fallback ratings if data calculation fails"""
        self._set_fallback_car_ratings()
        self._set_fallback_driver_ratings()
    
    def _set_fallback_car_ratings(self):
        """Set realistic 2025 season fallback car ratings based on current championship"""
        self.car_performance = {
            # McLaren - Currently dominating 2025 season (Piastri P1, Norris P2)
            'McLaren Mercedes': {'dry_pace': 0.94, 'wet_pace': 0.91, 'strategy': 0.88, 'reliability': 0.87},
            
            # Red Bull - Still competitive but not dominant anymore
            'Red Bull Racing Honda RBPT': {'dry_pace': 0.89, 'wet_pace': 0.92, 'strategy': 0.90, 'reliability': 0.85},
            
            # Mercedes - Competitive midfield with Russell and Antonelli
            'Mercedes': {'dry_pace': 0.85, 'wet_pace': 0.88, 'strategy': 0.83, 'reliability': 0.86},
            
            # Ferrari - Midfield struggles despite Hamilton joining
            'Scuderia Ferrari': {'dry_pace': 0.82, 'wet_pace': 0.80, 'strategy': 0.75, 'reliability': 0.78},
            
            # Williams - Decent midfield with Sainz upgrade
            'Williams Mercedes': {'dry_pace': 0.78, 'wet_pace': 0.76, 'strategy': 0.74, 'reliability': 0.80},
            
            # Haas - Improved with Ocon
            'MoneyGram Haas F1 Team': {'dry_pace': 0.76, 'wet_pace': 0.74, 'strategy': 0.72, 'reliability': 0.77},
            
            # Kick Sauber - Midfield with Hulkenberg experience
            'Kick Sauber F1 Team': {'dry_pace': 0.75, 'wet_pace': 0.73, 'strategy': 0.70, 'reliability': 0.75},
            
            # Alpine - Struggling midfield
            'BWT Alpine F1 Team': {'dry_pace': 0.73, 'wet_pace': 0.72, 'strategy': 0.68, 'reliability': 0.74},
            
            # Racing Bulls - Lower midfield
            'Racing Bulls F1 Team': {'dry_pace': 0.72, 'wet_pace': 0.71, 'strategy': 0.67, 'reliability': 0.73},
            
            # Aston Martin - STRUGGLING (realistic for 2025 - their car is ass)
            'Aston Martin Aramco Mercedes': {'dry_pace': 0.68, 'wet_pace': 0.66, 'strategy': 0.65, 'reliability': 0.70},
        }
        logger.warning("Using realistic 2025 season fallback car performance ratings")
    
    def _set_fallback_driver_ratings(self):
        """Set realistic 2025 season fallback driver ratings based on current performance"""
        self.driver_performance = {
            # McLaren drivers - Currently leading championship
            'Oscar Piastri': {'overall_skill': 0.94, 'wet_skill': 0.88, 'race_craft': 0.92, 'strategy_execution': 0.90},
            'Lando Norris': {'overall_skill': 0.92, 'wet_skill': 0.86, 'race_craft': 0.89, 'strategy_execution': 0.88},
            
            # Top tier drivers
            'Max Verstappen': {'overall_skill': 0.95, 'wet_skill': 0.95, 'race_craft': 0.93, 'strategy_execution': 0.90},
            'Lewis Hamilton': {'overall_skill': 0.88, 'wet_skill': 0.93, 'race_craft': 0.90, 'strategy_execution': 0.85},
            'George Russell': {'overall_skill': 0.86, 'wet_skill': 0.84, 'race_craft': 0.85, 'strategy_execution': 0.87},
            
            # Second tier
            'Charles Leclerc': {'overall_skill': 0.85, 'wet_skill': 0.82, 'race_craft': 0.84, 'strategy_execution': 0.80},
            'Carlos Sainz': {'overall_skill': 0.82, 'wet_skill': 0.79, 'race_craft': 0.83, 'strategy_execution': 0.82},
            'Fernando Alonso': {'overall_skill': 0.84, 'wet_skill': 0.88, 'race_craft': 0.87, 'strategy_execution': 0.85},
            'Yuki Tsunoda': {'overall_skill': 0.79, 'wet_skill': 0.76, 'race_craft': 0.78, 'strategy_execution': 0.75},
            
            # Experienced midfield
            'Alexander Albon': {'overall_skill': 0.78, 'wet_skill': 0.75, 'race_craft': 0.79, 'strategy_execution': 0.80},
            'Pierre Gasly': {'overall_skill': 0.77, 'wet_skill': 0.79, 'race_craft': 0.76, 'strategy_execution': 0.78},
            'Esteban Ocon': {'overall_skill': 0.76, 'wet_skill': 0.74, 'race_craft': 0.75, 'strategy_execution': 0.77},
            'Nico Hülkenberg': {'overall_skill': 0.78, 'wet_skill': 0.80, 'race_craft': 0.77, 'strategy_execution': 0.82},
            
            # Rising stars / Rookies
            'Kimi Antonelli': {'overall_skill': 0.73, 'wet_skill': 0.70, 'race_craft': 0.71, 'strategy_execution': 0.68},
            'Oliver Bearman': {'overall_skill': 0.71, 'wet_skill': 0.68, 'race_craft': 0.70, 'strategy_execution': 0.67},
            'Gabriel Bortoleto': {'overall_skill': 0.70, 'wet_skill': 0.67, 'race_craft': 0.69, 'strategy_execution': 0.66},
            'Franco Colapinto': {'overall_skill': 0.72, 'wet_skill': 0.69, 'race_craft': 0.71, 'strategy_execution': 0.68},
            'Liam Lawson': {'overall_skill': 0.74, 'wet_skill': 0.71, 'race_craft': 0.73, 'strategy_execution': 0.70},
            'Isack Hadjar': {'overall_skill': 0.72, 'wet_skill': 0.69, 'race_craft': 0.71, 'strategy_execution': 0.68},
            
            # Pay drivers / Struggling
            'Lance Stroll': {'overall_skill': 0.68, 'wet_skill': 0.65, 'race_craft': 0.66, 'strategy_execution': 0.67},
        }
        logger.warning("Using realistic 2025 season fallback driver performance ratings")
    
    def _get_field_average_performance(self) -> float:
        """Calculate field average performance from actual 2025 data"""
        if hasattr(self, 'car_performance') and self.car_performance:
            car_performances = [stats.get('dry_pace', 0.75) for stats in self.car_performance.values()]
            return sum(car_performances) / len(car_performances)
        return 0.75  # Default if no data
    
    def _get_team_fallback_rating(self, team: str) -> Dict:
        """Get fallback rating for a specific team"""
        # Create temporary fallback ratings dict
        fallback_car_ratings = {
            'McLaren Mercedes': {'dry_pace': 0.94, 'wet_pace': 0.91, 'strategy': 0.88, 'reliability': 0.87},
            'Red Bull Racing Honda RBPT': {'dry_pace': 0.89, 'wet_pace': 0.92, 'strategy': 0.90, 'reliability': 0.85},
            'Mercedes': {'dry_pace': 0.85, 'wet_pace': 0.88, 'strategy': 0.83, 'reliability': 0.86},
            'Scuderia Ferrari': {'dry_pace': 0.82, 'wet_pace': 0.80, 'strategy': 0.75, 'reliability': 0.78},
            'Williams Mercedes': {'dry_pace': 0.78, 'wet_pace': 0.76, 'strategy': 0.74, 'reliability': 0.80},
            'MoneyGram Haas F1 Team': {'dry_pace': 0.76, 'wet_pace': 0.74, 'strategy': 0.72, 'reliability': 0.77},
            'Kick Sauber F1 Team': {'dry_pace': 0.75, 'wet_pace': 0.73, 'strategy': 0.70, 'reliability': 0.75},
            'BWT Alpine F1 Team': {'dry_pace': 0.73, 'wet_pace': 0.72, 'strategy': 0.68, 'reliability': 0.74},
            'Racing Bulls F1 Team': {'dry_pace': 0.72, 'wet_pace': 0.71, 'strategy': 0.67, 'reliability': 0.73},
            'Aston Martin Aramco Mercedes': {'dry_pace': 0.68, 'wet_pace': 0.66, 'strategy': 0.65, 'reliability': 0.70},
        }
        return fallback_car_ratings.get(team, {'dry_pace': 0.70, 'wet_pace': 0.70, 'strategy': 0.70, 'reliability': 0.75})
    
    def _get_driver_fallback_rating(self, driver_name: str) -> Dict:
        """Get fallback rating for a specific driver"""
        # Create temporary fallback ratings dict based on 2025 performance
        fallback_driver_ratings = {
            'Oscar Piastri': {'overall_skill': 0.94, 'wet_skill': 0.88, 'race_craft': 0.92, 'strategy_execution': 0.90},
            'Lando Norris': {'overall_skill': 0.92, 'wet_skill': 0.86, 'race_craft': 0.89, 'strategy_execution': 0.88},
            'Max Verstappen': {'overall_skill': 0.95, 'wet_skill': 0.95, 'race_craft': 0.93, 'strategy_execution': 0.90},
            'Lewis Hamilton': {'overall_skill': 0.88, 'wet_skill': 0.93, 'race_craft': 0.90, 'strategy_execution': 0.85},
            'George Russell': {'overall_skill': 0.86, 'wet_skill': 0.84, 'race_craft': 0.85, 'strategy_execution': 0.87},
            'Charles Leclerc': {'overall_skill': 0.85, 'wet_skill': 0.82, 'race_craft': 0.84, 'strategy_execution': 0.80},
            'Carlos Sainz': {'overall_skill': 0.82, 'wet_skill': 0.79, 'race_craft': 0.83, 'strategy_execution': 0.82},
            'Fernando Alonso': {'overall_skill': 0.84, 'wet_skill': 0.88, 'race_craft': 0.87, 'strategy_execution': 0.85},
            'Yuki Tsunoda': {'overall_skill': 0.79, 'wet_skill': 0.76, 'race_craft': 0.78, 'strategy_execution': 0.75},
            'Alexander Albon': {'overall_skill': 0.78, 'wet_skill': 0.75, 'race_craft': 0.79, 'strategy_execution': 0.80},
            'Pierre Gasly': {'overall_skill': 0.77, 'wet_skill': 0.79, 'race_craft': 0.76, 'strategy_execution': 0.78},
            'Esteban Ocon': {'overall_skill': 0.76, 'wet_skill': 0.74, 'race_craft': 0.75, 'strategy_execution': 0.77},
            'Nico Hülkenberg': {'overall_skill': 0.78, 'wet_skill': 0.80, 'race_craft': 0.77, 'strategy_execution': 0.82},
            'Kimi Antonelli': {'overall_skill': 0.73, 'wet_skill': 0.70, 'race_craft': 0.71, 'strategy_execution': 0.68},
            'Oliver Bearman': {'overall_skill': 0.71, 'wet_skill': 0.68, 'race_craft': 0.70, 'strategy_execution': 0.67},
            'Gabriel Bortoleto': {'overall_skill': 0.70, 'wet_skill': 0.67, 'race_craft': 0.69, 'strategy_execution': 0.66},
            'Franco Colapinto': {'overall_skill': 0.72, 'wet_skill': 0.69, 'race_craft': 0.71, 'strategy_execution': 0.68},
            'Liam Lawson': {'overall_skill': 0.74, 'wet_skill': 0.71, 'race_craft': 0.73, 'strategy_execution': 0.70},
            'Isack Hadjar': {'overall_skill': 0.72, 'wet_skill': 0.69, 'race_craft': 0.71, 'strategy_execution': 0.68},
            'Lance Stroll': {'overall_skill': 0.68, 'wet_skill': 0.65, 'race_craft': 0.66, 'strategy_execution': 0.67},
        }
        return fallback_driver_ratings.get(driver_name, {'overall_skill': 0.72, 'wet_skill': 0.70, 'race_craft': 0.70, 'strategy_execution': 0.68})
    
    def predict_race_grid(self, race_name: str, weather: str = "Dry", 
                         qualifying_results: Optional[Dict[str, int]] = None,
                         temperature: float = 25.0) -> Dict:
        """
        Predict full race grid results
        
        Args:
            race_name: Name of the race (e.g., "Austrian Grand Prix")
            weather: Weather conditions ("Dry", "Light Rain", "Heavy Rain", "Wet")
            qualifying_results: Optional dict of driver -> qualifying position
            temperature: Track temperature in Celsius
            
        Returns:
            Dict with race predictions, confidence scores, and metadata
        """
        try:
            logger.info(f"Predicting race grid for {race_name} in {weather} conditions")
            
            # Generate baseline predictions for all drivers
            race_predictions = []
            
            for driver_code, driver_info in self.drivers_2025.items():
                try:
                    # Get qualifying position (default to random if not provided)
                    quali_pos = qualifying_results.get(driver_code, np.random.randint(1, 21)) if qualifying_results else np.random.randint(1, 21)
                    
                    # Get driver's recent form
                    driver_form = self._get_driver_form(driver_code, race_name)
                    
                    # Use ensemble service for base prediction
                    base_prediction = self._get_base_race_prediction(
                        driver_code, driver_info['team'], race_name, quali_pos, weather, temperature
                    )
                    
                    # Apply weather effects
                    adjusted_prediction = self._apply_weather_effects(
                        base_prediction, driver_code, driver_info['team'], weather
                    )
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence_score(
                        driver_code, race_name, weather, driver_form
                    )
                    
                    race_predictions.append({
                        'driver_code': driver_code,
                        'driver_name': driver_info['name'],
                        'team': driver_info['team'],
                        'number': driver_info['number'],
                        'predicted_position': adjusted_prediction['position'],
                        'predicted_time': adjusted_prediction['time'],
                        'qualifying_position': quali_pos,
                        'confidence': confidence,
                        'driver_form': driver_form,
                        'weather_impact': adjusted_prediction.get('weather_impact', 0.0)
                    })
                    
                except Exception as e:
                    logger.error(f"Error predicting for driver {driver_code}: {e}")
                    continue
            
            # Sort by predicted position
            race_predictions.sort(key=lambda x: x['predicted_position'])
            
            # Reassign positions to ensure 1-20 ordering
            for i, prediction in enumerate(race_predictions):
                prediction['predicted_position'] = i + 1
                
                # Calculate gap to winner
                if i == 0:
                    prediction['gap_to_winner'] = "Winner"
                else:
                    # Estimate gap based on position difference and track characteristics
                    base_gap = (i * 2.5) + np.random.normal(0, 1.2)  # ~2.5s per position with variance
                    prediction['gap_to_winner'] = f"+{base_gap:.1f}s"
            
            # Calculate race statistics
            race_stats = self._calculate_race_statistics(race_predictions, weather, race_name)
            
            return {
                'success': True,
                'race_name': race_name,
                'weather_conditions': weather,
                'temperature': temperature,
                'predictions': race_predictions,
                'statistics': race_stats,
                'model_info': {
                    'model_type': 'Enhanced Ensemble (XGBoost + RandomForest + NeuralNetwork)',
                    'total_drivers': len(race_predictions),
                    'prediction_timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"Error in race grid prediction: {e}")
            return {
                'success': False,
                'error': str(e),
                'race_name': race_name,
                'weather_conditions': weather
            }
    
    def _get_base_race_prediction(self, driver: str, team: str, race: str, 
                                 quali_pos: int, weather: str, temperature: float) -> Dict:
        """Get base race prediction using ensemble models"""
        try:
            # Create input data for the ensemble model
            input_data = {
                'driver': driver,
                'team': team,
                'race': race,
                'qualifying_position': float(quali_pos),
                'weather': weather,
                'season': 2025,
                'points': 0,  # Default for prediction
                'grid_position': float(quali_pos),
                'status': 'Finished'  # Assume finish for prediction
            }
            
            # Use calculated 2025 performance data - prioritize actual results over fallbacks
            car_stats = self.car_performance.get(team, {})
            driver_full_name = self.drivers_2025.get(driver, {}).get('name', driver)
            driver_stats = self.driver_performance.get(driver_full_name, {})
            
            # If no 2025 data exists, use realistic fallback based on known 2025 performance
            if not car_stats:
                logger.warning(f"No car performance data for {team}, using fallback")
                car_stats = self._get_team_fallback_rating(team)
            if not driver_stats:
                logger.warning(f"No driver performance data for {driver_full_name}, using fallback")
                driver_stats = self._get_driver_fallback_rating(driver_full_name)
            
            # Get car pace rating (most important factor - 80% weight based on 2025 data showing car dominance)
            car_pace = car_stats.get('dry_pace', 0.75) if weather == 'Dry' else car_stats.get('wet_pace', 0.75)
            car_reliability = car_stats.get('reliability', 0.85)
            car_strategy = car_stats.get('strategy', 0.75)
            
            # Get driver skill rating (20% weight - driver less important than car in 2025)
            driver_skill = driver_stats.get('overall_skill', 0.75) if weather == 'Dry' else driver_stats.get('wet_skill', 0.75)
            driver_race_craft = driver_stats.get('race_craft', 0.75)
            
            # Log actual ratings being used for debugging
            logger.debug(f"{driver} ({team}): car_pace={car_pace:.3f}, driver_skill={driver_skill:.3f}")
            
            # Combined performance score (car is dominant factor in 2025)
            combined_performance = (car_pace * 0.8) + (driver_skill * 0.2)
            
            # Calculate expected position based on performance vs field average
            # Use dynamic field average based on actual 2025 data
            field_average = self._get_field_average_performance()
            performance_advantage = combined_performance - field_average
            
            # Scale position changes more aggressively to separate fast/slow cars
            base_position_change = performance_advantage * -15  # Increased from -12
            
            # Add race craft factor (driver's ability to gain positions during race)
            race_craft_bonus = (driver_race_craft - field_average) * 1.5
            
            # Reduce randomness significantly to let data drive predictions
            variance_factor = max(0.3, 1.0 - combined_performance)  # Much less variance for all drivers
            random_factor = np.random.normal(0, variance_factor * 0.8)  # Reduced from *2 to *0.8
            
            # Calculate final position change
            total_position_change = base_position_change + race_craft_bonus + random_factor
            
            # Apply reliability factor (less random, more data-driven)
            reliability_threshold = car_reliability * 0.95  # More conservative reliability
            if np.random.random() > reliability_threshold:
                # Reliability issue - but not as severe
                total_position_change += np.random.uniform(1, 4)  # Reduced from 3-8
            
            predicted_pos = max(1, min(20, quali_pos + total_position_change))
            
            # Apply 2025 season boost for top performers to ensure they finish near the front
            if combined_performance > 0.87:  # Top tier (McLaren level)
                predicted_pos = min(predicted_pos, 5)  # Cap at P5
            elif combined_performance > 0.84:  # Second tier (Mercedes/Ferrari level)
                predicted_pos = min(predicted_pos, 8)  # Cap at P8
            elif combined_performance < 0.75:  # Bottom tier (Aston Martin level)
                predicted_pos = max(predicted_pos, 12)  # Floor at P12
            
            # Calculate race time based on position and car pace
            base_time = 88.0 + (predicted_pos * 0.15) + np.random.normal(0, 0.5)
            time_advantage = (car_pace - 0.75) * -3  # Better cars = faster times
            predicted_time = base_time + time_advantage
            
            # Try ensemble service as enhancement if available
            try:
                if hasattr(self.ensemble_service, 'predict_driver_performance'):
                    ensemble_prediction = self.ensemble_service.predict_driver_performance(
                        driver_code=driver,
                        track=race,
                        weather=weather,
                        team=team
                    )
                    # Blend our data-driven prediction with ensemble (60/40 split)
                    ensemble_pos = ensemble_prediction.get('predicted_race_position', predicted_pos)
                    predicted_pos = (predicted_pos * 0.6) + (ensemble_pos * 0.4)
                    predicted_pos = max(1, min(20, predicted_pos))
            except Exception as e:
                logger.debug(f"Ensemble enhancement failed for {driver}: {e}")
            
            return {
                'position': predicted_pos,
                'time': predicted_time
            }
                
        except Exception as e:
            logger.warning(f"Using fallback prediction for {driver}: {e}")
            # Simple fallback
            position_change = np.random.randint(-5, 6)
            return {
                'position': max(1, min(20, quali_pos + position_change)),
                'time': 90.0 + np.random.normal(0, 2)
            }
    
    def _apply_weather_effects(self, base_prediction: Dict, driver: str, team: str, weather: str) -> Dict:
        """Apply weather condition effects to predictions"""
        if weather == "Dry":
            return base_prediction
        
        weather_data = self.weather_effects.get(weather, self.weather_effects["Dry"])
        
        # Base weather impact
        time_multiplier = weather_data['base_multiplier']
        variance = weather_data['driver_variance']
        
        # Get data-driven driver and car performance
        driver_full_name = self.drivers_2025.get(driver, {}).get('name', driver)
        driver_stats = self.driver_performance.get(driver_full_name, {})
        car_stats = self.car_performance.get(team, {})
        
        # Check if driver is skilled in wet conditions (based on data)
        driver_wet_skill = driver_stats.get('wet_skill', 0.7)
        car_wet_pace = car_stats.get('wet_pace', 0.7)
        
        # Combined wet weather competency (car is more important than driver)
        wet_competency = (car_wet_pace * 0.7) + (driver_wet_skill * 0.3)
        skilled_in_wet = wet_competency > 0.78  # Top ~30% in wet conditions
        
        # Apply chaos factor for variable conditions
        chaos_factor = weather_data.get('chaos_factor', 0.0)
        additional_variance = chaos_factor * np.random.uniform(-2, 2)
        
        # Strategy impact for changing conditions (data-driven)
        strategy_impact = 0.0
        if weather_data.get('strategy_impact', False):
            # Use calculated strategy ratings (car strategy more important than driver)
            driver_strategy = driver_stats.get('strategy_execution', 0.7)
            car_strategy = car_stats.get('strategy', 0.7)
            combined_strategy = (car_strategy * 0.6) + (driver_strategy * 0.4)
            strategy_impact = (combined_strategy - 0.7) * np.random.uniform(-1.5, 1.5)
        
        if skilled_in_wet:
            # Skilled drivers perform relatively better in wet/mixed conditions
            position_improvement = np.random.uniform(-2.5, 0.5) + strategy_impact
            time_penalty = time_multiplier * 0.85  # Less time penalty
        else:
            # Regular drivers have more variance and struggle more
            position_improvement = np.random.uniform(-1, 4) + additional_variance - strategy_impact
            time_penalty = time_multiplier * (1 + variance * 0.3)
        
        adjusted_position = max(1, min(20, base_prediction['position'] + position_improvement))
        adjusted_time = base_prediction['time'] * time_penalty
        
        return {
            'position': adjusted_position,
            'time': adjusted_time,
            'weather_impact': position_improvement
        }
    
    def _get_driver_form(self, driver: str, race: str) -> Dict:
        """Analyze driver's recent form"""
        if self.historical_data.empty:
            return {'recent_avg_position': 10, 'races_completed': 0, 'podiums': 0}
        
        # Get driver's recent races (last 5)
        driver_recent = self.historical_data[
            (self.historical_data['driver'] == driver) & 
            (self.historical_data['season'] >= 2024)
        ].tail(5)
        
        if driver_recent.empty:
            return {'recent_avg_position': 10, 'races_completed': 0, 'podiums': 0}
        
        avg_position = driver_recent['race_position'].mean()
        races_completed = len(driver_recent[driver_recent['status'] == 'Finished'])
        podiums = len(driver_recent[driver_recent['race_position'] <= 3])
        
        return {
            'recent_avg_position': avg_position,
            'races_completed': races_completed,
            'podiums': podiums
        }
    
    def _get_driver_skill_rating(self, driver: str) -> float:
        """Get data-driven driver skill rating (0-1 scale)"""
        driver_full_name = self.drivers_2025.get(driver, {}).get('name', driver)
        driver_stats = self.driver_performance.get(driver_full_name, {})
        return driver_stats.get('overall_skill', 0.70)  # Default to 0.70 for unknown drivers
    
    def _get_strategy_skill(self, driver: str) -> float:
        """Get data-driven driver/team strategy skill rating (0-1 scale)"""
        driver_full_name = self.drivers_2025.get(driver, {}).get('name', driver)
        driver_stats = self.driver_performance.get(driver_full_name, {})
        return driver_stats.get('strategy_execution', 0.65)  # Default for unknown drivers
    
    def _calculate_confidence_score(self, driver: str, race: str, weather: str, driver_form: Dict) -> float:
        """Calculate prediction confidence score (0-100%)"""
        base_confidence = 75.0  # Base confidence
        
        # Adjust based on driver skill and consistency
        skill_rating = self._get_driver_skill_rating(driver)
        base_confidence += (skill_rating - 0.7) * 30  # Skilled drivers = higher confidence
        
        # Adjust based on weather (more uncertainty in wet/mixed conditions)
        if weather != "Dry":
            weather_data = self.weather_effects.get(weather, self.weather_effects["Dry"])
            weather_uncertainty = weather_data['driver_variance'] * 20
            
            # Additional uncertainty for mixed/changing conditions
            if weather_data.get('strategy_impact', False):
                weather_uncertainty += 5  # Strategy decisions add uncertainty
            if weather_data.get('chaos_factor', 0) > 0:
                weather_uncertainty += weather_data['chaos_factor'] * 15  # Variable conditions
                
            base_confidence -= weather_uncertainty
        
        # Adjust based on recent form
        if driver_form['races_completed'] > 0:
            form_factor = min(driver_form['races_completed'] / 5.0, 1.0)  # More races = higher confidence
            base_confidence += form_factor * 10
        
        # Add some random variance
        base_confidence += np.random.normal(0, 5)
        
        return max(60.0, min(98.0, base_confidence))  # Clamp between 60-98%
    
    def _calculate_race_statistics(self, predictions: List[Dict], weather: str, race_name: str) -> Dict:
        """Calculate race prediction statistics"""
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        # Count predicted podium finishers by team
        podium_teams = [p['team'] for p in predictions[:3]]
        team_counts = {}
        for team in podium_teams:
            team_counts[team] = team_counts.get(team, 0) + 1
        
        return {
            'average_confidence': round(avg_confidence, 1),
            'weather_impact': weather != "Dry",
            'predicted_podium_teams': team_counts,
            'total_predictions': len(predictions),
            'high_confidence_predictions': len([p for p in predictions if p['confidence'] > 85]),
            'competitive_field': len([p for p in predictions if p['confidence'] < 80])  # More uncertainty = competitive
        }

# Create singleton instance
race_prediction_service = RacePredictionService()