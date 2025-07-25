from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd

from services.enhanced_ensemble_service import enhanced_ensemble_service
from services.enhanced_prediction_service import EnhancedPredictionService
from services.race_prediction_service import race_prediction_service
from services.telemetry_analyzer_service import TelemetryAnalyzerService

app = FastAPI(
    title="F1 Enhanced Prediction API", 
    version="3.0.0",
    description="Enhanced F1 prediction system with data-driven car and driver ratings plus ensemble ML models"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use enhanced prediction service for individual driver predictions
enhanced_prediction_service = EnhancedPredictionService()
prediction_service = enhanced_ensemble_service  # Keep for backward compatibility
telemetry_analyzer = TelemetryAnalyzerService()

@app.on_event("startup")
async def startup_event():
    """Initialize the prediction service and load cached data on startup"""
    print("Starting F1 Driver Performance Prediction API...")
    print("Loading cached data and trained ML models...")
    
    # Check if cache directory exists
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    cache_db = os.path.join(cache_dir, 'fastf1_http_cache.sqlite')
    data_file = os.path.join(os.path.dirname(__file__), 'f1_data.csv')
    
    # Auto-download F1 data if cache is missing
    if not os.path.exists(cache_db) or not os.path.exists(data_file):
        print("Cache or data files missing - downloading F1 data...")
        print("This may take 5-10 minutes on first startup...")
        
        try:
            import subprocess
            import sys
            
            # Run the download script
            download_script = os.path.join(os.path.dirname(__file__), 'download_current_data.py')
            print(f"Running: python3 {download_script}")
            
            # Stream output in real-time
            process = subprocess.Popen([sys.executable, download_script], 
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     universal_newlines=True, cwd=os.path.dirname(__file__))
            
            # Print output line by line as it comes
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"📥 {output.strip()}")
            
            return_code = process.poll()
            if return_code == 0:
                print("✅ F1 data download completed successfully!")
                print("Cache and data files are now ready.")
            else:
                print(f"❌ Download failed with return code: {return_code}")
                print("API will start but predictions may not work correctly")
                
        except Exception as e:
            print(f"❌ Error during auto-download: {e}")
            print("API will start but predictions may not work correctly")
    
    # Check if cached data exists and load info
    if os.path.exists(data_file):
        try:
            data = pd.read_csv(data_file)
            print(f"Cached data loaded: {len(data)} records")
            print(f"Seasons: {sorted(data['season'].unique())}")
            print(f"Drivers: {len(data['driver'].unique())} unique drivers")
            print(f"Races: {len(data['race'].unique())} unique races")
        except Exception as e:
            print(f"Error reading cached data: {e}")
    else:
        print("No cached data found after download attempt")
        print("Manual intervention may be required")
    
    # Initialize the enhanced ensemble prediction service
    try:
        if hasattr(prediction_service, 'qualifying_models') and prediction_service.qualifying_models:
            print(f"Enhanced Ensemble Models Loaded:")
            print(f"  Qualifying Models: {list(prediction_service.qualifying_models.keys())}")
            print(f"  Race Models: {list(prediction_service.race_models.keys())}")
            print(f"  Features: {len(prediction_service.feature_columns)} enhanced features")
            print("Enhanced ensemble ML models loaded successfully")
        else:
            print("Using fallback prediction models")
    except Exception as e:
        print(f"Error initializing enhanced ensemble service: {e}")
        print("Using fallback prediction models")
    
    print("API ready for predictions!")

class PredictionRequest(BaseModel):
    driver: str
    track: str
    weather: str
    team: str

class PredictionResponse(BaseModel):
    predicted_qualifying_position: int
    predicted_race_position: int
    qualifying_confidence: float
    race_confidence: float

class RacePredictionRequest(BaseModel):
    race_name: str
    weather: str = "Dry"
    qualifying_results: Optional[Dict[str, int]] = None
    temperature: float = 25.0

class DriverPrediction(BaseModel):
    driver_code: str
    driver_name: str
    team: str
    number: int
    predicted_position: int
    predicted_time: float
    qualifying_position: int
    confidence: float
    gap_to_winner: str
    driver_form: Dict
    weather_impact: float

class RaceStatistics(BaseModel):
    average_confidence: float
    weather_impact: bool
    predicted_podium_teams: Dict[str, int]
    total_predictions: int
    high_confidence_predictions: int
    competitive_field: int

class RacePredictionResponse(BaseModel):
    success: bool
    race_name: str
    weather_conditions: str
    temperature: float
    predictions: List[DriverPrediction]
    statistics: RaceStatistics
    model_info: Dict

@app.post("/api/predict/driver", response_model=PredictionResponse)
async def predict_driver_performance(request: PredictionRequest):
    """
    Predict individual driver performance using enhanced data-driven ratings + ML
    """
    try:
        result = enhanced_prediction_service.predict_driver_performance(
            driver=request.driver,
            track=request.track,
            weather=request.weather,
            team=request.team
        )
        return PredictionResponse(
            predicted_qualifying_position=result["predicted_qualifying_position"],
            predicted_race_position=result["predicted_race_position"],
            qualifying_confidence=result["qualifying_confidence"],
            race_confidence=result["race_confidence"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict/race")
async def predict_race_grid(request: RacePredictionRequest):
    """
    Predict full race grid results with weather conditions and confidence scoring
    """
    try:
        result = race_prediction_service.predict_race_grid(
            race_name=request.race_name,
            weather=request.weather,
            qualifying_results=request.qualifying_results,
            temperature=request.temperature
        )
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Prediction failed'))
        
        # Convert to response format
        predictions = [
            DriverPrediction(
                driver_code=p['driver_code'],
                driver_name=p['driver_name'],
                team=p['team'],
                number=p['number'],
                predicted_position=p['predicted_position'],
                predicted_time=p['predicted_time'],
                qualifying_position=p['qualifying_position'],
                confidence=p['confidence'],
                gap_to_winner=p['gap_to_winner'],
                driver_form=p['driver_form'],
                weather_impact=p['weather_impact']
            ) for p in result['predictions']
        ]
        
        statistics = RaceStatistics(
            average_confidence=result['statistics']['average_confidence'],
            weather_impact=result['statistics']['weather_impact'],
            predicted_podium_teams=result['statistics']['predicted_podium_teams'],
            total_predictions=result['statistics']['total_predictions'],
            high_confidence_predictions=result['statistics']['high_confidence_predictions'],
            competitive_field=result['statistics']['competitive_field']
        )
        
        return RacePredictionResponse(
            success=result['success'],
            race_name=result['race_name'],
            weather_conditions=result['weather_conditions'],
            temperature=result['temperature'],
            predictions=predictions,
            statistics=statistics,
            model_info=result['model_info']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Race prediction failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Telemetry Analysis Endpoints

class TelemetryAnalysisRequest(BaseModel):
    year: int
    race: str
    session: str = "R"  # R for race, Q for qualifying, etc.
    drivers: Optional[List[str]] = None

class SpeedTraceRequest(BaseModel):
    year: int
    race: str
    driver: str
    session: str = "R"
    lap_number: Optional[int] = None

class DriverComparisonRequest(BaseModel):
    year: int
    race: str
    driver1: str
    driver2: str
    session: str = "R"
    lap_type: str = "fastest"

class TrackMapRequest(BaseModel):
    year: int
    race: str
    driver: str
    session: str = "R"
    lap_number: Optional[int] = None

class WeatherContextRequest(BaseModel):
    race: str
    session: str = "R"

@app.post("/api/telemetry/analyze")
async def analyze_session_telemetry(request: TelemetryAnalysisRequest):
    """
    Comprehensive telemetry analysis for a race session
    Returns performance metrics, car setup analysis, track analysis, 
    driver comparisons, and strategic insights
    """
    try:
        result = await telemetry_analyzer.analyze_session_telemetry(
            year=request.year,
            race=request.race,
            session=request.session,
            drivers=request.drivers
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry analysis failed: {str(e)}")

@app.post("/api/telemetry/speed-trace")
async def get_speed_trace(request: SpeedTraceRequest):
    """
    Get detailed speed trace with throttle/brake overlay for visualization
    This shows exactly where drivers gain/lose time and how they achieve it
    """
    try:
        result = await telemetry_analyzer.get_speed_trace_with_inputs(
            year=request.year,
            race=request.race,
            driver=request.driver,
            session=request.session,
            lap_number=request.lap_number
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speed trace analysis failed: {str(e)}")

@app.post("/api/telemetry/driver-comparison")
async def get_driver_comparison(request: DriverComparisonRequest):
    """
    Get telemetry comparison between two drivers (e.g., VER vs NOR at Spa)
    Returns comprehensive telemetry data for speed, throttle, brake, gear comparison
    """
    try:
        result = await telemetry_analyzer.get_driver_comparison_telemetry(
            year=request.year,
            race=request.race,
            driver1=request.driver1,
            driver2=request.driver2,
            session=request.session,
            lap_type=request.lap_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Driver comparison failed: {str(e)}")

@app.post("/api/telemetry/track-map")
async def get_track_map(request: TrackMapRequest):
    """
    Get track map data with driver position coordinates for visualization
    Returns track layout, driver positions, racing line, and sector information
    """
    try:
        result = await telemetry_analyzer.get_track_map_data(
            year=request.year,
            race=request.race,
            driver=request.driver,
            session=request.session,
            lap_number=request.lap_number
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Track map data failed: {str(e)}")

@app.post("/api/telemetry/weather-context")
async def get_weather_context(request: WeatherContextRequest):
    """
    Get comprehensive weather context for a racing session
    Returns temperature, humidity, wind, rainfall, driver ratings, and tire strategy
    """
    try:
        result = telemetry_analyzer.get_weather_context(
            race_name=request.race,
            session_type=request.session
        )
        
        # Convert WeatherContext dataclass to dict for JSON response
        return {
            'success': True,
            'race': request.race,
            'session': request.session,
            'weather': {
                'condition': result.condition,
                'temperature': result.temperature,
                'humidity': result.humidity,
                'wind_speed': result.wind_speed,
                'track_temperature': result.track_temperature,
                'rainfall': result.rainfall
            },
            'impact_analysis': result.weather_impact,
            'tire_strategy': {
                'influence': result.tire_strategy_influence,
                'recommendation': result.weather_impact.get('tire_strategy', 'Unknown')
            },
            'driver_ratings': result.driver_weather_rating,
            'insights': {
                'grip_level': result.weather_impact.get('grip_level', 'Unknown'),
                'performance_factors': [
                    result.weather_impact.get('temperature_effect', 'Unknown'),
                    result.weather_impact.get('wind_impact', 'Unknown')
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather context analysis failed: {str(e)}")

@app.get("/api/telemetry/available-sessions/{year}")
async def get_available_sessions(year: int):
    """
    Get list of available race sessions for telemetry analysis (2024-2025 only)
    """
    try:
        # Only allow 2024 and 2025 seasons
        if year not in [2024, 2025]:
            return {
                'year': year,
                'available_races': [],
                'total_races': 0,
                'error': 'Only 2024 and 2025 seasons are supported'
            }
        
        # Get races from existing cache directory
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache', str(year))
        available_races = []
        
        if os.path.exists(cache_dir):
            for race_dir in os.listdir(cache_dir):
                if os.path.isdir(os.path.join(cache_dir, race_dir)):
                    # Extract race name from directory name (format: YYYY-MM-DD_Race_Name)
                    parts = race_dir.split('_', 1)
                    if len(parts) > 1:
                        race_name = parts[1].replace('_', ' ')
                        # Check if race has telemetry data
                        race_path = os.path.join(cache_dir, race_dir)
                        sessions = [d for d in os.listdir(race_path) if os.path.isdir(os.path.join(race_path, d))]
                        
                        if sessions:  # Only include races with session data
                            available_races.append({
                                'race_name': race_name,
                                'location': race_name.split(' Grand Prix')[0] if 'Grand Prix' in race_name else race_name,
                                'date': parts[0],
                                'sessions': sessions,
                                'directory': race_dir
                            })
        
        # Sort by date
        available_races.sort(key=lambda x: x['date'])
        
        return {
            'year': year,
            'available_races': available_races,
            'total_races': len(available_races)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available sessions: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
