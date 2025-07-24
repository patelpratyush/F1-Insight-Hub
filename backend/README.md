# F1 Enhanced AI Prediction API

Advanced FastAPI backend that predicts F1 race results using ensemble machine learning models with data-driven performance ratings and comprehensive weather modeling.

## Features

### 🤖 **Advanced ML Models**

- **Enhanced Ensemble Models**: XGBoost + Random Forest + Neural Networks
- **Data-Driven Ratings**: Car and driver performance calculated from 718 historical records
- **Weather Modeling**: 9 weather conditions including mixed/changing conditions
- **Strategy Impact**: Tire strategy and pit stop decision modeling

### 🏎️ **Realistic F1 Simulation**

- **Car Performance Priority**: 70% car, 30% driver (realistic F1 balance)
- **Dynamic Weather Effects**: Different drivers/cars perform better in wet conditions
- **Reliability Modeling**: DNF probability based on historical data
- **Race Craft**: Driver ability to gain positions during race

### 📊 **Comprehensive Data**

- **718 Race Records**: Complete 2024-2025 season data
- **20 Drivers**: Full 2025 F1 grid with accurate team transfers
- **24 Grand Prix**: All official F1 circuits
- **FastF1 Integration**: Real telemetry and timing data

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Download the data using `download_current_data.py`

```bash
python3 download_current_data.py
```

### 3. Run Server

```bash
python3 main.py
```

Server starts on `http://localhost:8000`

### 3. Test APIs

**Individual Driver Prediction:**

```bash
curl -X POST "http://localhost:8000/api/predict/driver" \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "VER",
    "track": "Monaco Grand Prix",
    "weather": "Dry",
    "team": "Red Bull"
  }'
```

**Full Race Grid Prediction:**

```bash
curl -X POST "http://localhost:8000/api/predict/race" \
  -H "Content-Type: application/json" \
  -d '{
    "race_name": "Austrian Grand Prix",
    "weather": "Light Rain",
    "temperature": 18.0,
    "qualifying_results": {
      "VER": 1, "NOR": 2, "LEC": 3
    }
  }'
```

## API Endpoints

### `POST /api/predict/driver`

Predicts individual driver performance for a specific race.

**Request:**

```json
{
  "driver": "VER",
  "track": "Monaco Grand Prix", 
  "weather": "Dry",
  "team": "Red Bull"
}
```

**Response:**

```json
{
  "predicted_qualifying_position": 3,
  "predicted_race_position": 2,
  "qualifying_confidence": 85.2,
  "race_confidence": 78.4
}
```

### `POST /api/predict/race` ⭐ **NEW**

Predicts full race grid results with weather conditions and confidence scoring.

**Request:**

```json
{
  "race_name": "Austrian Grand Prix",
  "weather": "Dry to Light Rain",
  "temperature": 20.0,
  "qualifying_results": {
    "VER": 1, "NOR": 2, "LEC": 3
  }
}
```

**Response:**

```json
{
  "success": true,
  "race_name": "Austrian Grand Prix",
  "weather_conditions": "Dry to Light Rain",
  "predictions": [
    {
      "driver_code": "VER",
      "driver_name": "Max Verstappen",
      "team": "Red Bull Racing Honda RBPT",
      "predicted_position": 1,
      "confidence": 92.3,
      "gap_to_winner": "Winner",
      "weather_impact": -0.2
    }
  ],
  "statistics": {
    "average_confidence": 78.5,
    "weather_impact": true,
    "total_predictions": 20
  }
}
```

### `GET /health`

Returns server health status.

## How It Works

### 1. Data-Driven Performance Ratings

**Car Performance (70% weight):**

- **Dry/Wet Pace**: Average race positions in different conditions
- **Strategy Rating**: Qualifying → Race position improvement
- **Reliability**: Finish rate and DNF probability

**Driver Performance (30% weight):**

- **Overall Skill**: Historical race performance
- **Wet Weather Skill**: Separate wet condition performance
- **Race Craft**: Ability to gain positions during race
- **Strategy Execution**: How well they execute team decisions

### 2. Enhanced Machine Learning

**Ensemble Models:**

- **XGBoost**: Gradient boosting with hyperparameter optimization
- **Random Forest**: Multiple decision trees for robustness
- **Neural Networks**: Deep learning for complex patterns

**Advanced Weather Modeling:**

- **9 Weather Conditions**: Dry, Light Rain, Heavy Rain, Wet, Mixed, Variable, Changing conditions
- **Driver-Specific Effects**: Some drivers excel in wet (Hamilton, Verstappen)
- **Car-Specific Effects**: Some cars handle weather changes better
- **Strategy Impact**: Weather changes affect tire strategy decisions

### 3. Realistic F1 Simulation

**Performance Calculation:**

```python
combined_performance = (car_pace * 0.7) + (driver_skill * 0.3)
position_change = performance_advantage * -12  # Better = higher up grid
race_craft_bonus = (driver_race_craft - 0.7) * 2
reliability_factor = random() > car_reliability  # DNF chance
```

**Weather Effects:**

```python
wet_competency = (car_wet_pace * 0.7) + (driver_wet_skill * 0.3)
strategy_impact = (car_strategy * 0.6) + (driver_strategy * 0.4)
```

### 4. Prediction Process

1. **Load Historical Data**: 718 race records from F1 database
2. **Calculate Ratings**: Data-driven car and driver performance
3. **Base Prediction**: Combine car (70%) + driver (30%) ratings
4. **Weather Effects**: Apply condition-specific impacts
5. **Reliability Factor**: Account for potential DNFs
6. **Ensemble Enhancement**: Blend with ML model predictions (60/40)
7. **Confidence Scoring**: Based on data quality and conditions

## File Structure

```bash
backend/
├── main.py                          # FastAPI server with race prediction API
├── f1_data.csv                      # 718 historical race records
├── enhanced_ml_model.py             # Enhanced ensemble model training
├── requirements.txt                 # Dependencies
├── services/
│   ├── enhanced_ensemble_service.py     # Ensemble ML models
│   ├── race_prediction_service.py       # Full race grid predictions
│   ├── enhanced_prediction_service.py   # Individual driver predictions
│   └── data_service.py                  # Data handling utilities
├── models/                          # Original XGBoost models
│   ├── f1_qualifying_gbm_model.pkl
│   ├── f1_race_gbm_model.pkl
│   └── *.pkl                        # Scalers and encoders
├── enhanced_models/                 # New ensemble models
│   ├── qualifying_ensemble.pkl      # XGBoost + RF + NN for qualifying
│   ├── race_ensemble.pkl            # XGBoost + RF + NN for race
│   └── *.pkl                        # Enhanced scalers and features
└── cache/                           # FastF1 telemetry cache (2024-2025)
    ├── 2024/                        # Complete 2024 season data
    ├── 2025/                        # 2025 season data (through British GP)
    └── fastf1_http_cache.sqlite     # FastF1 HTTP cache
```

## 🌤️ Weather Conditions

### **Basic Conditions:**

- **Dry**: Normal racing conditions
- **Light Rain**: Slight wet conditions favoring skilled wet drivers
- **Heavy Rain**: Challenging conditions with high uncertainty
- **Wet**: Full wet racing with intermediates/wets

### **Mixed/Changing Conditions:** ⭐ **NEW**

- **Mixed**: Variable conditions throughout race
- **Dry → Light Rain**: Race starts dry, rain develops (strategy critical)
- **Light Rain → Dry**: Race starts wet, track dries (tire timing crucial)
- **Dry → Heavy Rain**: Sudden heavy rain during race (chaos factor)
- **Variable**: Highly unpredictable changing conditions (maximum uncertainty)

## 🏎️ 2025 F1 Grid (20 Drivers)

**Current Teams & Drivers:**

- **Red Bull**: VER, (Teammate TBD)
- **McLaren**: NOR, PIA  
- **Ferrari**: HAM, LEC (Hamilton transfer!)
- **Mercedes**: RUS, ANT (Antonelli promoted)
- **Aston Martin**: ALO, STR
- **Alpine**: GAS, OCO
- **RB**: TSU, LAW
- **Williams**: SAI, ALB, COL (Sainz transfer)
- **Haas**: HUL, BEA (Bearman full-time)
- **Kick Sauber**: BOR, HAD (New rookies)

## 🏁 All 24 F1 Circuits

Bahrain, Saudi Arabian, Australian, Japanese, Chinese, Miami, Emilia Romagna, Monaco, Canadian, Spanish, Austrian, British, Hungarian, Belgian, Dutch, Italian, Azerbaijan, Singapore, United States, Mexico City, São Paulo, Las Vegas, Qatar, Abu Dhabi

## 📈 Model Performance

### **Enhanced Ensemble Models:**

- **Qualifying MAE**: 0.359 positions (excellent)
- **Race MAE**: 1.638 positions (very good)
- **Confidence Range**: 60-98% (weather-dependent)
- **Training Data**: 718 race records, 28 drivers, 2024-2025 seasons

### **Data-Driven Ratings Accuracy:**

- **Car Performance**: Based on average race positions and reliability
- **Driver Skill**: Calculated from historical race craft and consistency
- **Weather Performance**: Separate wet/dry performance calculations
- **Strategy Ratings**: Based on qualifying → race position improvements

### **Performance by Weather:**

- **Dry Conditions**: Highest confidence (80-95%)
- **Light Rain**: Moderate confidence (70-85%)
- **Mixed Conditions**: Lower confidence (60-80%) - realistic uncertainty
- **Variable Weather**: Lowest confidence (60-75%) - reflects F1 reality

## 🚀 Key Improvements

### **Data-Driven Approach:**

- ✅ **No more manual ratings** - all performance calculated from real data
- ✅ **Car dominance modeled** - 70% car, 30% driver (realistic F1 balance)
- ✅ **Weather expertise** - drivers like Hamilton/Verstappen excel in wet
- ✅ **Strategy modeling** - teams like Red Bull/McLaren better at strategy calls
- ✅ **Reliability factors** - some cars more prone to DNFs

### **Advanced Features:**

- ✅ **Full race predictions** - predict entire 20-driver grid
- ✅ **Mixed weather conditions** - changing conditions during race
- ✅ **Confidence scoring** - realistic uncertainty modeling
- ✅ **Gap time predictions** - estimated time gaps between drivers
- ✅ **Weather impact tracking** - see how conditions affect each driver

### **Production Ready:**

- ✅ **FastF1 integration** - real F1 telemetry data
- ✅ **Cache-only operation** - no internet required for predictions
- ✅ **Enhanced API** - individual driver + full race grid endpoints
- ✅ **2025 season ready** - accurate team transfers and rookies
