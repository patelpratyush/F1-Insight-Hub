#!/usr/bin/env python3
"""
FastF1 Integration Service - Lightweight
Only retains weather analysis which requires actual FastF1 session data.
All other metadata (standings, results, schedules) is served by cache_manager.py.
"""

import fastf1
import pandas as pd
import logging
from typing import Dict, List
from datetime import datetime
import warnings
import os

from services.cache_manager import cache_manager

warnings.filterwarnings('ignore')

cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

logger = logging.getLogger(__name__)


class FastF1Service:
    """Service for weather-based F1 analysis using FastF1 session data."""

    def get_driver_weather_performance(self, year: int = 2025) -> List[Dict]:
        """Analyze driver performance in different weather conditions using FastF1 session data."""
        try:
            logger.info(f"Analyzing weather performance for {year} from FastF1 session data...")

            # Use cache_manager for the schedule of completed races
            completed = cache_manager.get_completed_races(year)
            if not completed:
                logger.warning(f"No completed races in cache for {year}, using FastF1 schedule")
                try:
                    schedule = fastf1.get_event_schedule(year)
                    current_date = pd.Timestamp.now(tz='UTC')
                    schedule['Session5Date'] = pd.to_datetime(schedule['Session5Date'], utc=True)
                    completed_df = schedule[schedule['Session5Date'] < current_date]
                    race_names = completed_df['EventName'].tolist()
                except Exception:
                    return []
            else:
                race_names = [r.get("race_name", "") for r in completed]

            weather_data: Dict[str, Dict[str, List]] = {}

            for race_name in race_names:
                try:
                    session = fastf1.get_session(year, race_name, 'R')
                    session.load(laps=False, telemetry=False, weather=True, messages=False)

                    if hasattr(session, 'weather_data') and not session.weather_data.empty:
                        weather_info = session.weather_data.iloc[0]
                        temp = weather_info.get('AirTemp', 20)
                        humidity = weather_info.get('Humidity', 50)
                        rainfall = weather_info.get('Rainfall', False)

                        if rainfall or humidity > 85:
                            condition = 'Wet'
                        elif temp > 30:
                            condition = 'Hot'
                        elif humidity > 70:
                            condition = 'Humid'
                        else:
                            condition = 'Dry'

                        results = session.results
                        if not results.empty:
                            for _, driver_result in results.iterrows():
                                driver_code = driver_result.get('Abbreviation', '')
                                position = driver_result.get('Position', 0)
                                if not driver_code or pd.isna(position):
                                    continue

                                if condition not in weather_data:
                                    weather_data[condition] = {}
                                if driver_code not in weather_data[condition]:
                                    weather_data[condition][driver_code] = []
                                weather_data[condition][driver_code].append(float(position))

                except Exception as race_error:
                    logger.warning(f"Failed to analyze weather for {race_name}: {race_error}")
                    continue

            # Calculate averages
            weather_analysis = []
            for condition, drivers in weather_data.items():
                avg_positions = {}
                race_count = 0
                for driver_code, positions in drivers.items():
                    if positions:
                        avg_positions[driver_code] = round(sum(positions) / len(positions), 1)
                        race_count = max(race_count, len(positions))

                if avg_positions:
                    weather_analysis.append({
                        'condition': condition,
                        'races': race_count,
                        'avgPosition': avg_positions,
                    })

            if weather_analysis:
                logger.info(f"Generated weather analysis for {len(weather_analysis)} conditions")
                return weather_analysis

            logger.warning(f"No weather analysis data generated for {year}")
            return []

        except Exception as e:
            logger.error(f"Error analyzing weather performance: {e}")
            return []


# Global service instance
fastf1_service = FastF1Service()
