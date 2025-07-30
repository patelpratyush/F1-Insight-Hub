#!/usr/bin/env python3
"""
Enhanced F1 Machine Learning Model with Ensemble Methods and Advanced Features
Implements Random Forest + XGBoost + Neural Network ensemble for improved predictions.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
import os
import pickle
from typing import Dict, Tuple, List, Optional
import warnings
import optuna
from scipy import stats
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_model_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedF1MLModel:
    def __init__(self, use_fastf1_cache: bool = True):
        """Initialize the enhanced F1 ML model with ensemble methods"""
        self.use_fastf1_cache = use_fastf1_cache
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        self.models_dir = os.path.join(os.path.dirname(__file__), 'enhanced_models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Ensemble models storage
        self.qualifying_models = {}
        self.race_models = {}
        self.label_encoders = {}
        self.scaler = None
        self.robust_scaler = None
        self.feature_columns = []
        
        # Track characteristics with enhanced details
        self.track_characteristics = {
            'Monaco Grand Prix': {'type': 'street', 'difficulty': 10, 'speed': 'low', 'overtaking': 'very_hard', 'elevation_change': 'high', 'tire_deg': 'low'},
            'Silverstone Grand Prix': {'type': 'high_speed', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Monza Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'very_high', 'overtaking': 'easy', 'elevation_change': 'low', 'tire_deg': 'medium'},
            'Spa-Francorchamps Grand Prix': {'type': 'high_speed', 'difficulty': 9, 'speed': 'high', 'overtaking': 'medium', 'elevation_change': 'very_high', 'tire_deg': 'high'},
            'Singapore Grand Prix': {'type': 'street', 'difficulty': 9, 'speed': 'low', 'overtaking': 'hard', 'elevation_change': 'low', 'tire_deg': 'low'},
            'Suzuka Grand Prix': {'type': 'technical', 'difficulty': 9, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'medium', 'tire_deg': 'medium'},
            'Interlagos Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'Austin Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'Bahrain Grand Prix': {'type': 'mixed', 'difficulty': 6, 'speed': 'medium', 'overtaking': 'easy', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Saudi Arabian Grand Prix': {'type': 'street', 'difficulty': 8, 'speed': 'high', 'overtaking': 'hard', 'elevation_change': 'low', 'tire_deg': 'medium'},
            'Australian Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'medium'},
            'Japanese Grand Prix': {'type': 'technical', 'difficulty': 9, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'medium', 'tire_deg': 'medium'},
            'Chinese Grand Prix': {'type': 'mixed', 'difficulty': 6, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'medium'},
            'Miami Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Emilia Romagna Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'hard', 'elevation_change': 'medium', 'tire_deg': 'low'},
            'Canadian Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'high', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Spanish Grand Prix': {'type': 'technical', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'hard', 'elevation_change': 'medium', 'tire_deg': 'high'},
            'Austrian Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'high', 'overtaking': 'easy', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'British Grand Prix': {'type': 'high_speed', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Belgian Grand Prix': {'type': 'high_speed', 'difficulty': 9, 'speed': 'very_high', 'overtaking': 'easy', 'elevation_change': 'very_high', 'tire_deg': 'high'},
            'Hungarian Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'low', 'overtaking': 'very_hard', 'elevation_change': 'medium', 'tire_deg': 'low'},
            'Dutch Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'hard', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'Italian Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'very_high', 'overtaking': 'easy', 'elevation_change': 'low', 'tire_deg': 'medium'},
            'Azerbaijan Grand Prix': {'type': 'street', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'United States Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'Mexico City Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'São Paulo Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'high', 'tire_deg': 'medium'},
            'Las Vegas Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'very_high', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Qatar Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'high'},
            'Abu Dhabi Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'medium'}
        }
        
        # Weather impact factors by driver (simplified example)
        self.driver_weather_factors = {
            'Lewis Hamilton': {'wet_skill': 1.2, 'hot_weather': 1.0, 'cold_weather': 0.95},
            'Max Verstappen': {'wet_skill': 1.15, 'hot_weather': 1.05, 'cold_weather': 1.0},
            'Lando Norris': {'wet_skill': 0.9, 'hot_weather': 1.0, 'cold_weather': 1.05},
            'Charles Leclerc': {'wet_skill': 1.1, 'hot_weather': 1.0, 'cold_weather': 1.0},
            # Add more drivers as needed - using defaults for others
        }
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """Load and prepare the F1 data with enhanced feature engineering"""
        logger.info("Loading F1 data...")
        
        if self.use_fastf1_cache:
            df = self._load_from_fastf1_cache()
        else:
            # Fallback to CSV (if it exists)
            csv_file = os.path.join(os.path.dirname(__file__), 'f1_data.csv')
            if not os.path.exists(csv_file):
                raise FileNotFoundError(f"Data file not found: {csv_file}")
            df = pd.read_csv(csv_file)
        
        logger.info(f"Loaded {len(df)} records from {len(df['season'].unique())} seasons")
        
        # Data cleaning
        df = df.dropna(subset=['qualifying_position', 'race_position'])
        df['avg_lap_time'] = df['avg_lap_time'].fillna(df['avg_lap_time'].mean())
        df['gap_to_winner'] = df['gap_to_winner'].fillna(0)
        
        # Add missing columns expected by enhanced features
        df['grid_position'] = df['qualifying_position']  # Grid position same as qualifying position (simplified)
        
        # Enhanced feature engineering
        df = self._engineer_enhanced_features(df)
        
        logger.info(f"Data prepared with {len(df)} records and {len(df.columns)} features")
        return df
    
    def _load_from_fastf1_cache(self) -> pd.DataFrame:
        """Load data from FastF1 cache and convert to training format"""
        import pickle
        
        all_data = []
        seasons = ['2024', '2025']
        
        for season in seasons:
            season_dir = os.path.join(self.cache_dir, season)
            if not os.path.exists(season_dir):
                logger.warning(f"Season {season} directory not found")
                continue
            
            races_processed = 0
            
            # Process each race in the season
            for race_folder in sorted(os.listdir(season_dir)):
                race_path = os.path.join(season_dir, race_folder)
                if not os.path.isdir(race_path):
                    continue
                
                # Extract race info
                race_name = race_folder.replace(f'{season}-', '').replace('_', ' ')
                
                # Process race sessions to get qualifying and race data
                race_data = self._process_race_sessions_for_ml(race_path, season, race_name)
                if race_data:
                    all_data.extend(race_data)
                    races_processed += 1
            
            logger.info(f"   Processed {races_processed} races from {season}")
        
        if not all_data:
            raise ValueError("No data loaded from FastF1 cache")
            
        return pd.DataFrame(all_data)
    
    def _process_race_sessions_for_ml(self, race_path: str, season: str, race_name: str) -> List[Dict]:
        """Process race sessions to extract ML training data"""
        import pickle
        
        # 2025 season driver mapping
        drivers_2025 = {
            '1': {'code': 'VER', 'name': 'Max Verstappen', 'team': 'Red Bull Racing Honda RBPT'},
            '22': {'code': 'TSU', 'name': 'Yuki Tsunoda', 'team': 'Red Bull Racing Honda RBPT'},
            '44': {'code': 'HAM', 'name': 'Lewis Hamilton', 'team': 'Scuderia Ferrari'},
            '16': {'code': 'LEC', 'name': 'Charles Leclerc', 'team': 'Scuderia Ferrari'},
            '63': {'code': 'RUS', 'name': 'George Russell', 'team': 'Mercedes'},
            '12': {'code': 'ANT', 'name': 'Kimi Antonelli', 'team': 'Mercedes'},
            '4': {'code': 'NOR', 'name': 'Lando Norris', 'team': 'McLaren Mercedes'},
            '81': {'code': 'PIA', 'name': 'Oscar Piastri', 'team': 'McLaren Mercedes'},
            '14': {'code': 'ALO', 'name': 'Fernando Alonso', 'team': 'Aston Martin Aramco Mercedes'},
            '18': {'code': 'STR', 'name': 'Lance Stroll', 'team': 'Aston Martin Aramco Mercedes'},
            '10': {'code': 'GAS', 'name': 'Pierre Gasly', 'team': 'BWT Alpine F1 Team'},
            '43': {'code': 'COL', 'name': 'Franco Colapinto', 'team': 'BWT Alpine F1 Team'},
            '30': {'code': 'LAW', 'name': 'Liam Lawson', 'team': 'Racing Bulls F1 Team'},
            '6': {'code': 'HAD', 'name': 'Isack Hadjar', 'team': 'Racing Bulls F1 Team'},
            '55': {'code': 'SAI', 'name': 'Carlos Sainz', 'team': 'Williams Mercedes'},
            '23': {'code': 'ALB', 'name': 'Alexander Albon', 'team': 'Williams Mercedes'},
            '31': {'code': 'OCO', 'name': 'Esteban Ocon', 'team': 'MoneyGram Haas F1 Team'},
            '38': {'code': 'BEA', 'name': 'Oliver Bearman', 'team': 'MoneyGram Haas F1 Team'},
            '27': {'code': 'HUL', 'name': 'Nico Hülkenberg', 'team': 'Kick Sauber F1 Team'},
            '5': {'code': 'BOR', 'name': 'Gabriel Bortoleto', 'team': 'Kick Sauber F1 Team'}
        }
        
        race_data = []
        qualifying_data = {}
        race_results = {}
        
        try:
            # Process each session in the race
            for session_folder in os.listdir(race_path):
                session_path = os.path.join(race_path, session_folder)
                if not os.path.isdir(session_path):
                    continue
                
                # Load timing data for this session
                timing_file = os.path.join(session_path, 'timing_app_data.ff1pkl')
                if not os.path.exists(timing_file):
                    continue
                
                # Load weather data if available
                weather_file = os.path.join(session_path, 'weather_data.ff1pkl')
                weather_data = self._load_weather_data(weather_file)
                
                try:
                    with open(timing_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    if 'data' not in cache_data:
                        continue
                    
                    timing_data = cache_data['data']
                    if not hasattr(timing_data, 'iterrows'):
                        continue
                    
                    # Determine session type and process
                    if 'Qualifying' in session_folder:
                        qualifying_data = self._extract_qualifying_results(timing_data, drivers_2025)
                    elif 'Race' in session_folder:
                        race_results = self._extract_race_results(timing_data, drivers_2025)
                        
                except Exception as e:
                    logger.warning(f"Error processing session {session_folder}: {e}")
                    continue
            
            # Combine qualifying and race data
            if qualifying_data and race_results:
                for driver_num, quali_data in qualifying_data.items():
                    if driver_num in race_results:
                        race_result = race_results[driver_num]
                        
                        # Create training record
                        record = {
                            'season': int(season),
                            'race': race_name,
                            'driver': quali_data['code'],
                            'team': quali_data['team'],
                            'qualifying_position': quali_data['position'],
                            'race_position': race_result['position'],
                            'avg_lap_time': race_result['avg_lap_time'],
                            'best_lap_time': min(quali_data['best_lap'], race_result['best_lap']),
                            'points': max(0, 25 - race_result['position'] + 1) if race_result['position'] <= 10 else 0,  # Simplified points
                            'gap_to_winner': race_result['gap_to_winner'],
                            'weather': weather_data['weather'],
                            'temperature': weather_data['temperature'],
                            'status': 'Finished'  # Default status - can be enhanced later
                        }
                        race_data.append(record)
                        
        except Exception as e:
            logger.warning(f"Error processing race {race_name}: {e}")
        
        return race_data
    
    def _extract_qualifying_results(self, timing_data, drivers_2025) -> Dict:
        """Extract qualifying positions from timing data"""
        driver_best_times = {}
        
        for _, row in timing_data.iterrows():
            driver_num = str(row.get('Driver', ''))
            if not driver_num or driver_num == 'nan':
                continue
            
            lap_time = row.get('LapTime')
            if pd.notna(lap_time):
                if driver_num not in driver_best_times:
                    driver_best_times[driver_num] = {'best_lap': lap_time, 'laps': []}
                
                driver_best_times[driver_num]['laps'].append(lap_time)
                if lap_time < driver_best_times[driver_num]['best_lap']:
                    driver_best_times[driver_num]['best_lap'] = lap_time
        
        # Sort by best lap time and assign positions
        sorted_drivers = sorted(driver_best_times.items(), 
                              key=lambda x: x[1]['best_lap'])
        
        qualifying_results = {}
        for position, (driver_num, data) in enumerate(sorted_drivers, 1):
            driver_info = drivers_2025.get(driver_num, {
                'code': f'D{driver_num}', 'name': f'Driver {driver_num}', 'team': 'Unknown Team'
            })
            
            qualifying_results[driver_num] = {
                'position': position,
                'best_lap': data['best_lap'].total_seconds(),
                'code': driver_info['code'],
                'team': driver_info['team']
            }
        
        return qualifying_results
    
    def _extract_race_results(self, timing_data, drivers_2025) -> Dict:
        """Extract race positions from timing data"""
        driver_lap_times = {}
        
        for _, row in timing_data.iterrows():
            driver_num = str(row.get('Driver', ''))
            if not driver_num or driver_num == 'nan':
                continue
            
            lap_time = row.get('LapTime')
            if pd.notna(lap_time):
                if driver_num not in driver_lap_times:
                    driver_lap_times[driver_num] = []
                driver_lap_times[driver_num].append(lap_time)
        
        # Calculate average lap times and sort
        driver_avg_times = {}
        for driver_num, lap_times in driver_lap_times.items():
            if lap_times:
                avg_time = sum(lap_times, pd.Timedelta(0)) / len(lap_times)
                best_time = min(lap_times)
                driver_avg_times[driver_num] = {
                    'avg_lap_time': avg_time.total_seconds(),
                    'best_lap': best_time.total_seconds(),
                    'total_laps': len(lap_times)
                }
        
        # Sort by average lap time and assign positions
        sorted_drivers = sorted(driver_avg_times.items(), 
                              key=lambda x: x[1]['avg_lap_time'])
        
        race_results = {}
        winner_time = sorted_drivers[0][1]['avg_lap_time'] if sorted_drivers else 0
        
        for position, (driver_num, data) in enumerate(sorted_drivers, 1):
            race_results[driver_num] = {
                'position': position,
                'avg_lap_time': data['avg_lap_time'],
                'best_lap': data['best_lap'],
                'gap_to_winner': data['avg_lap_time'] - winner_time
            }
        
        return race_results
    
    def _load_weather_data(self, weather_file: str) -> Dict:
        """Load weather data from FastF1 cache file"""
        if not os.path.exists(weather_file):
            return {'weather': 'Dry', 'temperature': 25.0, 'humidity': 50.0, 'rainfall': False}
        
        try:
            with open(weather_file, 'rb') as f:
                weather_cache = pickle.load(f)
            
            if 'data' not in weather_cache:
                return {'weather': 'Dry', 'temperature': 25.0, 'humidity': 50.0, 'rainfall': False}
            
            weather_data = weather_cache['data']
            
            # Extract weather metrics (average over session)
            if hasattr(weather_data, 'mean'):
                avg_temp = weather_data.get('AirTemp', pd.Series([25.0])).mean()
                avg_humidity = weather_data.get('Humidity', pd.Series([50.0])).mean()
                has_rain = weather_data.get('Rainfall', pd.Series([False])).any()
                
                weather_condition = 'Wet' if has_rain else 'Dry'
                
                return {
                    'weather': weather_condition,
                    'temperature': float(avg_temp) if pd.notna(avg_temp) else 25.0,
                    'humidity': float(avg_humidity) if pd.notna(avg_humidity) else 50.0,
                    'rainfall': bool(has_rain)
                }
            
        except Exception as e:
            logger.warning(f"Error loading weather data: {e}")
        
        return {'weather': 'Dry', 'temperature': 25.0, 'humidity': 50.0, 'rainfall': False}
    
    def _engineer_enhanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive features including rivalries and team dynamics"""
        logger.info("Engineering enhanced features...")
        
        # Sort by season and race for time-series features
        df = df.sort_values(['season', 'race', 'qualifying_position'])
        
        # Enhanced track characteristics - convert to numeric values
        track_char_mapping = {
            'low': 1, 'medium': 2, 'high': 3,
            'street': 1, 'permanent': 2, 'hybrid': 3,
            'easy': 1, 'hard': 3
        }
        
        for char in ['type', 'difficulty', 'speed', 'overtaking', 'elevation_change', 'tire_deg']:
            track_values = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get(char, 'medium'))
            df[f'track_{char}'] = track_values.map(lambda x: track_char_mapping.get(x, 2))
        
        # Historical performance features (existing)
        df['driver_historical_quali_avg'] = df.groupby('driver')['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_historical_race_avg'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_historical_points_avg'] = df.groupby('driver')['points'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        # Team performance features (existing)
        df['team_historical_quali_avg'] = df.groupby('team')['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['team_historical_race_avg'] = df.groupby('team')['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['team_historical_points_avg'] = df.groupby('team')['points'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        # NEW: Enhanced momentum features with robust calculation
        def safe_momentum(y):
            """Calculate momentum using simple slope without polyfit"""
            try:
                if len(y) < 2:
                    return 0.0
                # Use simple linear trend instead of polyfit
                x_vals = np.arange(len(y))
                if len(set(y)) == 1:  # All values are the same
                    return 0.0
                # Simple slope calculation: (y_end - y_start) / (x_end - x_start)
                return -(y.iloc[-1] - y.iloc[0]) / (len(y) - 1)
            except (Exception):
                return 0.0
        
        # Use expanding window for more stable calculation
        df['driver_momentum_3'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.rolling(window=3, min_periods=2).apply(safe_momentum, raw=False).shift(1)
        )
        df['driver_momentum_5'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.rolling(window=5, min_periods=3).apply(safe_momentum, raw=False).shift(1)
        )
        
        # NEW: Championship position pressure
        df['championship_position'] = df.groupby(['season', 'race'])['points'].transform(
            lambda x: x.expanding().sum().rank(ascending=False, method='dense')
        ).shift(1)
        df['championship_pressure'] = np.where(df['championship_position'] <= 3, 1.2, 
                                     np.where(df['championship_position'] <= 8, 1.0, 0.8))
        
        # NEW: Team dynamics - teammate comparison
        df['teammate_performance_diff'] = df.groupby(['team', 'season', 'race'])['race_position'].transform(
            lambda x: x - x.mean() if len(x) > 1 else 0
        )
        
        # NEW: Track-specific performance (simplified to avoid complex transforms)
        track_avg = df.groupby('race')['race_position'].transform('mean')
        driver_track_avg = df.groupby(['driver', 'race'])['race_position'].transform(
            lambda x: x.expanding().mean().shift(1).fillna(x.mean())
        )
        df['driver_track_advantage'] = track_avg - driver_track_avg
        
        # NEW: Weather impact features
        df['weather_impact'] = df.apply(self._calculate_weather_impact, axis=1)
        
        # NEW: Form streaks (using transform for better performance)
        df['podium_streak'] = df.groupby('driver')['race_position'].transform(
            lambda x: (x <= 3).rolling(window=5, min_periods=1).sum().shift(1).fillna(0)
        )
        
        df['dnf_streak'] = df.groupby('driver')['status'].transform(
            lambda x: (x != 'Finished').rolling(window=5, min_periods=1).sum().shift(1).fillna(0)
        )
        
        # Recent form (last 3 races)
        df['driver_recent_quali_avg'] = df.groupby('driver')['qualifying_position'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean().shift(1)
        )
        df['driver_recent_race_avg'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean().shift(1)
        )
        
        # Track-specific performance
        df['driver_track_quali_avg'] = df.groupby(['driver', 'race'])['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_track_race_avg'] = df.groupby(['driver', 'race'])['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        # Season performance
        df['season_race_number'] = df.groupby('season').cumcount() + 1
        df['driver_season_quali_avg'] = df.groupby(['driver', 'season'])['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_season_race_avg'] = df.groupby(['driver', 'season'])['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        # Grid position advantage/disadvantage
        df['grid_vs_quali_diff'] = df['grid_position'] - df['qualifying_position']
        
        # Performance trends
        df['quali_trend'] = df.groupby('driver')['qualifying_position'].transform(
            lambda x: x.diff().rolling(window=3, min_periods=1).mean()
        )
        df['race_trend'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.diff().rolling(window=3, min_periods=1).mean()
        )
        
        # Weather impact
        df['weather_dry'] = (df['weather'] == 'Dry').astype(int)
        df['weather_wet'] = (df['weather'] == 'Wet').astype(int)
        
        # Status encoding
        df['dnf'] = (df['status'] != 'Finished').astype(int)
        
        # Fill NaN values with appropriate defaults
        feature_columns = [col for col in df.columns if any(keyword in col for keyword in 
                          ['historical', 'recent', 'track', 'season', 'trend', 'momentum', 'championship', 'teammate', 'advantage', 'impact', 'streak'])]
        
        for col in feature_columns:
            if col in df.columns:
                if 'quali' in col:
                    df[col] = df[col].fillna(10.0)
                elif 'race' in col:
                    df[col] = df[col].fillna(10.0)
                elif 'points' in col:
                    df[col] = df[col].fillna(0.0)
                elif 'momentum' in col or 'trend' in col:
                    df[col] = df[col].fillna(0.0)
                elif 'championship' in col:
                    df[col] = df[col].fillna(10.0)
                else:
                    df[col] = df[col].fillna(0.0)
        
        logger.info(f"Created {len([col for col in df.columns if col not in ['season', 'race', 'driver', 'team', 'qualifying_position', 'race_position', 'points', 'status']])} engineered features")
        return df
    
    def _calculate_weather_impact(self, row) -> float:
        """Calculate weather impact for a driver"""
        driver = row['driver']
        weather = row['weather']
        
        if driver in self.driver_weather_factors:
            factors = self.driver_weather_factors[driver]
            if weather == 'Wet':
                return factors['wet_skill']
            elif weather == 'Dry':
                return 1.0  # Baseline
        
        return 1.0  # Default neutral impact
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare features for training with enhanced encoding"""
        logger.info("Preparing features for model training...")
        
        # Encode categorical variables
        categorical_columns = ['driver', 'team', 'race'] + [f'track_{char}' for char in ['type', 'speed', 'overtaking', 'elevation_change', 'tire_deg']]
        
        for col in categorical_columns:
            if col in df.columns:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        # Select enhanced feature columns
        feature_columns = [
            'season', 'season_race_number', 'grid_position', 'avg_lap_time', 'gap_to_winner',
            'track_difficulty', 'grid_vs_quali_diff', 'weather_dry', 'weather_wet', 'dnf',
            'driver_historical_quali_avg', 'driver_historical_race_avg', 'driver_historical_points_avg',
            'team_historical_quali_avg', 'team_historical_race_avg', 'team_historical_points_avg',
            'driver_recent_quali_avg', 'driver_recent_race_avg',
            'driver_track_quali_avg', 'driver_track_race_avg',
            'driver_season_quali_avg', 'driver_season_race_avg',
            'quali_trend', 'race_trend',
            # New enhanced features
            'driver_momentum_3', 'driver_momentum_5', 'championship_position', 'championship_pressure',
            'teammate_performance_diff', 'driver_track_advantage', 'weather_impact',
            'podium_streak', 'dnf_streak'
        ]
        
        # Add encoded categorical features
        for col in categorical_columns:
            if col in df.columns:
                feature_columns.append(col + '_encoded')
        
        # Filter to existing columns
        feature_columns = [col for col in feature_columns if col in df.columns]
        self.feature_columns = feature_columns
        
        # Separate features and targets
        X = df[feature_columns].copy()
        y_qualifying = df['qualifying_position'].copy()
        y_race = df['race_position'].copy()
        
        # Enhanced scaling with RobustScaler for outliers
        self.scaler = StandardScaler()
        self.robust_scaler = RobustScaler()
        
        # Handle any remaining NaN or infinite values
        X_clean = X.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_clean),
            columns=X_clean.columns,
            index=X_clean.index
        )
        
        logger.info(f"Prepared {len(feature_columns)} enhanced features for training")
        return X_scaled, pd.DataFrame({'qualifying': y_qualifying, 'race': y_race})
    
    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series, model_type: str) -> Dict:
        """Optimize hyperparameters using Optuna"""
        logger.info(f"Optimizing hyperparameters for {model_type}...")
        
        def objective(trial):
            if model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'random_state': 42
                }
                model = xgb.XGBRegressor(**params)
            elif model_type == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'max_depth': trial.suggest_int('max_depth', 5, 20),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                    'random_state': 42
                }
                model = RandomForestRegressor(**params)
            
            scores = cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_absolute_error')
            return -scores.mean()
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=10, show_progress_bar=False)  # Further reduced for stability
        
        logger.info(f"Best {model_type} parameters: {study.best_params}")
        return study.best_params
    
    def train_ensemble_models(self, X: pd.DataFrame, y: pd.DataFrame) -> Dict:
        """Train ensemble models with optimized hyperparameters"""
        logger.info("Training ensemble models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        
        results = {}
        
        # Train models for both qualifying and race
        for target in ['qualifying', 'race']:
            logger.info(f"Training {target} ensemble...")
            
            models = {}
            
            # 1. XGBoost with optimized parameters
            xgb_params = self.optimize_hyperparameters(X_train, y_train[target], 'xgboost')
            models['xgboost'] = xgb.XGBRegressor(**xgb_params, objective='reg:squarederror', eval_metric='rmse')
            models['xgboost'].fit(X_train, y_train[target])
            
            # 2. Random Forest with optimized parameters
            rf_params = self.optimize_hyperparameters(X_train, y_train[target], 'random_forest')
            models['random_forest'] = RandomForestRegressor(**rf_params)
            models['random_forest'].fit(X_train, y_train[target])
            
            # 3. Neural Network with more robust settings
            models['neural_network'] = MLPRegressor(
                hidden_layer_sizes=(50, 25),  # Reduced complexity
                max_iter=500,  # Reduced iterations
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2,
                alpha=0.01,  # L2 regularization
                learning_rate_init=0.001,  # Lower learning rate
                solver='adam'  # Explicit solver
            )
            # Store scaling parameters for neural network
            nn_mean = y_train[target].mean()
            nn_std = y_train[target].std()
            models[f'neural_network_mean_{target}'] = nn_mean
            models[f'neural_network_std_{target}'] = nn_std
            
            # Scale target for neural network stability
            y_scaled = (y_train[target] - nn_mean) / nn_std
            models['neural_network'].fit(X_train, y_scaled)
            
            # Store models
            if target == 'qualifying':
                self.qualifying_models = models
            else:
                self.race_models = models
            
            # Evaluate ensemble
            predictions = {}
            for name, model in models.items():
                if name.startswith('neural_network') and not name == 'neural_network':
                    continue  # Skip scaling parameters
                
                if name == 'neural_network':
                    # Unscale neural network predictions for evaluation
                    nn_pred = model.predict(X_test)
                    nn_mean = models[f'neural_network_mean_{target}']
                    nn_std = models[f'neural_network_std_{target}']
                    pred = (nn_pred * nn_std) + nn_mean
                else:
                    pred = model.predict(X_test)
                
                predictions[name] = pred
                
                mae = mean_absolute_error(y_test[target], pred)
                rmse = np.sqrt(mean_squared_error(y_test[target], pred))
                r2 = r2_score(y_test[target], pred)
                
                logger.info(f"{target} {name} - MAE: {mae:.3f}, RMSE: {rmse:.3f}, R²: {r2:.3f}")
            
            # Ensemble prediction (weighted average)
            weights = {'xgboost': 0.5, 'random_forest': 0.3, 'neural_network': 0.2}
            ensemble_pred = sum(weights[name] * predictions[name] for name in weights.keys())
            
            # Evaluate ensemble
            ensemble_mae = mean_absolute_error(y_test[target], ensemble_pred)
            ensemble_rmse = np.sqrt(mean_squared_error(y_test[target], ensemble_pred))
            ensemble_r2 = r2_score(y_test[target], ensemble_pred)
            
            results[target] = {
                'ensemble_mae': ensemble_mae,
                'ensemble_rmse': ensemble_rmse,
                'ensemble_r2': ensemble_r2,
                'individual_models': {
                    name: {
                        'mae': mean_absolute_error(y_test[target], predictions[name]),
                        'rmse': np.sqrt(mean_squared_error(y_test[target], predictions[name])),
                        'r2': r2_score(y_test[target], predictions[name])
                    } for name in predictions.keys()
                }
            }
            
            logger.info(f"{target} Ensemble - MAE: {ensemble_mae:.3f}, RMSE: {ensemble_rmse:.3f}, R²: {ensemble_r2:.3f}")
        
        logger.info("Ensemble model training completed")
        return results
    
    def predict_with_ensemble(self, X: pd.DataFrame) -> Dict:
        """Make predictions using ensemble models"""
        if not self.qualifying_models or not self.race_models:
            raise ValueError("Ensemble models not trained yet")
        
        # Scale features
        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Weights for ensemble
        weights = {'xgboost': 0.5, 'random_forest': 0.3, 'neural_network': 0.2}
        
        # Qualifying predictions
        quali_predictions = {}
        for name, model in self.qualifying_models.items():
            if name.startswith('neural_network') and not name.endswith('_qualifying'):
                continue  # Skip scaling parameters
            if name == 'neural_network':
                # Unscale neural network predictions
                nn_pred = model.predict(X_scaled)
                nn_mean = self.qualifying_models['neural_network_mean_qualifying']
                nn_std = self.qualifying_models['neural_network_std_qualifying']
                quali_predictions[name] = (nn_pred * nn_std) + nn_mean
            else:
                quali_predictions[name] = model.predict(X_scaled)
        
        qualifying_pred = sum(weights[name] * quali_predictions[name] for name in weights.keys())
        
        # Race predictions
        race_predictions = {}
        for name, model in self.race_models.items():
            if name.startswith('neural_network') and not name.endswith('_race'):
                continue  # Skip scaling parameters
            if name == 'neural_network':
                # Unscale neural network predictions
                nn_pred = model.predict(X_scaled)
                nn_mean = self.race_models['neural_network_mean_race']
                nn_std = self.race_models['neural_network_std_race']
                race_predictions[name] = (nn_pred * nn_std) + nn_mean
            else:
                race_predictions[name] = model.predict(X_scaled)
        
        race_pred = sum(weights[name] * race_predictions[name] for name in weights.keys())
        
        # Calculate confidence based on prediction variance
        quali_variance = np.var(list(quali_predictions.values()), axis=0)
        race_variance = np.var(list(race_predictions.values()), axis=0)
        
        # Convert variance to confidence (lower variance = higher confidence)
        qualifying_confidence = 1 / (1 + quali_variance)
        race_confidence = 1 / (1 + race_variance)
        
        return {
            'qualifying_position': qualifying_pred.round().astype(int),
            'race_position': race_pred.round().astype(int),
            'qualifying_confidence': qualifying_confidence,
            'race_confidence': race_confidence,
            'individual_predictions': {
                'qualifying': quali_predictions,
                'race': race_predictions
            }
        }
    
    def save_ensemble_models(self):
        """Save trained ensemble models and preprocessors"""
        logger.info("Saving enhanced ensemble models...")
        
        # Save models
        joblib.dump(self.qualifying_models, os.path.join(self.models_dir, 'qualifying_ensemble.pkl'))
        joblib.dump(self.race_models, os.path.join(self.models_dir, 'race_ensemble.pkl'))
        
        # Save preprocessors
        joblib.dump(self.label_encoders, os.path.join(self.models_dir, 'label_encoders.pkl'))
        joblib.dump(self.scaler, os.path.join(self.models_dir, 'scaler.pkl'))
        joblib.dump(self.robust_scaler, os.path.join(self.models_dir, 'robust_scaler.pkl'))
        
        # Save feature columns
        joblib.dump(self.feature_columns, os.path.join(self.models_dir, 'feature_columns.pkl'))
        
        logger.info("Enhanced ensemble models saved successfully")
    
    def load_ensemble_models(self):
        """Load trained ensemble models and preprocessors"""
        logger.info("Loading enhanced ensemble models...")
        
        # Load models
        self.qualifying_models = joblib.load(os.path.join(self.models_dir, 'qualifying_ensemble.pkl'))
        self.race_models = joblib.load(os.path.join(self.models_dir, 'race_ensemble.pkl'))
        
        # Load preprocessors
        self.label_encoders = joblib.load(os.path.join(self.models_dir, 'label_encoders.pkl'))
        self.scaler = joblib.load(os.path.join(self.models_dir, 'scaler.pkl'))
        self.robust_scaler = joblib.load(os.path.join(self.models_dir, 'robust_scaler.pkl'))
        
        # Load feature columns
        self.feature_columns = joblib.load(os.path.join(self.models_dir, 'feature_columns.pkl'))
        
        logger.info("Enhanced ensemble models loaded successfully")
    
    def train_pipeline(self) -> Dict:
        """Complete enhanced training pipeline"""
        logger.info("Starting enhanced F1 ML ensemble training pipeline...")
        
        try:
            # Load and prepare data
            df = self.load_and_prepare_data()
            
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Train ensemble models
            results = self.train_ensemble_models(X, y)
            
            # Save models
            self.save_ensemble_models()
            
            # Log results and compare with baseline
            logger.info("Enhanced Training Results:")
            baseline_race_mae = 1.638  # Current baseline from your data
            baseline_qualifying_mae = 0.359  # Current baseline
            
            for target in ['qualifying', 'race']:
                ensemble_mae = results[target]['ensemble_mae']
                baseline_mae = baseline_qualifying_mae if target == 'qualifying' else baseline_race_mae
                improvement = ((baseline_mae - ensemble_mae) / baseline_mae) * 100
                
                logger.info(f"{target.title()} Ensemble - MAE: {ensemble_mae:.3f}, RMSE: {results[target]['ensemble_rmse']:.3f}, R²: {results[target]['ensemble_r2']:.3f}")
                logger.info(f"{target.title()} vs Baseline: {improvement:+.1f}% ({'IMPROVED' if improvement > 0 else 'WORSE'})")
            
            # Save performance comparison
            performance_summary = {
                'enhanced_qualifying_mae': results['qualifying']['ensemble_mae'],
                'enhanced_race_mae': results['race']['ensemble_mae'],
                'baseline_qualifying_mae': baseline_qualifying_mae,
                'baseline_race_mae': baseline_race_mae,
                'qualifying_improvement_pct': ((baseline_qualifying_mae - results['qualifying']['ensemble_mae']) / baseline_qualifying_mae) * 100,
                'race_improvement_pct': ((baseline_race_mae - results['race']['ensemble_mae']) / baseline_race_mae) * 100
            }
            
            # Save summary to file
            import json
            with open(os.path.join(self.models_dir, 'performance_comparison.json'), 'w') as f:
                json.dump(performance_summary, f, indent=2)
            
            results['performance_summary'] = performance_summary
            return results
            
        except Exception as e:
            logger.error(f"Enhanced training failed: {str(e)}")
            raise

def main():
    """Main training function"""
    trainer = EnhancedF1MLModel()
    results = trainer.train_pipeline()
    
    print("\n" + "="*70)
    print("ENHANCED F1 ML ENSEMBLE MODEL TRAINING COMPLETED")
    print("="*70)
    
    for target in ['qualifying', 'race']:
        print(f"\n{target.title()} Ensemble Performance:")
        print(f"  MAE: {results[target]['ensemble_mae']:.3f} positions")
        print(f"  RMSE: {results[target]['ensemble_rmse']:.3f} positions")
        print(f"  R²: {results[target]['ensemble_r2']:.3f}")
        
        print(f"\n  Individual Model Performance:")
        for model_name, metrics in results[target]['individual_models'].items():
            print(f"    {model_name}: MAE {metrics['mae']:.3f}, R² {metrics['r2']:.3f}")
    
    print("\nEnhanced ensemble models saved to ./enhanced_models/ directory")
    print("="*70)

if __name__ == "__main__":
    main()