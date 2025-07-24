#!/usr/bin/env python3
"""
Race Prediction Service
Provides full grid race predictions using enhanced ensemble models with weather integration.
"""

import pandas as pd
import numpy as np
import os
import logging
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
        
        # Driver roster for 2025 season
        self.drivers_2025 = {
            'VER': {'name': 'Max Verstappen', 'team': 'Red Bull Racing Honda RBPT', 'number': 1},
            'NOR': {'name': 'Lando Norris', 'team': 'McLaren Mercedes', 'number': 4},
            'BOR': {'name': 'Gabriel Bortoleto', 'team': 'Kick Sauber F1 Team', 'number': 5},
            'HAD': {'name': 'Isack Hadjar', 'team': 'Kick Sauber F1 Team', 'number': 6},
            'GAS': {'name': 'Pierre Gasly', 'team': 'BWT Alpine F1 Team', 'number': 10},
            'ANT': {'name': 'Kimi Antonelli', 'team': 'Mercedes', 'number': 12},
            'ALO': {'name': 'Fernando Alonso', 'team': 'Aston Martin Aramco Mercedes', 'number': 14},
            'LEC': {'name': 'Charles Leclerc', 'team': 'Scuderia Ferrari', 'number': 16},
            'STR': {'name': 'Lance Stroll', 'team': 'Aston Martin Aramco Mercedes', 'number': 18},
            'TSU': {'name': 'Yuki Tsunoda', 'team': 'Visa Cash App RB F1 Team', 'number': 22},
            'ALB': {'name': 'Alexander Albon', 'team': 'Williams Mercedes', 'number': 23},
            'HUL': {'name': 'Nico Hulkenberg', 'team': 'MoneyGram Haas F1 Team', 'number': 27},
            'LAW': {'name': 'Liam Lawson', 'team': 'Visa Cash App RB F1 Team', 'number': 30},
            'OCO': {'name': 'Esteban Ocon', 'team': 'BWT Alpine F1 Team', 'number': 31},
            'COL': {'name': 'Franco Colapinto', 'team': 'Williams Mercedes', 'number': 43},
            'HAM': {'name': 'Lewis Hamilton', 'team': 'Scuderia Ferrari', 'number': 44},
            'SAI': {'name': 'Carlos Sainz', 'team': 'Williams Mercedes', 'number': 55},
            'RUS': {'name': 'George Russell', 'team': 'Mercedes', 'number': 63},
            'PIA': {'name': 'Oscar Piastri', 'team': 'McLaren Mercedes', 'number': 81},
            'BEA': {'name': 'Oliver Bearman', 'team': 'MoneyGram Haas F1 Team', 'number': 87}
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
                logger.warning("Historical data file not found")
                self.historical_data = pd.DataFrame()
                self._set_fallback_ratings()
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            self.historical_data = pd.DataFrame()
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
        """Set basic fallback car ratings"""
        self.car_performance = {
            'Red Bull Racing Honda RBPT': {'dry_pace': 0.90, 'wet_pace': 0.88, 'strategy': 0.85, 'reliability': 0.82},
            'McLaren Mercedes': {'dry_pace': 0.88, 'wet_pace': 0.86, 'strategy': 0.83, 'reliability': 0.80},
            'Scuderia Ferrari': {'dry_pace': 0.85, 'wet_pace': 0.82, 'strategy': 0.75, 'reliability': 0.78},
            'Mercedes': {'dry_pace': 0.82, 'wet_pace': 0.85, 'strategy': 0.80, 'reliability': 0.83},
        }
        logger.warning("Using fallback car performance ratings")
    
    def _set_fallback_driver_ratings(self):
        """Set basic fallback driver ratings"""
        self.driver_performance = {
            'VER': {'overall_skill': 0.95, 'wet_skill': 0.92, 'race_craft': 0.90, 'strategy_execution': 0.88},
            'HAM': {'overall_skill': 0.90, 'wet_skill': 0.95, 'race_craft': 0.92, 'strategy_execution': 0.85},
            'LEC': {'overall_skill': 0.88, 'wet_skill': 0.85, 'race_craft': 0.86, 'strategy_execution': 0.82},
            'NOR': {'overall_skill': 0.87, 'wet_skill': 0.83, 'race_craft': 0.85, 'strategy_execution': 0.84},
        }
        logger.warning("Using fallback driver performance ratings")
    
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
            
            # Use data-driven car + driver performance for base prediction
            car_stats = self.car_performance.get(team, {})
            
            # Map driver code to full name for lookup
            driver_full_name = self.drivers_2025.get(driver, {}).get('name', driver)
            driver_stats = self.driver_performance.get(driver_full_name, {})
            
            # Get car pace rating (most important factor - 70% weight)
            car_pace = car_stats.get('dry_pace', 0.75) if weather == 'Dry' else car_stats.get('wet_pace', 0.75)
            car_reliability = car_stats.get('reliability', 0.8)
            
            # Get driver skill rating (30% weight)
            driver_skill = driver_stats.get('overall_skill', 0.7) if weather == 'Dry' else driver_stats.get('wet_skill', 0.7)
            driver_race_craft = driver_stats.get('race_craft', 0.7)
            
            # Combined performance score (car dominates, but driver matters)
            combined_performance = (car_pace * 0.7) + (driver_skill * 0.3)
            
            # Calculate expected position based on performance vs field average (0.75)
            performance_advantage = combined_performance - 0.75
            base_position_change = performance_advantage * -12  # Scale to position changes
            
            # Add race craft factor (driver's ability to gain positions during race)
            race_craft_bonus = (driver_race_craft - 0.7) * 2  # Up to ±0.6 positions
            
            # Add some randomness but less for better performers
            variance_factor = 1.0 - (combined_performance - 0.5)  # Better performers = less variance
            random_factor = np.random.normal(0, variance_factor * 2)
            
            # Calculate final position change
            total_position_change = base_position_change + race_craft_bonus + random_factor
            
            # Apply reliability factor (chance of DNF/issues)
            if np.random.random() > car_reliability:
                # Reliability issue - worse position
                total_position_change += np.random.uniform(3, 8)
            
            predicted_pos = max(1, min(20, quali_pos + total_position_change))
            
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