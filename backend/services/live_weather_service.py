#!/usr/bin/env python3
"""
Live Weather Service for F1 Insight Hub
Provides real-time weather data for F1 circuits using OpenWeatherMap API
"""

import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import os
from enum import Enum

logger = logging.getLogger(__name__)

class WeatherCondition(Enum):
    CLEAR = "clear"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    MIXED = "mixed"

@dataclass
class WeatherData:
    """Weather data for F1 circuit"""
    circuit_name: str
    location: str
    country: str
    temperature: float  # Celsius
    humidity: int  # Percentage
    wind_speed: float  # km/h
    wind_direction: int  # Degrees
    pressure: float  # hPa
    visibility: float  # km
    condition: WeatherCondition
    description: str
    precipitation_chance: int  # Percentage
    precipitation_intensity: float  # mm/h
    track_temperature: float  # Estimated track temp
    grip_level: str  # "Excellent", "Good", "Variable", "Poor"
    timestamp: datetime
    forecast_hours: List[Dict]  # Next 24 hours forecast

@dataclass
class RaceWeekendWeather:
    """Complete race weekend weather forecast"""
    circuit_name: str
    race_date: datetime
    current_weather: WeatherData
    practice_forecast: List[WeatherData]  # FP1, FP2, FP3
    qualifying_forecast: WeatherData
    race_forecast: WeatherData
    weekend_summary: Dict

class LiveWeatherService:
    """Live weather service for F1 circuits"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not found. Using fallback weather data.")
            self.use_api = False
        else:
            self.use_api = True
            
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.circuit_locations = self._initialize_circuit_locations()
        self.weather_cache = {}  # Cache weather data for 10 minutes
        self.cache_duration = 600  # 10 minutes in seconds
        
    def _initialize_circuit_locations(self) -> Dict[str, Dict]:
        """Initialize F1 circuit coordinates and details"""
        return {
            "Bahrain Grand Prix": {
                "lat": 26.0325, "lon": 50.5106,
                "location": "Sakhir", "country": "Bahrain",
                "timezone": "Asia/Bahrain"
            },
            "Saudi Arabian Grand Prix": {
                "lat": 21.6319, "lon": 39.1044,
                "location": "Jeddah", "country": "Saudi Arabia", 
                "timezone": "Asia/Riyadh"
            },
            "Australian Grand Prix": {
                "lat": -37.8497, "lon": 144.968,
                "location": "Melbourne", "country": "Australia",
                "timezone": "Australia/Melbourne"
            },
            "Japanese Grand Prix": {
                "lat": 34.8431, "lon": 136.5407,
                "location": "Suzuka", "country": "Japan",
                "timezone": "Asia/Tokyo"
            },
            "Chinese Grand Prix": {
                "lat": 31.3389, "lon": 121.2197,
                "location": "Shanghai", "country": "China",
                "timezone": "Asia/Shanghai"
            },
            "Miami Grand Prix": {
                "lat": 25.9581, "lon": -80.2389,
                "location": "Miami", "country": "USA",
                "timezone": "America/New_York"
            },
            "Emilia Romagna Grand Prix": {
                "lat": 44.3439, "lon": 11.7167,
                "location": "Imola", "country": "Italy",
                "timezone": "Europe/Rome"
            },
            "Monaco Grand Prix": {
                "lat": 43.7347, "lon": 7.4206,
                "location": "Monte Carlo", "country": "Monaco",
                "timezone": "Europe/Monaco"
            },
            "Spanish Grand Prix": {
                "lat": 41.57, "lon": 2.2611,
                "location": "Barcelona", "country": "Spain",
                "timezone": "Europe/Madrid"
            },
            "Canadian Grand Prix": {
                "lat": 45.5, "lon": -73.5228,
                "location": "Montreal", "country": "Canada",
                "timezone": "America/Toronto"
            },
            "Austrian Grand Prix": {
                "lat": 47.2197, "lon": 14.7647,
                "location": "Spielberg", "country": "Austria",
                "timezone": "Europe/Vienna"
            },
            "British Grand Prix": {
                "lat": 52.0786, "lon": -1.0169,
                "location": "Silverstone", "country": "United Kingdom",
                "timezone": "Europe/London"
            },
            "Hungarian Grand Prix": {
                "lat": 47.5789, "lon": 19.2486,
                "location": "Budapest", "country": "Hungary",
                "timezone": "Europe/Budapest"
            },
            "Belgian Grand Prix": {
                "lat": 50.4372, "lon": 5.9714,
                "location": "Spa-Francorchamps", "country": "Belgium",
                "timezone": "Europe/Brussels"
            },
            "Dutch Grand Prix": {
                "lat": 52.3886, "lon": 4.5419,
                "location": "Zandvoort", "country": "Netherlands",
                "timezone": "Europe/Amsterdam"
            },
            "Italian Grand Prix": {
                "lat": 45.6156, "lon": 9.2811,
                "location": "Monza", "country": "Italy",
                "timezone": "Europe/Rome"
            },
            "Azerbaijan Grand Prix": {
                "lat": 40.3725, "lon": 49.8533,
                "location": "Baku", "country": "Azerbaijan",
                "timezone": "Asia/Baku"
            },
            "Singapore Grand Prix": {
                "lat": 1.2914, "lon": 103.864,
                "location": "Singapore", "country": "Singapore",
                "timezone": "Asia/Singapore"
            },
            "United States Grand Prix": {
                "lat": 30.1328, "lon": -97.6411,
                "location": "Austin", "country": "USA",
                "timezone": "America/Chicago"
            },
            "Mexico City Grand Prix": {
                "lat": 19.4042, "lon": -99.0907,
                "location": "Mexico City", "country": "Mexico",
                "timezone": "America/Mexico_City"
            },
            "São Paulo Grand Prix": {
                "lat": -23.7036, "lon": -46.6997,
                "location": "São Paulo", "country": "Brazil",
                "timezone": "America/Sao_Paulo"
            },
            "Las Vegas Grand Prix": {
                "lat": 36.1147, "lon": -115.1728,
                "location": "Las Vegas", "country": "USA",
                "timezone": "America/Los_Angeles"
            },
            "Qatar Grand Prix": {
                "lat": 25.4919, "lon": 51.4542,
                "location": "Lusail", "country": "Qatar",
                "timezone": "Asia/Qatar"
            },
            "Abu Dhabi Grand Prix": {
                "lat": 24.4672, "lon": 54.6031,
                "location": "Abu Dhabi", "country": "UAE",
                "timezone": "Asia/Dubai"
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached weather data is still valid"""
        if cache_key not in self.weather_cache:
            return False
        
        cached_time = self.weather_cache[cache_key].get('timestamp', datetime.min)
        return (datetime.now() - cached_time).total_seconds() < self.cache_duration
    
    def _determine_f1_weather_condition(self, weather_code: int, rain_intensity: float) -> WeatherCondition:
        """Convert OpenWeather condition codes to F1-specific conditions"""
        # OpenWeatherMap condition codes: https://openweathermap.org/weather-conditions
        
        if weather_code in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
            # Thunderstorms
            return WeatherCondition.HEAVY_RAIN
        elif weather_code in [300, 301, 302, 310, 311, 312, 313, 314, 321]:
            # Drizzle
            return WeatherCondition.LIGHT_RAIN
        elif weather_code in [500, 501]:
            # Light rain
            return WeatherCondition.LIGHT_RAIN
        elif weather_code in [502, 503, 504, 511, 520, 521, 522, 531]:
            # Heavy rain
            return WeatherCondition.HEAVY_RAIN
        elif weather_code in [600, 601, 602, 611, 612, 613, 615, 616, 620, 621, 622]:
            # Snow (treat as heavy rain for F1 purposes)
            return WeatherCondition.HEAVY_RAIN
        elif weather_code in [701, 711, 721, 731, 741, 751, 761, 762, 771, 781]:
            # Atmospheric conditions (fog, dust, etc.)
            return WeatherCondition.OVERCAST
        elif weather_code == 800:
            # Clear sky
            return WeatherCondition.CLEAR
        elif weather_code in [801, 802]:
            # Few/scattered clouds
            return WeatherCondition.CLEAR
        elif weather_code in [803, 804]:
            # Broken/overcast clouds
            return WeatherCondition.OVERCAST
        else:
            return WeatherCondition.OVERCAST
    
    def _calculate_track_temperature(self, air_temp: float, humidity: int, wind_speed: float, condition: WeatherCondition) -> float:
        """Estimate track temperature based on air temperature and conditions"""
        # Track temperature is typically higher than air temperature
        base_multiplier = 1.3  # Track typically 30% warmer than air
        
        # Adjust based on conditions
        if condition == WeatherCondition.CLEAR:
            multiplier = 1.4  # Sunny conditions heat the track more
        elif condition == WeatherCondition.OVERCAST:
            multiplier = 1.2  # Clouds reduce heating
        elif condition in [WeatherCondition.LIGHT_RAIN, WeatherCondition.HEAVY_RAIN]:
            multiplier = 0.95  # Rain cools the track
        else:
            multiplier = base_multiplier
        
        # Humidity and wind effects
        humidity_factor = 1.0 - (humidity - 50) * 0.002  # Higher humidity = lower track temp
        wind_factor = 1.0 - (wind_speed * 0.01)  # Wind cools the track
        
        track_temp = air_temp * multiplier * humidity_factor * wind_factor
        return round(track_temp, 1)
    
    def _determine_grip_level(self, condition: WeatherCondition, temperature: float, humidity: int) -> str:
        """Determine track grip level based on weather conditions"""
        if condition == WeatherCondition.CLEAR and 20 <= temperature <= 30 and humidity < 70:
            return "Excellent"
        elif condition == WeatherCondition.CLEAR and humidity < 80:
            return "Good"
        elif condition == WeatherCondition.OVERCAST:
            return "Good"
        elif condition == WeatherCondition.LIGHT_RAIN:
            return "Variable"
        elif condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.MIXED]:
            return "Poor"
        else:
            return "Variable"
    
    async def get_current_weather(self, circuit_name: str) -> Optional[WeatherData]:
        """Get current weather for a specific F1 circuit"""
        if not self.use_api:
            return self._get_fallback_weather(circuit_name)
        
        cache_key = f"current_{circuit_name}"
        if self._is_cache_valid(cache_key):
            logger.debug(f"Using cached weather for {circuit_name}")
            return self.weather_cache[cache_key]['data']
        
        circuit_info = self.circuit_locations.get(circuit_name)
        if not circuit_info:
            logger.error(f"Circuit location not found: {circuit_name}")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Current weather
                current_url = f"{self.base_url}/weather"
                params = {
                    'lat': circuit_info['lat'],
                    'lon': circuit_info['lon'],
                    'appid': self.api_key,
                    'units': 'metric'
                }
                
                async with session.get(current_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Weather API error: {response.status}")
                        return self._get_fallback_weather(circuit_name)
                    
                    data = await response.json()
                    
                    # Extract weather data
                    main = data['main']
                    weather = data['weather'][0]
                    wind = data.get('wind', {})
                    
                    condition = self._determine_f1_weather_condition(weather['id'], 0)
                    track_temp = self._calculate_track_temperature(
                        main['temp'], main['humidity'], wind.get('speed', 0) * 3.6, condition
                    )
                    grip_level = self._determine_grip_level(condition, main['temp'], main['humidity'])
                    
                    weather_data = WeatherData(
                        circuit_name=circuit_name,
                        location=circuit_info['location'],
                        country=circuit_info['country'],
                        temperature=main['temp'],
                        humidity=main['humidity'],
                        wind_speed=wind.get('speed', 0) * 3.6,  # Convert m/s to km/h
                        wind_direction=wind.get('deg', 0),
                        pressure=main['pressure'],
                        visibility=data.get('visibility', 10000) / 1000,  # Convert m to km
                        condition=condition,
                        description=weather['description'],
                        precipitation_chance=0,  # Current weather doesn't include forecast
                        precipitation_intensity=0.0,
                        track_temperature=track_temp,
                        grip_level=grip_level,
                        timestamp=datetime.now(),
                        forecast_hours=[]
                    )
                    
                    # Cache the result
                    self.weather_cache[cache_key] = {
                        'data': weather_data,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"Retrieved current weather for {circuit_name}: {condition.value}, {main['temp']}°C")
                    return weather_data
                    
        except Exception as e:
            logger.error(f"Error fetching weather for {circuit_name}: {e}")
            return self._get_fallback_weather(circuit_name)
    
    async def get_race_weekend_forecast(self, circuit_name: str, race_date: datetime) -> Optional[RaceWeekendWeather]:
        """Get complete race weekend weather forecast"""
        if not self.use_api:
            return self._get_fallback_weekend_weather(circuit_name, race_date)
        
        cache_key = f"weekend_{circuit_name}_{race_date.strftime('%Y-%m-%d')}"
        if self._is_cache_valid(cache_key):
            return self.weather_cache[cache_key]['data']
        
        circuit_info = self.circuit_locations.get(circuit_name)
        if not circuit_info:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # 5-day forecast (includes hourly data)
                forecast_url = f"{self.base_url}/forecast"
                params = {
                    'lat': circuit_info['lat'],
                    'lon': circuit_info['lon'],
                    'appid': self.api_key,
                    'units': 'metric'
                }
                
                async with session.get(forecast_url, params=params) as response:
                    if response.status != 200:
                        return self._get_fallback_weekend_weather(circuit_name, race_date)
                    
                    data = await response.json()
                    
                    # Get current weather
                    current_weather = await self.get_current_weather(circuit_name)
                    
                    # Process forecast data for race weekend
                    weekend_weather = self._process_race_weekend_forecast(
                        circuit_name, race_date, data, current_weather, circuit_info
                    )
                    
                    # Cache the result
                    self.weather_cache[cache_key] = {
                        'data': weekend_weather,
                        'timestamp': datetime.now()
                    }
                    
                    return weekend_weather
                    
        except Exception as e:
            logger.error(f"Error fetching weekend forecast for {circuit_name}: {e}")
            return self._get_fallback_weekend_weather(circuit_name, race_date)
    
    def _process_race_weekend_forecast(self, circuit_name: str, race_date: datetime, 
                                     forecast_data: Dict, current_weather: WeatherData, 
                                     circuit_info: Dict) -> RaceWeekendWeather:
        """Process 5-day forecast data into race weekend format"""
        
        # Typical F1 weekend schedule (adjust times based on timezone)
        friday_practice = race_date - timedelta(days=2)
        saturday_sessions = race_date - timedelta(days=1)
        race_day = race_date
        
        practice_forecasts = []
        qualifying_forecast = None
        race_forecast = None
        
        # Process forecast list to find relevant sessions
        for forecast in forecast_data['list']:
            forecast_time = datetime.fromtimestamp(forecast['dt'])
            
            # Check if this forecast matches our race weekend sessions
            if forecast_time.date() == friday_practice.date():
                # Practice sessions (FP1, FP2)
                weather_data = self._convert_forecast_to_weather_data(
                    forecast, circuit_name, circuit_info
                )
                practice_forecasts.append(weather_data)
            
            elif forecast_time.date() == saturday_sessions.date():
                # Saturday practice and qualifying
                weather_data = self._convert_forecast_to_weather_data(
                    forecast, circuit_name, circuit_info
                )
                if forecast_time.hour >= 14:  # Qualifying typically in afternoon
                    qualifying_forecast = weather_data
                else:
                    practice_forecasts.append(weather_data)
            
            elif forecast_time.date() == race_day.date():
                # Race day
                weather_data = self._convert_forecast_to_weather_data(
                    forecast, circuit_name, circuit_info
                )
                if forecast_time.hour >= 13:  # Race typically starts around 15:00 local
                    race_forecast = weather_data
                    break
        
        # Generate weekend summary
        weekend_summary = self._generate_weekend_summary(
            practice_forecasts, qualifying_forecast, race_forecast
        )
        
        return RaceWeekendWeather(
            circuit_name=circuit_name,
            race_date=race_date,
            current_weather=current_weather,
            practice_forecast=practice_forecasts[:3],  # Limit to 3 practice sessions
            qualifying_forecast=qualifying_forecast or current_weather,
            race_forecast=race_forecast or current_weather,
            weekend_summary=weekend_summary
        )
    
    def _convert_forecast_to_weather_data(self, forecast: Dict, circuit_name: str, circuit_info: Dict) -> WeatherData:
        """Convert OpenWeather forecast item to WeatherData"""
        main = forecast['main']
        weather = forecast['weather'][0]
        wind = forecast.get('wind', {})
        rain = forecast.get('rain', {})
        
        condition = self._determine_f1_weather_condition(weather['id'], rain.get('3h', 0))
        track_temp = self._calculate_track_temperature(
            main['temp'], main['humidity'], wind.get('speed', 0) * 3.6, condition
        )
        grip_level = self._determine_grip_level(condition, main['temp'], main['humidity'])
        
        return WeatherData(
            circuit_name=circuit_name,
            location=circuit_info['location'],
            country=circuit_info['country'],
            temperature=main['temp'],
            humidity=main['humidity'],
            wind_speed=wind.get('speed', 0) * 3.6,
            wind_direction=wind.get('deg', 0),
            pressure=main['pressure'],
            visibility=10.0,  # Forecast doesn't include visibility
            condition=condition,
            description=weather['description'],
            precipitation_chance=int(forecast.get('pop', 0) * 100),
            precipitation_intensity=rain.get('3h', 0) / 3,  # Convert 3h to hourly
            track_temperature=track_temp,
            grip_level=grip_level,
            timestamp=datetime.fromtimestamp(forecast['dt']),
            forecast_hours=[]
        )
    
    def _generate_weekend_summary(self, practice: List[WeatherData], qualifying: WeatherData, race: WeatherData) -> Dict:
        """Generate race weekend weather summary"""
        all_sessions = practice + ([qualifying] if qualifying else []) + ([race] if race else [])
        
        if not all_sessions:
            return {"summary": "No weather data available"}
        
        # Analyze conditions across the weekend
        conditions = [session.condition for session in all_sessions]
        temps = [session.temperature for session in all_sessions]
        rain_sessions = len([c for c in conditions if c in [WeatherCondition.LIGHT_RAIN, WeatherCondition.HEAVY_RAIN]])
        
        return {
            "weekend_trend": "Variable" if len(set(conditions)) > 2 else "Stable",
            "rain_probability": min(100, rain_sessions * 25),
            "temperature_range": f"{min(temps):.1f}°C - {max(temps):.1f}°C",
            "dominant_condition": max(set(conditions), key=conditions.count).value,
            "grip_assessment": race.grip_level if race else "Unknown",
            "strategy_impact": "High" if rain_sessions > 0 else "Medium",
            "tire_recommendation": self._recommend_tires(conditions)
        }
    
    def _recommend_tires(self, conditions: List[WeatherCondition]) -> str:
        """Recommend tire strategy based on weekend conditions"""
        rain_count = len([c for c in conditions if c in [WeatherCondition.LIGHT_RAIN, WeatherCondition.HEAVY_RAIN]])
        
        if rain_count > len(conditions) / 2:
            return "Wet weather compounds priority"
        elif rain_count > 0:
            return "Mixed strategy - prepare for changing conditions"
        else:
            return "Standard dry compounds"
    
    def _get_fallback_weather(self, circuit_name: str) -> WeatherData:
        """Generate fallback weather data when API is unavailable"""
        circuit_info = self.circuit_locations.get(circuit_name, {
            "location": "Unknown", "country": "Unknown"
        })
        
        # Use typical weather patterns for different regions
        temp = 25.0  # Default temperature
        condition = WeatherCondition.CLEAR
        
        if "Middle East" in circuit_info.get('region', '') or circuit_name in ["Bahrain Grand Prix", "Abu Dhabi Grand Prix", "Qatar Grand Prix"]:
            temp = 32.0
            condition = WeatherCondition.CLEAR
        elif "Europe" in circuit_info.get('region', '') or circuit_name in ["British Grand Prix", "Belgian Grand Prix"]:
            temp = 18.0
            condition = WeatherCondition.OVERCAST
        
        return WeatherData(
            circuit_name=circuit_name,
            location=circuit_info.get('location', 'Unknown'),
            country=circuit_info.get('country', 'Unknown'),
            temperature=temp,
            humidity=60,
            wind_speed=10.0,
            wind_direction=180,
            pressure=1013.25,
            visibility=10.0,
            condition=condition,
            description="Fallback weather data",
            precipitation_chance=10,
            precipitation_intensity=0.0,
            track_temperature=temp * 1.3,
            grip_level="Good",
            timestamp=datetime.now(),
            forecast_hours=[]
        )
    
    def _get_fallback_weekend_weather(self, circuit_name: str, race_date: datetime) -> RaceWeekendWeather:
        """Generate fallback weekend weather when API is unavailable"""
        current = self._get_fallback_weather(circuit_name)
        
        return RaceWeekendWeather(
            circuit_name=circuit_name,
            race_date=race_date,
            current_weather=current,
            practice_forecast=[current, current, current],
            qualifying_forecast=current,
            race_forecast=current,
            weekend_summary={
                "summary": "Fallback weather data - API unavailable",
                "weekend_trend": "Stable",
                "rain_probability": 10,
                "temperature_range": f"{current.temperature}°C",
                "strategy_impact": "Low"
            }
        )

# Global service instance (lazy-loaded)
live_weather_service = None

def get_live_weather_service():
    """Get or create the live weather service instance"""
    global live_weather_service
    if live_weather_service is None:
        live_weather_service = LiveWeatherService()
    return live_weather_service