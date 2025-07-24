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
    def __init__(self, data_file: str = 'f1_data.csv'):
        """Initialize the enhanced F1 ML model with ensemble methods"""
        self.data_file = os.path.join(os.path.dirname(__file__), data_file)
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
        
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        df = pd.read_csv(self.data_file)
        logger.info(f"Loaded {len(df)} records from {len(df['season'].unique())} seasons")
        
        # Data cleaning
        df = df.dropna(subset=['qualifying_position', 'race_position'])
        df['avg_lap_time'] = df['avg_lap_time'].fillna(df['avg_lap_time'].mean())
        df['gap_to_winner'] = df['gap_to_winner'].fillna(0)
        
        # Enhanced feature engineering
        df = self._engineer_enhanced_features(df)
        
        logger.info(f"Data prepared with {len(df)} records and {len(df.columns)} features")
        return df
    
    def _engineer_enhanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive features including rivalries and team dynamics"""
        logger.info("Engineering enhanced features...")
        
        # Sort by season and race for time-series features
        df = df.sort_values(['season', 'race', 'qualifying_position'])
        
        # Enhanced track characteristics
        for char in ['type', 'difficulty', 'speed', 'overtaking', 'elevation_change', 'tire_deg']:
            df[f'track_{char}'] = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get(char, 'medium'))
        
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
        
        # NEW: Enhanced momentum features with safe polyfit
        def safe_momentum(y):
            try:
                if len(y) < 2:
                    return 0.0
                return -np.polyfit(range(len(y)), y, 1)[0]
            except (np.linalg.LinAlgError, ValueError):
                return 0.0
        
        df['driver_momentum_3'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.rolling(window=3, min_periods=2).apply(safe_momentum).shift(1)
        )
        df['driver_momentum_5'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.rolling(window=5, min_periods=3).apply(safe_momentum).shift(1)
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
        
        # NEW: Track-specific performance
        df['driver_track_advantage'] = df.groupby(['driver', 'race'])['race_position'].transform(
            lambda x: df.groupby('race')['race_position'].transform('mean') - x.expanding().mean().shift(1)
        )
        
        # NEW: Weather impact features
        df['weather_impact'] = df.apply(self._calculate_weather_impact, axis=1)
        
        # NEW: Form streaks
        df['podium_streak'] = df.groupby('driver').apply(
            lambda x: (x['race_position'] <= 3).rolling(window=5, min_periods=1).sum().shift(1)
        ).reset_index(level=0, drop=True)
        
        df['dnf_streak'] = df.groupby('driver').apply(
            lambda x: (x['status'] != 'Finished').rolling(window=5, min_periods=1).sum().shift(1)
        ).reset_index(level=0, drop=True)
        
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
        
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
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
        study.optimize(objective, n_trials=15, show_progress_bar=False)  # Reduced for faster training
        
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
            
            # 3. Neural Network
            models['neural_network'] = MLPRegressor(
                hidden_layer_sizes=(100, 50, 25),
                max_iter=1000,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2
            )
            models['neural_network'].fit(X_train, y_train[target])
            
            # Store models
            if target == 'qualifying':
                self.qualifying_models = models
            else:
                self.race_models = models
            
            # Evaluate ensemble
            predictions = {}
            for name, model in models.items():
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
            quali_predictions[name] = model.predict(X_scaled)
        
        qualifying_pred = sum(weights[name] * quali_predictions[name] for name in weights.keys())
        
        # Race predictions
        race_predictions = {}
        for name, model in self.race_models.items():
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
            
            # Log results
            logger.info("Enhanced Training Results:")
            for target in ['qualifying', 'race']:
                logger.info(f"{target.title()} Ensemble - MAE: {results[target]['ensemble_mae']:.3f}, RMSE: {results[target]['ensemble_rmse']:.3f}, R²: {results[target]['ensemble_r2']:.3f}")
            
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