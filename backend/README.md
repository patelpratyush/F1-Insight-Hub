# F1 Driver Performance Prediction API

FastAPI backend that predicts F1 driver performance using Gradient Boosting Machine Learning trained on 2024-2025 season data.

## Features

- **Gradient Boosting Models**: XGBoost for qualifying and race position predictions
- **Real F1 Data**: 738 race records from 2024-2025 seasons
- **27 Drivers**: Complete F1 grid with 2025 team transfers
- **24 Tracks**: All Grand Prix circuits
- **Weather Impact**: Dry, wet, and mixed conditions
- **Cache-Only**: Uses pre-downloaded F1 data, no API calls

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Run Server

```bash
python3 main.py
```

Server starts on `http://localhost:8000`

### 3. Test API

```bash
curl -X POST "http://localhost:8000/api/predict/driver" \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "VER",
    "track": "Monaco Grand Prix",
    "weather": "dry",
    "team": "Red Bull"
  }'
```

## API Endpoints

### `POST /api/predict/driver`

Predicts driver performance for a specific race.

**Request:**

```json
{
  "driver": "VER",
  "track": "Monaco Grand Prix", 
  "weather": "dry",
  "team": "Red Bull"
}
```

**Response:**

```json
{
  "predicted_qualifying_position": 3,
  "predicted_race_position": 2,
  "qualifying_confidence": 0.85,
  "race_confidence": 0.78
}
```

### `GET /health`

Returns server health status.

## How It Works

### 1. Data Source

- **f1_data.csv**: 738 race records from 2024-2025 seasons
- **cache/**: FastF1 cached telemetry data
- **models/**: Pre-trained XGBoost models

### 2. Machine Learning

- **Algorithm**: XGBoost Gradient Boosting
- **Two Models**: Separate models for qualifying and race predictions
- **Features**: Driver history, track performance, team stats, weather factors
- **Training**: Historical performance patterns from 2024-2025

### 3. Feature Engineering

- Driver performance at specific tracks
- Recent form (last 5 races)
- Team performance trends
- Weather adaptation factors
- 2025 driver transfers (Hamilton to Ferrari)

### 4. Prediction Process

1. Normalize track names and team mappings
2. Extract features from historical data
3. Scale features using trained scaler
4. Predict using XGBoost models
5. Calculate confidence scores
6. Return formatted results

## File Structure

```bash
backend/
├── main.py              # FastAPI server
├── f1_data.csv          # Training data
├── requirements.txt     # Dependencies
├── services/
│   ├── data_service.py      # Data handling
│   └── prediction_service.py # ML predictions
├── models/
│   ├── f1_qualifying_gbm_model.pkl
│   ├── f1_race_gbm_model.pkl
│   ├── feature_scaler.pkl
│   └── label_encoders.pkl
└── cache/               # F1 telemetry cache
```

## Supported Drivers

VER, HAM, RUS, LEC, SAI, NOR, PIA, ALO, STR, GAS, OCO, TSU, RIC, ALB, SAR, MAG, HUL, BOT, ZHO, PER

## Supported Tracks

All 24 F1 Grand Prix circuits (Bahrain, Saudi Arabian, Australian, Japanese, Chinese, Miami, Emilia Romagna, Monaco, Canadian, Spanish, Austrian, British, Hungarian, Belgian, Dutch, Italian, Azerbaijan, Singapore, United States, Mexico City, São Paulo, Las Vegas, Qatar, Abu Dhabi)

## Model Performance

- **Qualifying MAE**: ~2.1 positions
- **Race MAE**: ~2.3 positions
- **Confidence Range**: 50-95%
- **Training Data**: 738 race records, 27 drivers, 25 races

## Notes

- Models are pre-trained and loaded at startup
- No internet connection required for predictions
- 2025 season updates included (Hamilton transfer)
- Cache-only operation for fast response times
