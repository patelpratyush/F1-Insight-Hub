import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
from typing import Dict, List, Optional
import joblib
import os

from .data_service import DataService

class PredictionService:
    def __init__(self):
        self.data_service = DataService()
        self.qualifying_model = None
        self.race_model = None
        self.label_encoders = {}
        self.scaler = None
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), '..', 'models')
        os.makedirs(self.model_path, exist_ok=True)
        
        self.driver_mapping = {
            'VER': 'Max Verstappen',
            'HAM': 'Lewis Hamilton',
            'RUS': 'George Russell',
            'LEC': 'Charles Leclerc',
            'SAI': 'Carlos Sainz',
            'NOR': 'Lando Norris',
            'PIA': 'Oscar Piastri',
            'ALO': 'Fernando Alonso',
            'STR': 'Lance Stroll',
            'TSU': 'Yuki Tsunoda',
            'RIC': 'Daniel Ricciardo',
            'GAS': 'Pierre Gasly',
            'OCO': 'Esteban Ocon',
            'ALB': 'Alexander Albon',
            'SAR': 'Logan Sargeant',
            'MAG': 'Kevin Magnussen',
            'HUL': 'Nico Hulkenberg',
            'BOT': 'Valtteri Bottas',
            'ZHO': 'Guanyu Zhou',
            'PER': 'Sergio Perez'
        }
        
        self.team_mapping = {
            'Red Bull': 'Red Bull Racing',
            'Mercedes': 'Mercedes',
            'Ferrari': 'Ferrari',
            'McLaren': 'McLaren',
            'Aston Martin': 'Aston Martin',
            'Alpine': 'Alpine',
            'AlphaTauri': 'RB',
            'Williams': 'Williams',
            'Haas': 'Haas F1 Team',
            'Alfa Romeo': 'Kick Sauber'
        }
    
    def get_2025_driver_transfers(self):
        """Map of drivers who changed teams for 2025"""
        return {
            'HAM': {'2024_team': 'Mercedes', '2025_team': 'Ferrari'},
            # Add more transfers as they happen
        }
    
    def _normalize_track_name(self, track: str) -> str:
        """Normalize track names to match data format"""
        track_mapping = {
            'Monaco Grand Prix': 'Monaco',
            'British Grand Prix': 'British',
            'Italian Grand Prix': 'Italian',
            'Bahrain Grand Prix': 'Bahrain',
            'Saudi Arabian Grand Prix': 'Saudi Arabian',
            'Australian Grand Prix': 'Australian',
            'Japanese Grand Prix': 'Japanese',
            'Chinese Grand Prix': 'Chinese',
            'Miami Grand Prix': 'Miami',
            'Emilia Romagna Grand Prix': 'Emilia Romagna',
            'Spanish Grand Prix': 'Spanish',
            'Canadian Grand Prix': 'Canadian',
            'Austrian Grand Prix': 'Austrian',
            'Hungarian Grand Prix': 'Hungarian',
            'Belgian Grand Prix': 'Belgian',
            'Dutch Grand Prix': 'Dutch',
            'Singapore Grand Prix': 'Singapore',
            'United States Grand Prix': 'United States',
            'Mexico City Grand Prix': 'Mexico City',
            'São Paulo Grand Prix': 'São Paulo',
            'Las Vegas Grand Prix': 'Las Vegas',
            'Qatar Grand Prix': 'Qatar',
            'Abu Dhabi Grand Prix': 'Abu Dhabi',
            'Azerbaijan Grand Prix': 'Azerbaijan'
        }
        return track_mapping.get(track, track.replace(' Grand Prix', ''))
    
    def create_features(self, driver: str, track: str, weather: str, team: str, historical_data: pd.DataFrame = None) -> Dict:
        # Normalize track name for consistent lookups
        normalized_track = self._normalize_track_name(track)
        track_chars = self.data_service.get_track_characteristics(normalized_track)
        team_perf = self.data_service.get_team_performance_data(self.team_mapping.get(team, team))
        
        # Weather factors
        weather_factor = 1.0
        if weather == 'wet':
            weather_factor = 1.2
        elif weather == 'mixed':
            weather_factor = 1.1
        
        # Driver historical performance at this track
        driver_track_performance = self._get_driver_track_performance(driver, normalized_track, historical_data)
        
        # Recent form (last 5 races)
        recent_form = self._get_recent_form(driver, historical_data)
        
        # Championship standing simulation
        championship_position = self._estimate_championship_position(driver)
        
        # 2025 specific features
        transfers = self.get_2025_driver_transfers()
        current_season = 2025  # Assuming current predictions are for 2025
        
        # Handle driver transfers
        has_transfer = driver in transfers and current_season == 2025
        
        features = {
            'driver': driver,
            'team': team,
            'track': self._normalize_track_name(track),  # Normalize track names
            'season': current_season,
            'is_2025': 1 if current_season == 2025 else 0,
            'has_transfer': 1 if has_transfer else 0,
            
            # Driver overall performance
            'driver_avg_quali': driver_track_performance['avg_qualifying'],
            'driver_avg_race': driver_track_performance['avg_race'],
            'driver_avg_points': recent_form['avg_points'],
            'driver_races_count': driver_track_performance['races_count'],
            
            # Recent form (last 5 races)
            'recent_avg_quali': recent_form['avg_qualifying'],
            'recent_avg_race': recent_form['avg_race'],
            'recent_podiums': recent_form['podiums'],
            'recent_wins': recent_form['wins'],
            'recent_points': recent_form['avg_points'],
            
            # Team performance
            'team_avg_quali': team_perf['avg_qualifying_position'],
            'team_avg_race': team_perf['avg_race_position'],
            'team_avg_points': recent_form['avg_points'],  # Approximate
            
            # Driver at specific track
            'driver_track_avg_quali': driver_track_performance['avg_qualifying'],
            'driver_track_avg_race': driver_track_performance['avg_race'],
            'driver_track_races': driver_track_performance['races_count'],
            
            # Championship context
            'championship_points': recent_form['avg_points'] * driver_track_performance['races_count'],
        }
        
        return features
    
    def _get_driver_track_performance(self, driver: str, track: str, historical_data: pd.DataFrame) -> Dict:
        """Get driver's historical performance at specific track"""
        if historical_data is None or historical_data.empty:
            return {
                'avg_qualifying': 10.0, 'avg_race': 10.0, 'best_qualifying': 10.0, 
                'best_race': 10.0, 'races_count': 0
            }
        
        driver_track_data = historical_data[
            (historical_data['driver'] == driver) & 
            (historical_data['track'] == track)
        ]
        
        if driver_track_data.empty:
            return {
                'avg_qualifying': 10.0, 'avg_race': 10.0, 'best_qualifying': 10.0, 
                'best_race': 10.0, 'races_count': 0
            }
        
        return {
            'avg_qualifying': driver_track_data['qualifying_position'].mean(),
            'avg_race': driver_track_data['race_position'].mean(),
            'best_qualifying': driver_track_data['qualifying_position'].min(),
            'best_race': driver_track_data['race_position'].min(),
            'races_count': len(driver_track_data)
        }
    
    def _get_recent_form(self, driver: str, historical_data: pd.DataFrame) -> Dict:
        """Get driver's recent form (last 5 races)"""
        if historical_data is None or historical_data.empty:
            return {
                'avg_qualifying': 10.0, 'avg_race': 10.0, 'avg_points': 5.0, 
                'podiums': 0, 'wins': 0
            }
        
        driver_data = historical_data[historical_data['driver'] == driver].tail(5)
        
        if driver_data.empty:
            return {
                'avg_qualifying': 10.0, 'avg_race': 10.0, 'avg_points': 5.0, 
                'podiums': 0, 'wins': 0
            }
        
        return {
            'avg_qualifying': driver_data['qualifying_position'].mean(),
            'avg_race': driver_data['race_position'].mean(),
            'avg_points': driver_data['points'].mean(),
            'podiums': len(driver_data[driver_data['race_position'] <= 3]),
            'wins': len(driver_data[driver_data['race_position'] == 1])
        }
    
    def _estimate_championship_position(self, driver: str) -> int:
        """Estimate current championship position"""
        driver_standings = {
            'VER': 1, 'LEC': 2, 'RUS': 3, 'HAM': 4, 'SAI': 5, 'NOR': 6, 
            'PIA': 7, 'ALO': 8, 'PER': 9, 'STR': 10, 'TSU': 11, 'GAS': 12,
            'OCO': 13, 'ALB': 14, 'MAG': 15, 'HUL': 16, 'RIC': 17, 'BOT': 18,
            'ZHO': 19, 'SAR': 20
        }
        return driver_standings.get(driver, 15)
    
    def _get_driver_experience(self, driver: str) -> int:
        """Get driver experience level"""
        experience_map = {
            'HAM': 10, 'ALO': 10, 'VER': 8, 'LEC': 6, 'RUS': 5, 'PER': 7,
            'SAI': 6, 'NOR': 5, 'PIA': 2, 'STR': 4, 'TSU': 3, 'GAS': 6,
            'OCO': 6, 'ALB': 4, 'MAG': 5, 'HUL': 7, 'RIC': 8, 'BOT': 8,
            'ZHO': 2, 'SAR': 1
        }
        return experience_map.get(driver, 3)
    
    def _get_qualifying_to_race_conversion(self, driver: str, historical_data: pd.DataFrame) -> float:
        """Calculate how well driver converts qualifying position to race position"""
        if historical_data is None or historical_data.empty:
            return 0.0
        
        driver_data = historical_data[historical_data['driver'] == driver]
        if driver_data.empty:
            return 0.0
        
        # Positive value means gains positions, negative means loses positions
        conversion = (driver_data['qualifying_position'] - driver_data['race_position']).mean()
        return conversion
    
    def _get_wet_weather_performance(self, driver: str, weather: str) -> float:
        """Get driver's wet weather performance factor"""
        if weather != 'wet':
            return 1.0
        
        wet_weather_specialists = {
            'HAM': 1.3, 'VER': 1.2, 'RUS': 1.1, 'NOR': 1.1, 'GAS': 1.1,
            'ALO': 1.1, 'OCO': 1.1, 'LEC': 1.0, 'SAI': 1.0, 'PER': 0.9,
            'PIA': 0.9, 'STR': 0.9, 'TSU': 0.9, 'ALB': 0.9, 'MAG': 0.9,
            'HUL': 0.9, 'RIC': 1.0, 'BOT': 1.0, 'ZHO': 0.8, 'SAR': 0.8
        }
        return wet_weather_specialists.get(driver, 1.0)
    
    def train_model(self, force_retrain: bool = False):
        qualifying_model_file = os.path.join(self.model_path, 'f1_qualifying_gbm_model.pkl')
        race_model_file = os.path.join(self.model_path, 'f1_race_gbm_model.pkl')
        encoders_file = os.path.join(self.model_path, 'label_encoders.pkl')
        scaler_file = os.path.join(self.model_path, 'feature_scaler.pkl')
        
        if not force_retrain and all(os.path.exists(f) for f in [qualifying_model_file, race_model_file, encoders_file, scaler_file]):
            try:
                self.qualifying_model = joblib.load(qualifying_model_file)
                self.race_model = joblib.load(race_model_file)
                self.label_encoders = joblib.load(encoders_file)
                self.scaler = joblib.load(scaler_file)
                self.is_trained = True
                return
            except:
                pass
        
        print("Training model with FastF1 data...")
        
        # Try to load existing data first
        data_file = os.path.join(self.model_path, '..', 'f1_data.csv')
        if os.path.exists(data_file):
            print("Using cached F1 data...")
            try:
                combined_data = pd.read_csv(data_file)
                self._train_with_data(combined_data)
                return
            except Exception as e:
                print(f"Error loading cached data: {e}")
        
        # No API calls - only cached data
        print("No cached data available and API calls disabled")
        print("Please run the download script first: python3 download_current_data.py")
        self._create_fallback_model()
        return
        
        if len(combined_data) < 20:
            print("Insufficient data, using fallback model...")
            self._create_fallback_model()
            return
        
        self._train_with_data(combined_data)
    
    def _train_with_data(self, combined_data: pd.DataFrame):
        """Train the Gradient Boosting models with structured F1 data"""
        print(f"Training Gradient Boosting models with {len(combined_data)} data points...")
        
        features = []
        qualifying_targets = []
        race_targets = []
        
        for _, row in combined_data.iterrows():
            try:
                # Create enhanced features using the historical data
                feature_row = self.create_features(
                    driver=row['driver'],
                    track=row['track'],
                    weather='dry',  # Default, can be enhanced later
                    team=row['team'],
                    historical_data=combined_data
                )
                
                features.append(feature_row)
                qualifying_targets.append(row['qualifying_position'])
                race_targets.append(row['race_position'])
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        if len(features) < 20:
            print("Insufficient features, using fallback model...")
            self._create_fallback_model()
            return
        
        df_features = pd.DataFrame(features)
        
        # Encode categorical variables
        categorical_columns = ['driver', 'track', 'team', 'weather']
        for col in categorical_columns:
            if col in df_features.columns:
                self.label_encoders[col] = LabelEncoder()
                df_features[col] = self.label_encoders[col].fit_transform(df_features[col])
        
        # Prepare numerical features
        X = df_features.select_dtypes(include=[np.number])
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Prepare targets
        y_qualifying = np.array(qualifying_targets)
        y_race = np.array(race_targets)
        
        # Split data
        X_train, X_test, y_qual_train, y_qual_test, y_race_train, y_race_test = train_test_split(
            X_scaled, y_qualifying, y_race, test_size=0.2, random_state=42
        )
        
        # Train Gradient Boosting models
        print("Training Qualifying Position Predictor...")
        self.qualifying_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )
        self.qualifying_model.fit(X_train, y_qual_train)
        
        print("Training Race Position Predictor...")
        self.race_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )
        self.race_model.fit(X_train, y_race_train)
        
        # Evaluate models
        y_qual_pred = self.qualifying_model.predict(X_test)
        y_race_pred = self.race_model.predict(X_test)
        
        qual_mae = mean_absolute_error(y_qual_test, y_qual_pred)
        race_mae = mean_absolute_error(y_race_test, y_race_pred)
        
        print(f"Qualifying Model MAE: {qual_mae:.2f}")
        print(f"Race Model MAE: {race_mae:.2f}")
        
        # Save models
        qualifying_model_file = os.path.join(self.model_path, 'f1_qualifying_gbm_model.pkl')
        race_model_file = os.path.join(self.model_path, 'f1_race_gbm_model.pkl')
        encoders_file = os.path.join(self.model_path, 'label_encoders.pkl')
        scaler_file = os.path.join(self.model_path, 'feature_scaler.pkl')
        
        joblib.dump(self.qualifying_model, qualifying_model_file)
        joblib.dump(self.race_model, race_model_file)
        joblib.dump(self.label_encoders, encoders_file)
        joblib.dump(self.scaler, scaler_file)
        
        print("Gradient Boosting models trained and saved successfully!")
        self.is_trained = True
    
    def _create_fallback_model(self):
        print("Creating fallback model with synthetic data...")
        
        driver_rankings = {
            'VER': 1, 'HAM': 3, 'RUS': 4, 'LEC': 2, 'SAI': 5,
            'NOR': 6, 'PIA': 8, 'ALO': 7, 'PER': 9, 'STR': 12,
            'TSU': 15, 'RIC': 13, 'GAS': 11, 'OCO': 14, 'ALB': 16,
            'SAR': 19, 'MAG': 17, 'HUL': 18, 'BOT': 20, 'ZHO': 21
        }
        
        team_rankings = {
            'Red Bull': 1, 'Ferrari': 2, 'Mercedes': 3, 'McLaren': 4,
            'Aston Martin': 5, 'Alpine': 6, 'AlphaTauri': 7, 'Williams': 8,
            'Haas': 9, 'Alfa Romeo': 10
        }
        
        self.fallback_driver_rankings = driver_rankings
        self.fallback_team_rankings = team_rankings
        self.is_trained = True
    
    def predict_driver_performance(self, driver: str, track: str, weather: str, team: str) -> Dict:
        if not self.is_trained:
            self.train_model()
        
        if self.qualifying_model is None or self.race_model is None:
            return self._fallback_prediction(driver, track, weather, team)
        
        # Load historical data for feature engineering
        data_file = os.path.join(self.model_path, '..', 'f1_data.csv')
        historical_data = None
        if os.path.exists(data_file):
            try:
                historical_data = pd.read_csv(data_file)
                print(f"Using CSV data: {len(historical_data)} records from {sorted(historical_data['season'].unique())}")
            except Exception as e:
                print(f"Error loading CSV data: {e}")
                pass
        
        # Create enhanced features
        features = self.create_features(driver, track, weather, team, historical_data)
        
        try:
            # Prepare feature row
            feature_row = {}
            for col, encoder in self.label_encoders.items():
                if col in features:
                    try:
                        feature_row[col] = encoder.transform([features[col]])[0]
                    except ValueError:
                        # Handle unseen categorical values
                        feature_row[col] = 0
            
            # Add numerical features
            for key, value in features.items():
                if key not in self.label_encoders and isinstance(value, (int, float)):
                    feature_row[key] = value
            
            # Convert to DataFrame and select numerical features
            X = pd.DataFrame([feature_row])
            X = X.select_dtypes(include=[np.number])
            
            if len(X.columns) == 0:
                return self._fallback_prediction(driver, track, weather, team)
            
            # Scale features
            if self.scaler is not None:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X.values
            
            # Make predictions using Gradient Boosting models
            qualifying_prediction = self.qualifying_model.predict(X_scaled)[0]
            race_prediction = self.race_model.predict(X_scaled)[0]
            
            # Ensure predictions are within valid range
            qualifying_prediction = max(1, min(20, round(qualifying_prediction)))
            race_prediction = max(1, min(20, round(race_prediction)))
            
            # Calculate confidence based on model uncertainty and feature quality
            qualifying_confidence = self._calculate_confidence(qualifying_prediction, features, 'qualifying')
            race_confidence = self._calculate_confidence(race_prediction, features, 'race')
            
            return {
                'qualifying_position': int(qualifying_prediction),
                'race_position': int(race_prediction),
                'qualifying_confidence': round(qualifying_confidence, 2),
                'race_confidence': round(race_confidence, 2)
            }
        
        except Exception as e:
            print(f"Gradient Boosting prediction error: {e}")
            return self._fallback_prediction(driver, track, weather, team)
    
    def _calculate_confidence(self, prediction: float, features: Dict, prediction_type: str) -> float:
        """Calculate prediction confidence based on feature quality and model context"""
        base_confidence = 0.75
        
        # Adjust confidence based on data availability
        if features.get('driver_track_races_count', 0) > 3:
            base_confidence += 0.1  # More historical data at track
        
        if features.get('recent_wins', 0) > 0:
            base_confidence += 0.05  # Recent good form
        
        if features.get('driver_experience', 0) > 7:
            base_confidence += 0.05  # Experienced driver
        
        # Weather uncertainty
        if features.get('weather') == 'wet':
            base_confidence -= 0.1
        elif features.get('weather') == 'mixed':
            base_confidence -= 0.05
        
        # Position uncertainty (middle positions are less predictable)
        position_uncertainty = abs(prediction - 10.5) / 20.0
        base_confidence += position_uncertainty * 0.2
        
        # Ensure confidence is within reasonable bounds
        return max(0.5, min(0.95, base_confidence))
    
    def _predict_race_position(self, qualifying_position: int, features: Dict) -> int:
        """Predict race position based on qualifying position and other factors"""
        race_position = qualifying_position
        
        # Weather impact on race vs qualifying
        weather_multiplier = features.get('weather_multiplier', 1.0)
        if weather_multiplier > 1.0:  # Wet/mixed conditions
            # Some drivers perform better in wet conditions
            if features.get('driver') in ['HAM', 'VER', 'RUS']:
                race_position -= 1  # Better in wet
            elif features.get('driver') in ['SAR', 'ZHO']:
                race_position += 1  # Worse in wet
        
        # Track characteristics impact
        track_difficulty = features.get('track_difficulty', 7)
        if track_difficulty > 8:  # High difficulty tracks
            # Experienced drivers perform better
            if features.get('driver') in ['HAM', 'ALO', 'VER']:
                race_position -= 1
        
        # Team reliability factor
        team_reliability = features.get('team_reliability', 0.8)
        if team_reliability < 0.7:
            race_position += 2  # Reliability issues
        
        # Random race incidents (safety cars, strategy, etc.)
        import random
        random.seed(hash(f"{features.get('driver')}{features.get('track')}") % 1000)
        incident_factor = random.randint(-2, 3)  # -2 to +3 position change
        race_position += incident_factor
        
        return max(1, min(20, round(race_position)))
    
    def _fallback_prediction(self, driver: str, track: str, weather: str, team: str) -> Dict:
        base_position = self.fallback_driver_rankings.get(driver, 15)
        team_factor = self.fallback_team_rankings.get(team, 8)
        
        track_chars = self.data_service.get_track_characteristics(track)
        track_difficulty = track_chars['difficulty']
        
        weather_penalty = 0
        if weather == 'wet':
            weather_penalty = 2
        elif weather == 'mixed':
            weather_penalty = 1
        
        qualifying_position = base_position + (team_factor - 5) * 0.3 + weather_penalty
        qualifying_position = max(1, min(20, round(qualifying_position)))
        
        # Race position prediction based on qualifying
        race_position = qualifying_position
        
        # Weather impact on race performance
        if weather == 'wet':
            if driver in ['HAM', 'VER', 'RUS']:
                race_position -= 2  # Better in wet
            elif driver in ['SAR', 'ZHO']:
                race_position += 2  # Worse in wet
        
        # Track difficulty impact
        if track_difficulty > 8:
            if driver in ['HAM', 'ALO', 'VER']:
                race_position -= 1  # Better on difficult tracks
        
        # Team reliability
        if team in ['Haas', 'Williams']:
            race_position += 1  # Less reliable
        elif team in ['Red Bull', 'Mercedes']:
            race_position -= 1  # More reliable
        
        # Random race factors
        import random
        random.seed(hash(f"{driver}{track}") % 1000)
        race_position += random.randint(-2, 3)
        
        race_position = max(1, min(20, round(race_position)))
        
        qualifying_confidence = 0.75
        race_confidence = 0.65  # Lower confidence for race due to more variables
        
        return {
            'qualifying_position': int(qualifying_position),
            'race_position': int(race_position),
            'qualifying_confidence': qualifying_confidence,
            'race_confidence': race_confidence
        }