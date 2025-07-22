#!/usr/bin/env python3
"""
Enhanced Ensemble F1 Prediction Service
Uses the trained ensemble models (XGBoost + Random Forest + Neural Network) for improved predictions.
"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedEnsembleF1PredictionService:
    def __init__(self):
        """Initialize the enhanced ensemble prediction service"""
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', 'enhanced_models')
        self.qualifying_models = None
        self.race_models = None
        self.label_encoders = None
        self.scaler = None
        self.robust_scaler = None
        self.feature_columns = None
        
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
        
        # Driver mappings for consistency
        self.driver_mapping = {
            'VER': 'Max Verstappen',
            'NOR': 'Lando Norris', 
            'LEC': 'Charles Leclerc',
            'HAM': 'Lewis Hamilton',
            'RUS': 'George Russell',
            'PIA': 'Oscar Piastri',
            'SAI': 'Carlos Sainz',
            'ALO': 'Fernando Alonso',
            'STR': 'Lance Stroll',
            'GAS': 'Pierre Gasly',
            'OCO': 'Esteban Ocon',
            'TSU': 'Yuki Tsunoda',
            'ALB': 'Alexander Albon',
            'HUL': 'Nico Hulkenberg',
            'BEA': 'Oliver Bearman',
            'ANT': 'Kimi Antonelli',
            'LAW': 'Liam Lawson',
            'COL': 'Franco Colapinto',
            'BOR': 'Gabriel Bortoleto',
            'HAD': 'Isack Hadjar'
        }
        
        # Team mappings for 2025
        self.team_mapping = {
            'Red Bull': 'Red Bull Racing Honda RBPT',
            'McLaren': 'McLaren Mercedes',
            'Ferrari': 'Scuderia Ferrari',
            'Mercedes': 'Mercedes',
            'Aston Martin': 'Aston Martin Aramco Mercedes',
            'Alpine': 'BWT Alpine F1 Team',
            'AlphaTauri': 'Visa Cash App RB F1 Team',
            'Williams': 'Williams Mercedes',
            'Haas': 'MoneyGram Haas F1 Team',
            'Kick Sauber': 'Kick Sauber F1 Team'
        }
        
        # Load models on initialization
        self.load_models()
    
    def load_models(self):
        """Load the trained ensemble models and preprocessors"""
        try:
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
            logger.info(f"Loaded {len(self.qualifying_models)} qualifying models")
            logger.info(f"Loaded {len(self.race_models)} race models")
            
        except Exception as e:
            logger.error(f"Failed to load enhanced ensemble models: {str(e)}")
            # Fallback to regular models
            logger.info("Falling back to regular models...")
            self.load_fallback_models()
    
    def load_fallback_models(self):
        """Load regular models as fallback"""
        try:
            fallback_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            self.qualifying_models = {'xgboost': joblib.load(os.path.join(fallback_dir, 'qualifying_model.pkl'))}
            self.race_models = {'xgboost': joblib.load(os.path.join(fallback_dir, 'race_model.pkl'))}
            self.label_encoders = joblib.load(os.path.join(fallback_dir, 'label_encoders.pkl'))
            self.scaler = joblib.load(os.path.join(fallback_dir, 'scaler.pkl'))
            self.feature_columns = joblib.load(os.path.join(fallback_dir, 'feature_columns.pkl'))
            logger.info("Fallback models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load fallback models: {str(e)}")
            raise
    
    def prepare_prediction_features(self, driver_code: str, track: str, weather: str, team: str = None) -> pd.DataFrame:
        """Prepare features for prediction"""
        
        # Map driver code to full name
        driver_name = self.driver_mapping.get(driver_code, driver_code)
        
        # Map team to full name
        if team:
            team_name = self.team_mapping.get(team, team)
        else:
            team_name = "Unknown"
        
        # Get track characteristics
        track_chars = self.track_characteristics.get(track, {
            'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 
            'overtaking': 'medium', 'elevation_change': 'low', 'tire_deg': 'medium'
        })
        
        # Create base feature set with reasonable defaults
        features = {
            'season': 2025,
            'season_race_number': 15,  # Mid-season default
            'grid_position': 10,  # Will be updated with qualifying prediction
            'avg_lap_time': 90.0,  # Default lap time
            'gap_to_winner': 0.0,
            'track_difficulty': track_chars['difficulty'],
            'grid_vs_quali_diff': 0.0,
            'weather_dry': 1 if weather.lower() == 'dry' else 0,
            'weather_wet': 1 if weather.lower() == 'wet' else 0,
            'dnf': 0,
            
            # Historical averages (estimated)
            'driver_historical_quali_avg': 10.0,
            'driver_historical_race_avg': 10.0,
            'driver_historical_points_avg': 5.0,
            'team_historical_quali_avg': 10.0,
            'team_historical_race_avg': 10.0,
            'team_historical_points_avg': 15.0,
            
            # Recent form
            'driver_recent_quali_avg': 10.0,
            'driver_recent_race_avg': 10.0,
            
            # Track-specific
            'driver_track_quali_avg': 10.0,
            'driver_track_race_avg': 10.0,
            
            # Season performance
            'driver_season_quali_avg': 10.0,
            'driver_season_race_avg': 10.0,
            
            # Trends
            'quali_trend': 0.0,
            'race_trend': 0.0,
            
            # Enhanced features
            'driver_momentum_3': 0.0,
            'driver_momentum_5': 0.0,
            'championship_position': 10.0,
            'championship_pressure': 1.0,
            'teammate_performance_diff': 0.0,
            'driver_track_advantage': 0.0,
            'weather_impact': 1.0,
            'podium_streak': 0.0,
            'dnf_streak': 0.0,
        }
        
        # Add encoded categorical features
        categorical_vars = {
            'driver': driver_name,
            'team': team_name,
            'race': track,
            'track_type': track_chars['type'],
            'track_speed': track_chars['speed'],
            'track_overtaking': track_chars['overtaking'],
            'track_elevation_change': track_chars['elevation_change'],
            'track_tire_deg': track_chars['tire_deg']
        }
        
        # Encode categorical variables
        for var, value in categorical_vars.items():
            if var in self.label_encoders:
                try:
                    encoded_value = self.label_encoders[var].transform([str(value)])[0]
                    features[f'{var}_encoded'] = encoded_value
                except ValueError:
                    # Handle unseen categories
                    features[f'{var}_encoded'] = 0
            else:
                features[f'{var}_encoded'] = 0
        
        # Create DataFrame with only the features used in training
        df_features = pd.DataFrame([features])
        
        # Filter to only include features that were used in training
        available_features = [col for col in self.feature_columns if col in df_features.columns]
        df_features = df_features[available_features]
        
        # Add any missing features with default values
        for col in self.feature_columns:
            if col not in df_features.columns:
                df_features[col] = 0.0
        
        # Reorder columns to match training order
        df_features = df_features[self.feature_columns]
        
        return df_features
    
    def predict_driver_performance(self, driver_code: str, track: str, weather: str, team: str = None) -> Dict:
        """Predict driver performance using ensemble models"""
        
        if not self.qualifying_models or not self.race_models:
            raise ValueError("Models not loaded")
        
        try:
            # Prepare features
            features = self.prepare_prediction_features(driver_code, track, weather, team)
            
            # Scale features
            features_scaled = pd.DataFrame(
                self.scaler.transform(features),
                columns=features.columns,
                index=features.index
            )
            
            # Ensemble weights
            weights = {'xgboost': 0.5, 'random_forest': 0.3, 'neural_network': 0.2}
            
            # Qualifying predictions
            quali_predictions = {}
            for name, model in self.qualifying_models.items():
                quali_predictions[name] = model.predict(features_scaled)[0]
            
            # Calculate weighted average for qualifying
            if len(quali_predictions) > 1:
                qualifying_pred = sum(weights.get(name, 1/len(quali_predictions)) * pred 
                                    for name, pred in quali_predictions.items())
            else:
                qualifying_pred = list(quali_predictions.values())[0]
            
            # Race predictions
            race_predictions = {}
            for name, model in self.race_models.items():
                race_predictions[name] = model.predict(features_scaled)[0]
            
            # Calculate weighted average for race
            if len(race_predictions) > 1:
                race_pred = sum(weights.get(name, 1/len(race_predictions)) * pred 
                              for name, pred in race_predictions.items())
            else:
                race_pred = list(race_predictions.values())[0]
            
            # Calculate confidence based on prediction variance
            if len(quali_predictions) > 1:
                quali_variance = np.var(list(quali_predictions.values()))
                qualifying_confidence = 1 / (1 + quali_variance)
            else:
                qualifying_confidence = 0.85
            
            if len(race_predictions) > 1:
                race_variance = np.var(list(race_predictions.values()))
                race_confidence = 1 / (1 + race_variance)
            else:
                race_confidence = 0.75
            
            # Ensure predictions are within valid range
            qualifying_pred = max(1, min(20, round(qualifying_pred)))
            race_pred = max(1, min(20, round(race_pred)))
            
            # Ensure confidence is within valid range
            qualifying_confidence = max(0.3, min(0.95, qualifying_confidence))
            race_confidence = max(0.3, min(0.95, race_confidence))
            
            logger.info(f"Enhanced prediction for {driver_code}: Q{qualifying_pred} ({qualifying_confidence:.2f}), R{race_pred} ({race_confidence:.2f})")
            
            return {
                'predicted_qualifying_position': qualifying_pred,
                'predicted_race_position': race_pred,
                'qualifying_confidence': qualifying_confidence,
                'race_confidence': race_confidence,
                'model_type': 'enhanced_ensemble',
                'individual_predictions': {
                    'qualifying': quali_predictions,
                    'race': race_predictions
                }
            }
            
        except Exception as e:
            logger.error(f"Error making enhanced prediction: {str(e)}")
            # Fallback to basic prediction
            return self.fallback_prediction(driver_code, track, weather, team)
    
    def fallback_prediction(self, driver_code: str, track: str, weather: str, team: str = None) -> Dict:
        """Fallback prediction method"""
        logger.warning("Using fallback prediction method")
        
        # Simple heuristic-based prediction
        driver_rankings = {
            'VER': (2, 3), 'NOR': (3, 4), 'LEC': (4, 5), 'HAM': (5, 6),
            'RUS': (6, 7), 'PIA': (7, 8), 'SAI': (8, 9), 'ALO': (9, 10)
        }
        
        quali_pos, race_pos = driver_rankings.get(driver_code, (10, 12))
        
        # Adjust for weather
        if weather.lower() == 'wet':
            if driver_code in ['HAM', 'VER']:
                quali_pos = max(1, quali_pos - 2)
                race_pos = max(1, race_pos - 2)
        
        return {
            'predicted_qualifying_position': quali_pos,
            'predicted_race_position': race_pos,
            'qualifying_confidence': 0.6,
            'race_confidence': 0.5,
            'model_type': 'fallback_heuristic'
        }

# Create global instance
enhanced_ensemble_service = EnhancedEnsembleF1PredictionService()