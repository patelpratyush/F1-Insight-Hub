#!/usr/bin/env python3
"""
Enhanced F1 Prediction Service using the comprehensive ML model
"""

import pandas as pd
import numpy as np
import os
import sys
import joblib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add the parent directory to Python path to import the ML model
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from train_ml_model import F1MLModelTrainer

logger = logging.getLogger(__name__)

class EnhancedPredictionService:
    def __init__(self):
        """Initialize the enhanced prediction service"""
        self.model_trainer = F1MLModelTrainer()
        self.models_loaded = False
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'f1_data.csv')
        
        # Current season driver and team mappings
        self.current_drivers = {
            'VER': 'Max Verstappen',
            'NOR': 'Lando Norris', 
            'BOR': 'Gabriel Bortoleto',
            'HAD': 'Isack Hadjar',
            'GAS': 'Pierre Gasly',
            'ANT': 'Andrea Kimi Antonelli',
            'ALO': 'Fernando Alonso',
            'LEC': 'Charles Leclerc',
            'STR': 'Lance Stroll',
            'TSU': 'Yuki Tsunoda',
            'ALB': 'Alexander Albon',
            'HUL': 'Nico Hulkenberg',
            'LAW': 'Liam Lawson',
            'OCO': 'Esteban Ocon',
            'COL': 'Franco Colapinto',
            'HAM': 'Lewis Hamilton',
            'SAI': 'Carlos Sainz',
            'RUS': 'George Russell',
            'PIA': 'Oscar Piastri',
            'BEA': 'Oliver Bearman'
        }
        
        self.current_teams = {
            'Red Bull': 'Red Bull Racing Honda RBPT',
            'Ferrari': 'Scuderia Ferrari',
            'Mercedes': 'Mercedes',
            'McLaren': 'McLaren Mercedes',
            'Aston Martin': 'Aston Martin Aramco Mercedes',
            'Alpine': 'BWT Alpine F1 Team',
            'AlphaTauri': 'Visa Cash App RB F1 Team',
            'Williams': 'Williams Mercedes',
            'Haas': 'MoneyGram Haas F1 Team',
            'Kick Sauber': 'Kick Sauber F1 Team'
        }
        
        # Initialize the ML model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize or load the ML model"""
        try:
            # Check if trained models exist
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            if os.path.exists(os.path.join(models_dir, 'qualifying_model.pkl')):
                logger.info("Loading existing trained models...")
                self.model_trainer.load_models()
                self.models_loaded = True
            else:
                logger.info("No existing models found. Training new models...")
                self._train_models()
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            self.models_loaded = False
    
    def _train_models(self):
        """Train the ML models if not already trained"""
        try:
            if not os.path.exists(self.data_file):
                logger.error(f"Data file not found: {self.data_file}")
                logger.error("Please run the data download script first: python3 download_current_data.py")
                return False
            
            # Train the models
            results = self.model_trainer.train_pipeline()
            self.models_loaded = True
            logger.info("Models trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training models: {e}")
            self.models_loaded = False
            return False
    
    def _normalize_driver_name(self, driver_input: str) -> str:
        """Normalize driver name to match the data format"""
        # Handle different input formats
        if driver_input in self.current_drivers:
            return self.current_drivers[driver_input]
        
        # Handle full names
        driver_mapping = {
            'Max Verstappen': 'M VERSTAPPEN',
            'Lando Norris': 'L NORRIS',
            'Gabriel Bortoleto': 'G BORTOLETO',
            'Isack Hadjar': 'I HADJAR',
            'Pierre Gasly': 'P GASLY',
            'Kimi Antonelli': 'K ANTONELLI',
            'Fernando Alonso': 'F ALONSO',
            'Charles Leclerc': 'C LECLERC',
            'Lance Stroll': 'L STROLL',
            'Yuki Tsunoda': 'Y TSUNODA',
            'Alexander Albon': 'A ALBON',
            'Nico Hulkenberg': 'N HULKENBERG',
            'Liam Lawson': 'L LAWSON',
            'Esteban Ocon': 'E OCON',
            'Franco Colapinto': 'F COLAPINTO',
            'Lewis Hamilton': 'L HAMILTON',
            'Carlos Sainz': 'C SAINZ',
            'George Russell': 'G RUSSELL',
            'Oscar Piastri': 'O PIASTRI',
            'Oliver Bearman': 'O BEARMAN'
        }
        
        return driver_mapping.get(driver_input, driver_input)
    
    def _normalize_team_name(self, team_input: str) -> str:
        """Normalize team name to match the data format"""
        return self.current_teams.get(team_input, team_input)
    
    def _normalize_track_name(self, track_input: str) -> str:
        """Normalize track name to match the data format"""
        # Remove 'Grand Prix' suffix if present
        if track_input.endswith(' Grand Prix'):
            return track_input
        else:
            return f"{track_input} Grand Prix"
    
    def _create_prediction_features(self, driver: str, track: str, weather: str, team: str) -> pd.DataFrame:
        """Create feature vector for prediction"""
        # Normalize inputs
        driver_normalized = self._normalize_driver_name(driver)
        team_normalized = self._normalize_team_name(team)
        track_normalized = self._normalize_track_name(track)
        
        # Load historical data
        try:
            historical_data = pd.read_csv(self.data_file)
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            historical_data = pd.DataFrame()
        
        # Create base features similar to training data
        current_season = 2025
        
        # Get historical performance
        driver_history = historical_data[historical_data['driver'] == driver_normalized]
        team_history = historical_data[historical_data['team'] == team_normalized]
        track_history = historical_data[historical_data['race'] == track_normalized]
        
        # Calculate historical averages
        driver_quali_avg = driver_history['qualifying_position'].mean() if not driver_history.empty else 10.0
        driver_race_avg = driver_history['race_position'].mean() if not driver_history.empty else 10.0
        driver_points_avg = driver_history['points'].mean() if not driver_history.empty else 5.0
        
        team_quali_avg = team_history['qualifying_position'].mean() if not team_history.empty else 10.0
        team_race_avg = team_history['race_position'].mean() if not team_history.empty else 10.0
        team_points_avg = team_history['points'].mean() if not team_history.empty else 5.0
        
        # Recent form (last 3 races)
        recent_driver_history = driver_history.tail(3)
        recent_quali_avg = recent_driver_history['qualifying_position'].mean() if not recent_driver_history.empty else 10.0
        recent_race_avg = recent_driver_history['race_position'].mean() if not recent_driver_history.empty else 10.0
        
        # Track-specific performance
        driver_track_history = historical_data[
            (historical_data['driver'] == driver_normalized) & 
            (historical_data['race'] == track_normalized)
        ]
        track_quali_avg = driver_track_history['qualifying_position'].mean() if not driver_track_history.empty else 10.0
        track_race_avg = driver_track_history['race_position'].mean() if not driver_track_history.empty else 10.0
        
        # Season performance
        season_driver_history = driver_history[driver_history['season'] == current_season]
        season_quali_avg = season_driver_history['qualifying_position'].mean() if not season_driver_history.empty else 10.0
        season_race_avg = season_driver_history['race_position'].mean() if not season_driver_history.empty else 10.0
        
        # Performance trends
        if len(driver_history) > 1:
            quali_trend = driver_history['qualifying_position'].diff().tail(3).mean()
            race_trend = driver_history['race_position'].diff().tail(3).mean()
        else:
            quali_trend = 0.0
            race_trend = 0.0
        
        # Track characteristics
        track_chars = self.model_trainer.track_characteristics.get(track_normalized, {})
        track_difficulty = track_chars.get('difficulty', 7)
        
        # Create feature vector
        features = pd.DataFrame({
            'season': [current_season],
            'season_race_number': [12],  # Approximate mid-season
            'grid_position': [driver_quali_avg],  # Approximate from qualifying
            'avg_lap_time': [90.0],  # Default lap time
            'gap_to_winner': [0.0],  # Default gap
            'track_difficulty': [track_difficulty],
            'grid_vs_quali_diff': [0.0],  # Default no difference
            'weather_dry': [1 if weather.lower() == 'dry' else 0],
            'weather_wet': [1 if weather.lower() == 'wet' else 0],
            'dnf': [0],  # Assume no DNF
            'driver_historical_quali_avg': [driver_quali_avg],
            'driver_historical_race_avg': [driver_race_avg],
            'driver_historical_points_avg': [driver_points_avg],
            'team_historical_quali_avg': [team_quali_avg],
            'team_historical_race_avg': [team_race_avg],
            'team_historical_points_avg': [team_points_avg],
            'driver_recent_quali_avg': [recent_quali_avg],
            'driver_recent_race_avg': [recent_race_avg],
            'driver_track_quali_avg': [track_quali_avg],
            'driver_track_race_avg': [track_race_avg],
            'driver_season_quali_avg': [season_quali_avg],
            'driver_season_race_avg': [season_race_avg],
            'quali_trend': [quali_trend],
            'race_trend': [race_trend],
            'driver_encoded': [0],  # Will be encoded properly
            'team_encoded': [0],    # Will be encoded properly
            'race_encoded': [0],    # Will be encoded properly
            'track_type_encoded': [0],  # Will be encoded properly
            'track_speed_encoded': [0],  # Will be encoded properly
            'overtaking_difficulty_encoded': [0]  # Will be encoded properly
        })
        
        # Handle categorical encoding
        try:
            if hasattr(self.model_trainer, 'label_encoders'):
                # Apply label encoders if available
                categorical_mapping = {
                    'driver': driver_normalized,
                    'team': team_normalized,
                    'race': track_normalized,
                    'track_type': track_chars.get('type', 'mixed'),
                    'track_speed': track_chars.get('speed', 'medium'),
                    'overtaking_difficulty': track_chars.get('overtaking', 'medium')
                }
                
                for cat_col, value in categorical_mapping.items():
                    encoded_col = f"{cat_col}_encoded"
                    if cat_col in self.model_trainer.label_encoders:
                        try:
                            encoded_value = self.model_trainer.label_encoders[cat_col].transform([value])[0]
                            features[encoded_col] = [encoded_value]
                        except (ValueError, KeyError):
                            features[encoded_col] = [0]  # Default for unseen categories
        except Exception as e:
            logger.warning(f"Error encoding categorical features: {e}")
        
        # Filter to only include features that exist in the trained model
        if hasattr(self.model_trainer, 'feature_columns'):
            available_features = [col for col in self.model_trainer.feature_columns if col in features.columns]
            features = features[available_features]
        
        return features
    
    def predict_driver_performance(self, driver: str, track: str, weather: str, team: str) -> Dict:
        """Predict driver performance using the trained ML model"""
        try:
            # Ensure models are loaded
            if not self.models_loaded:
                logger.warning("Models not loaded. Attempting to train/load models...")
                self._initialize_model()
                
                if not self.models_loaded:
                    return self._fallback_prediction(driver, track, weather, team)
            
            # Create feature vector
            features = self._create_prediction_features(driver, track, weather, team)
            
            # Make prediction
            predictions = self.model_trainer.predict_with_confidence(features)
            
            return {
                'qualifying_position': int(predictions['qualifying_position'][0]),
                'race_position': int(predictions['race_position'][0]),
                'qualifying_confidence': float(predictions['qualifying_confidence'][0]),
                'race_confidence': float(predictions['race_confidence'][0])
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return self._fallback_prediction(driver, track, weather, team)
    
    def _fallback_prediction(self, driver: str, track: str, weather: str, team: str) -> Dict:
        """Fallback prediction when ML model is unavailable"""
        logger.warning("Using fallback prediction method")
        
        # Basic driver rankings
        driver_rankings = {
            'VER': 1, 'NOR': 2, 'LEC': 3, 'HAM': 4, 'RUS': 5, 'PIA': 6,
            'ALO': 7, 'SAI': 8, 'TSU': 9, 'ALB': 10, 'GAS': 11, 'OCO': 12,
            'HUL': 13, 'LAW': 14, 'STR': 15, 'BEA': 16, 'ANT': 17, 'COL': 18,
            'BOR': 19, 'HAD': 20
        }
        
        # Team performance adjustments
        team_adjustments = {
            'Red Bull': -2, 'Ferrari': -1, 'Mercedes': -1, 'McLaren': -1,
            'Aston Martin': 0, 'Alpine': 1, 'AlphaTauri': 1, 'Williams': 2,
            'Haas': 2, 'Kick Sauber': 3
        }
        
        # Get base position
        base_position = driver_rankings.get(driver, 15)
        team_adjustment = team_adjustments.get(team, 0)
        
        # Weather impact
        weather_impact = 0
        if weather.lower() == 'wet':
            # Some drivers are better in wet conditions
            if driver in ['HAM', 'VER', 'RUS', 'NOR']:
                weather_impact = -2
            elif driver in ['ANT', 'BOR', 'HAD']:
                weather_impact = 2
        
        # Calculate positions
        qualifying_position = max(1, min(20, base_position + team_adjustment + weather_impact))
        race_position = max(1, min(20, qualifying_position + np.random.randint(-3, 4)))
        
        return {
            'qualifying_position': int(qualifying_position),
            'race_position': int(race_position),
            'qualifying_confidence': 0.65,  # Lower confidence for fallback
            'race_confidence': 0.55
        }
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        if not self.models_loaded:
            return {
                'model_type': 'Fallback',
                'trained': False,
                'data_points': 0,
                'features': 0
            }
        
        try:
            data = pd.read_csv(self.data_file)
            return {
                'model_type': 'XGBoost Gradient Boosting',
                'trained': True,
                'data_points': len(data),
                'features': len(self.model_trainer.feature_columns) if hasattr(self.model_trainer, 'feature_columns') else 0,
                'seasons': sorted(data['season'].unique()) if 'season' in data.columns else []
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                'model_type': 'XGBoost Gradient Boosting',
                'trained': True,
                'data_points': 0,
                'features': 0
            }
    
    def retrain_model(self) -> bool:
        """Retrain the model with current data"""
        try:
            logger.info("Retraining model...")
            results = self.model_trainer.train_pipeline()
            self.models_loaded = True
            logger.info("Model retrained successfully")
            return True
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            return False