import fastf1
import pandas as pd
from typing import Dict, List, Optional
import os
from datetime import datetime

class DataService:
    def __init__(self):
        fastf1.Cache.enable_cache(os.path.join(os.path.dirname(__file__), '..', 'cache'))
    
    def get_driver_historical_data(self, driver: str, seasons: List[int] = None) -> pd.DataFrame:
        """Get driver historical data from cached CSV file only - no API calls"""
        if seasons is None:
            seasons = [2024, 2025]
        
        # Only use cached CSV data
        csv_file = os.path.join(os.path.dirname(__file__), '..', 'f1_data.csv')
        
        if not os.path.exists(csv_file):
            print(f"No cached data found at {csv_file}")
            return pd.DataFrame()
        
        try:
            all_data = pd.read_csv(csv_file)
            print(f"Loaded cached data: {len(all_data)} records from {sorted(all_data['season'].unique())}")
            
            # Filter for the specific driver and seasons
            driver_data = all_data[
                (all_data['driver'] == driver) & 
                (all_data['season'].isin(seasons))
            ]
            
            print(f"Found {len(driver_data)} records for driver {driver} in seasons {seasons}")
            return driver_data
            
        except Exception as e:
            print(f"Error loading cached data: {e}")
            return pd.DataFrame()
    
    def get_track_characteristics(self, track_name: str) -> Dict:
        track_map = {
            'Silverstone': {'type': 'high_speed', 'difficulty': 8, 'weather_factor': 0.8},
            'Monaco': {'type': 'street', 'difficulty': 10, 'weather_factor': 0.9},
            'Spa': {'type': 'high_speed', 'difficulty': 9, 'weather_factor': 0.7},
            'Monza': {'type': 'power', 'difficulty': 6, 'weather_factor': 0.6},
            'Singapore': {'type': 'street', 'difficulty': 9, 'weather_factor': 0.3},
            'Suzuka': {'type': 'technical', 'difficulty': 9, 'weather_factor': 0.8},
            'Interlagos': {'type': 'technical', 'difficulty': 8, 'weather_factor': 0.7},
            'Austin': {'type': 'mixed', 'difficulty': 7, 'weather_factor': 0.6},
            'Bahrain': {'type': 'mixed', 'difficulty': 6, 'weather_factor': 0.2},
            'Jeddah': {'type': 'street', 'difficulty': 8, 'weather_factor': 0.1},
        }
        
        return track_map.get(track_name, {'type': 'mixed', 'difficulty': 7, 'weather_factor': 0.5})
    
    def get_team_performance_data(self, team: str, seasons: List[int] = None) -> Dict:
        """Get team performance data from cached CSV file only - no API calls"""
        if seasons is None:
            seasons = [2024, 2025]
        
        team_stats = {
            'avg_qualifying_position': 10.0,
            'avg_race_position': 10.0,
            'reliability_score': 0.8,
            'development_trend': 0.0
        }
        
        # Only use cached CSV data
        csv_file = os.path.join(os.path.dirname(__file__), '..', 'f1_data.csv')
        
        if not os.path.exists(csv_file):
            print(f"No cached data found for team performance")
            return team_stats
        
        try:
            all_data = pd.read_csv(csv_file)
            
            # Filter for the specific team and seasons
            team_data = all_data[
                (all_data['team'] == team) & 
                (all_data['season'].isin(seasons))
            ]
            
            if not team_data.empty:
                team_stats['avg_qualifying_position'] = team_data['qualifying_position'].mean()
                team_stats['avg_race_position'] = team_data['race_position'].mean()
                print(f"Team {team} stats: Q{team_stats['avg_qualifying_position']:.1f} R{team_stats['avg_race_position']:.1f}")
            else:
                print(f"No cached data found for team {team}")
        
        except Exception as e:
            print(f"Error loading team performance data: {e}")
        
        return team_stats