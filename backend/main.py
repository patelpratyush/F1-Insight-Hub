from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd

from services.enhanced_ensemble_service import enhanced_ensemble_service

app = FastAPI(
    title="F1 Driver Performance Prediction API", 
    version="2.0.0",
    description="Gradient Boosting Machine Learning model that predicts race results based on past performance, qualifying times, and other structured F1 data"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prediction_service = enhanced_ensemble_service

@app.on_event("startup")
async def startup_event():
    """Initialize the prediction service and load cached data on startup"""
    print("Starting F1 Driver Performance Prediction API...")
    print("Loading cached data and trained ML models...")
    
    # Check if cached data exists
    data_file = os.path.join(os.path.dirname(__file__), 'f1_data.csv')
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
        print("No cached data found - please run download script first")
        print("Run: python3 download_current_data.py")
    
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

@app.post("/api/predict/driver", response_model=PredictionResponse)
async def predict_driver_performance(request: PredictionRequest):
    try:
        result = prediction_service.predict_driver_performance(
            driver_code=request.driver,
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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
