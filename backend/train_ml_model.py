#!/usr/bin/env python3
"""
F1 Machine Learning Model Training Script
Builds Gradient Boosting models for qualifying and race predictions with confidence scoring.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
import os
from typing import Dict, Tuple, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class F1MLModelTrainer:
    def __init__(self, data_file: str = 'f1_data.csv'):
        """Initialize the F1 ML model trainer"""
        self.data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model storage
        self.qualifying_model = None
        self.race_model = None
        self.label_encoders = {}
        self.scaler = None
        self.feature_columns = []
        
        # Track characteristics for feature engineering
        self.track_characteristics = {
            'Monaco Grand Prix': {'type': 'street', 'difficulty': 10, 'speed': 'low', 'overtaking': 'very_hard'},
            'Silverstone Grand Prix': {'type': 'high_speed', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium'},
            'Monza Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'very_high', 'overtaking': 'easy'},
            'Spa-Francorchamps Grand Prix': {'type': 'high_speed', 'difficulty': 9, 'speed': 'high', 'overtaking': 'medium'},
            'Singapore Grand Prix': {'type': 'street', 'difficulty': 9, 'speed': 'low', 'overtaking': 'hard'},
            'Suzuka Grand Prix': {'type': 'technical', 'difficulty': 9, 'speed': 'medium', 'overtaking': 'medium'},
            'Interlagos Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'medium'},
            'Austin Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'Bahrain Grand Prix': {'type': 'mixed', 'difficulty': 6, 'speed': 'medium', 'overtaking': 'easy'},
            'Saudi Arabian Grand Prix': {'type': 'street', 'difficulty': 8, 'speed': 'high', 'overtaking': 'hard'},
            'Australian Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'Japanese Grand Prix': {'type': 'technical', 'difficulty': 9, 'speed': 'medium', 'overtaking': 'medium'},
            'Chinese Grand Prix': {'type': 'mixed', 'difficulty': 6, 'speed': 'medium', 'overtaking': 'medium'},
            'Miami Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'Emilia Romagna Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'hard'},
            'Canadian Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'high', 'overtaking': 'medium'},
            'Spanish Grand Prix': {'type': 'technical', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'hard'},
            'Austrian Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'high', 'overtaking': 'easy'},
            'British Grand Prix': {'type': 'high_speed', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium'},
            'Belgian Grand Prix': {'type': 'high_speed', 'difficulty': 9, 'speed': 'very_high', 'overtaking': 'easy'},
            'Hungarian Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'low', 'overtaking': 'very_hard'},
            'Dutch Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'hard'},
            'Italian Grand Prix': {'type': 'power', 'difficulty': 6, 'speed': 'very_high', 'overtaking': 'easy'},
            'Azerbaijan Grand Prix': {'type': 'street', 'difficulty': 8, 'speed': 'high', 'overtaking': 'medium'},
            'United States Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'Mexico City Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'São Paulo Grand Prix': {'type': 'technical', 'difficulty': 8, 'speed': 'medium', 'overtaking': 'medium'},
            'Las Vegas Grand Prix': {'type': 'street', 'difficulty': 7, 'speed': 'very_high', 'overtaking': 'medium'},
            'Qatar Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'},
            'Abu Dhabi Grand Prix': {'type': 'mixed', 'difficulty': 7, 'speed': 'medium', 'overtaking': 'medium'}
        }
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """Load and prepare the F1 data with comprehensive feature engineering"""
        logger.info("Loading F1 data...")
        
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        df = pd.read_csv(self.data_file)
        logger.info(f"Loaded {len(df)} records from {len(df['season'].unique())} seasons")
        
        # Data cleaning
        df = df.dropna(subset=['qualifying_position', 'race_position'])
        df['avg_lap_time'] = df['avg_lap_time'].fillna(df['avg_lap_time'].mean())
        df['gap_to_winner'] = df['gap_to_winner'].fillna(0)
        
        # Feature engineering
        df = self._engineer_features(df)
        
        logger.info(f"Data prepared with {len(df)} records and {len(df.columns)} features")
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive features for ML model"""
        logger.info("Engineering features...")
        
        # Sort by season and race for time-series features
        df = df.sort_values(['season', 'race', 'qualifying_position'])
        
        # Track characteristics
        df['track_type'] = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get('type', 'mixed'))
        df['track_difficulty'] = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get('difficulty', 7))
        df['track_speed'] = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get('speed', 'medium'))
        df['overtaking_difficulty'] = df['race'].map(lambda x: self.track_characteristics.get(x, {}).get('overtaking', 'medium'))
        
        # Historical performance features
        df['driver_historical_quali_avg'] = df.groupby('driver')['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_historical_race_avg'] = df.groupby('driver')['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['driver_historical_points_avg'] = df.groupby('driver')['points'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        
        # Team performance features
        df['team_historical_quali_avg'] = df.groupby('team')['qualifying_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['team_historical_race_avg'] = df.groupby('team')['race_position'].transform(
            lambda x: x.expanding().mean().shift(1)
        )
        df['team_historical_points_avg'] = df.groupby('team')['points'].transform(
            lambda x: x.expanding().mean().shift(1)
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
        feature_columns = [
            'driver_historical_quali_avg', 'driver_historical_race_avg', 'driver_historical_points_avg',
            'team_historical_quali_avg', 'team_historical_race_avg', 'team_historical_points_avg',
            'driver_recent_quali_avg', 'driver_recent_race_avg',
            'driver_track_quali_avg', 'driver_track_race_avg',
            'driver_season_quali_avg', 'driver_season_race_avg',
            'quali_trend', 'race_trend'
        ]
        
        for col in feature_columns:
            if col in df.columns:
                if 'quali' in col:
                    df[col] = df[col].fillna(10.0)  # Mid-grid default
                elif 'race' in col:
                    df[col] = df[col].fillna(10.0)  # Mid-pack default
                elif 'points' in col:
                    df[col] = df[col].fillna(0.0)   # No points default
                else:
                    df[col] = df[col].fillna(0.0)   # Neutral trend default
        
        logger.info(f"Created {len([col for col in df.columns if col not in ['season', 'race', 'driver', 'team', 'qualifying_position', 'race_position', 'points', 'status']])} engineered features")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare features for training"""
        logger.info("Preparing features for model training...")
        
        # Encode categorical variables
        categorical_columns = ['driver', 'team', 'race', 'track_type', 'track_speed', 'overtaking_difficulty']
        
        for col in categorical_columns:
            if col in df.columns:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        # Select feature columns
        feature_columns = [
            'season', 'season_race_number', 'grid_position', 'avg_lap_time', 'gap_to_winner',
            'track_difficulty', 'grid_vs_quali_diff', 'weather_dry', 'weather_wet', 'dnf',
            'driver_historical_quali_avg', 'driver_historical_race_avg', 'driver_historical_points_avg',
            'team_historical_quali_avg', 'team_historical_race_avg', 'team_historical_points_avg',
            'driver_recent_quali_avg', 'driver_recent_race_avg',
            'driver_track_quali_avg', 'driver_track_race_avg',
            'driver_season_quali_avg', 'driver_season_race_avg',
            'quali_trend', 'race_trend'
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
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        logger.info(f"Prepared {len(feature_columns)} features for training")
        return X_scaled, pd.DataFrame({'qualifying': y_qualifying, 'race': y_race})
    
    def train_models(self, X: pd.DataFrame, y: pd.DataFrame) -> Dict:
        """Train XGBoost models for qualifying and race predictions"""
        logger.info("Training XGBoost models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        
        # XGBoost parameters
        xgb_params = {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse'
        }
        
        results = {}
        
        # Train qualifying model
        logger.info("Training qualifying position model...")
        self.qualifying_model = xgb.XGBRegressor(**xgb_params)
        self.qualifying_model.fit(X_train, y_train['qualifying'])
        
        # Evaluate qualifying model
        y_pred_quali = self.qualifying_model.predict(X_test)
        results['qualifying'] = {
            'mae': mean_absolute_error(y_test['qualifying'], y_pred_quali),
            'rmse': np.sqrt(mean_squared_error(y_test['qualifying'], y_pred_quali)),
            'r2': r2_score(y_test['qualifying'], y_pred_quali)
        }
        
        # Train race model
        logger.info("Training race position model...")
        self.race_model = xgb.XGBRegressor(**xgb_params)
        self.race_model.fit(X_train, y_train['race'])
        
        # Evaluate race model
        y_pred_race = self.race_model.predict(X_test)
        results['race'] = {
            'mae': mean_absolute_error(y_test['race'], y_pred_race),
            'rmse': np.sqrt(mean_squared_error(y_test['race'], y_pred_race)),
            'r2': r2_score(y_test['race'], y_pred_race)
        }
        
        # Feature importance
        results['qualifying_importance'] = dict(zip(
            self.feature_columns,
            self.qualifying_model.feature_importances_
        ))
        results['race_importance'] = dict(zip(
            self.feature_columns,
            self.race_model.feature_importances_
        ))
        
        logger.info("Model training completed")
        return results
    
    def calculate_confidence(self, X: pd.DataFrame, prediction_type: str = 'qualifying') -> np.ndarray:
        """Calculate prediction confidence scores"""
        model = self.qualifying_model if prediction_type == 'qualifying' else self.race_model
        
        if model is None:
            raise ValueError(f"Model for {prediction_type} not trained yet")
        
        # Get predictions from all trees (using iteration_range instead of ntree_limit)
        predictions = []
        for i in range(min(50, model.n_estimators)):  # Limit to first 50 trees for performance
            try:
                tree_pred = model.predict(X, iteration_range=(0, i+1))
                predictions.append(tree_pred)
            except Exception:
                # Fallback: use standard deviation of features as confidence proxy
                feature_std = np.std(X.values, axis=1)
                confidence = 1 / (1 + feature_std)
                return confidence
        
        if len(predictions) > 1:
            predictions = np.array(predictions)
            # Calculate confidence based on prediction variance
            prediction_std = np.std(predictions, axis=0)
            confidence = 1 / (1 + prediction_std)  # Higher std = lower confidence
        else:
            # Fallback confidence based on prediction magnitude
            base_pred = model.predict(X)
            # Closer to extreme positions (1 or 20) = higher confidence
            position_confidence = 1 - np.abs(base_pred - 10.5) / 9.5
            confidence = np.clip(position_confidence, 0.3, 0.9)
        
        return confidence
    
    def predict_with_confidence(self, X: pd.DataFrame) -> Dict:
        """Make predictions with confidence scores"""
        if self.qualifying_model is None or self.race_model is None:
            raise ValueError("Models not trained yet")
        
        # Scale features
        X_scaled = pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Make predictions
        qualifying_pred = self.qualifying_model.predict(X_scaled)
        race_pred = self.race_model.predict(X_scaled)
        
        # Calculate confidence
        qualifying_confidence = self.calculate_confidence(X_scaled, 'qualifying')
        race_confidence = self.calculate_confidence(X_scaled, 'race')
        
        return {
            'qualifying_position': qualifying_pred.round().astype(int),
            'race_position': race_pred.round().astype(int),
            'qualifying_confidence': qualifying_confidence,
            'race_confidence': race_confidence
        }
    
    def save_models(self):
        """Save trained models and preprocessors"""
        logger.info("Saving trained models...")
        
        # Save models
        joblib.dump(self.qualifying_model, os.path.join(self.models_dir, 'qualifying_model.pkl'))
        joblib.dump(self.race_model, os.path.join(self.models_dir, 'race_model.pkl'))
        
        # Save preprocessors
        joblib.dump(self.label_encoders, os.path.join(self.models_dir, 'label_encoders.pkl'))
        joblib.dump(self.scaler, os.path.join(self.models_dir, 'scaler.pkl'))
        
        # Save feature columns
        joblib.dump(self.feature_columns, os.path.join(self.models_dir, 'feature_columns.pkl'))
        
        logger.info("Models saved successfully")
    
    def load_models(self):
        """Load trained models and preprocessors"""
        logger.info("Loading trained models...")
        
        # Load models
        self.qualifying_model = joblib.load(os.path.join(self.models_dir, 'qualifying_model.pkl'))
        self.race_model = joblib.load(os.path.join(self.models_dir, 'race_model.pkl'))
        
        # Load preprocessors
        self.label_encoders = joblib.load(os.path.join(self.models_dir, 'label_encoders.pkl'))
        self.scaler = joblib.load(os.path.join(self.models_dir, 'scaler.pkl'))
        
        # Load feature columns
        self.feature_columns = joblib.load(os.path.join(self.models_dir, 'feature_columns.pkl'))
        
        logger.info("Models loaded successfully")
    
    def train_pipeline(self) -> Dict:
        """Complete training pipeline"""
        logger.info("Starting F1 ML model training pipeline...")
        
        try:
            # Load and prepare data
            df = self.load_and_prepare_data()
            
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Train models
            results = self.train_models(X, y)
            
            # Save models
            self.save_models()
            
            # Log results
            logger.info("Training Results:")
            logger.info(f"Qualifying Model - MAE: {results['qualifying']['mae']:.3f}, RMSE: {results['qualifying']['rmse']:.3f}, R²: {results['qualifying']['r2']:.3f}")
            logger.info(f"Race Model - MAE: {results['race']['mae']:.3f}, RMSE: {results['race']['rmse']:.3f}, R²: {results['race']['r2']:.3f}")
            
            # Top features
            logger.info("Top 10 Features for Qualifying:")
            quali_features = sorted(results['qualifying_importance'].items(), key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in quali_features:
                logger.info(f"  {feature}: {importance:.4f}")
            
            logger.info("Top 10 Features for Race:")
            race_features = sorted(results['race_importance'].items(), key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in race_features:
                logger.info(f"  {feature}: {importance:.4f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise

def main():
    """Main training function"""
    trainer = F1MLModelTrainer()
    results = trainer.train_pipeline()
    
    print("\n" + "="*60)
    print("F1 ML MODEL TRAINING COMPLETED")
    print("="*60)
    print(f"Qualifying Model Performance:")
    print(f"  MAE: {results['qualifying']['mae']:.3f} positions")
    print(f"  RMSE: {results['qualifying']['rmse']:.3f} positions")
    print(f"  R²: {results['qualifying']['r2']:.3f}")
    print(f"\nRace Model Performance:")
    print(f"  MAE: {results['race']['mae']:.3f} positions")
    print(f"  RMSE: {results['race']['rmse']:.3f} positions")
    print(f"  R²: {results['race']['r2']:.3f}")
    print("\nModels saved to ./models/ directory")
    print("="*60)

if __name__ == "__main__":
    main()