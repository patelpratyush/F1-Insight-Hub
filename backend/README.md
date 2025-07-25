# F1 Insight Hub - Backend API

FastAPI backend providing F1 race predictions, telemetry analysis, and comprehensive race data through machine learning models and real-time telemetry processing.

## 🏎️ Features

### **🤖 Machine Learning Predictions**
- **Ensemble Models**: XGBoost + Random Forest + Neural Networks (optional)
- **Basic Prediction Service**: Lightweight scikit-learn models for deployment
- **Data-Driven Ratings**: Performance calculated from 700+ historical race records
- **Weather Modeling**: 9 weather conditions with driver-specific wet weather skills

### **📊 Telemetry Analysis**
- **FastF1 Integration**: Real telemetry data from 2024-2025 seasons
- **Multi-Variable Analysis**: Speed, throttle, brake, gear, RPM, DRS traces
- **Session Support**: Practice (FP2, FP3), Qualifying (Q, SQ), Sprint (S), Race (R)
- **Google Drive Cache**: Pre-cached telemetry for faster loading

### **🏁 Race Predictions**
- **Individual Driver Predictions**: Position and confidence scoring
- **Full Grid Predictions**: Complete 20-driver race results
- **Car Performance Priority**: 70% car, 30% driver (realistic F1 balance)
- **Strategy & Reliability**: Pit stop strategy and DNF probability modeling

## 🚀 Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download F1 data (uses Google Drive cache)
python download_current_data.py

# 3. Run the server
python main.py
# Server starts at http://localhost:8000
```

### Production Deployment

#### Option 1: Fly.io (Recommended - 10GB image support)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
cd backend
fly launch --name your-f1-backend
fly deploy --remote-only
```

#### Option 2: Railway (4GB limit)

```bash
# Connect to Railway
railway login
railway init

# Deploy
railway up
```

#### Option 3: DigitalOcean App Platform

```bash
# Use the optimized Dockerfile
# Image size: ~500MB (basic) or ~4GB (enhanced ML)
```

## 📦 Deployment Configurations

### Basic Deployment (Lightweight - ~500MB)

Uses `requirements-base.txt` - includes essential prediction models without TensorFlow/PyTorch:

```bash
# Dockerfile uses requirements-base.txt
# Excludes enhanced ML models for smaller image size
```

**Features Available:**
- ✅ Race predictions (XGBoost + Random Forest)
- ✅ Telemetry analysis 
- ✅ All API endpoints
- ✅ Google Drive cache integration

### Enhanced Deployment (Full ML - ~4GB)

Uses `requirements.txt` - includes all ML models with TensorFlow/PyTorch:

```bash
# Dockerfile uses full requirements.txt
# Includes enhanced ensemble models
```

**Additional Features:**
- ✅ Neural Network models
- ✅ Enhanced ensemble predictions
- ✅ Advanced hyperparameter optimization

## 🔌 API Endpoints

### Core Prediction APIs

#### `POST /api/predict/driver`
Individual driver performance prediction:

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

#### `POST /api/predict/race`
Full race grid prediction:

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

### Telemetry Analysis APIs

#### `GET /api/telemetry/sessions`
Available sessions for analysis:

```bash
curl "http://localhost:8000/api/telemetry/sessions?race=Austrian%20Grand%20Prix"
```

#### `POST /api/telemetry/speed-trace`
Driver speed and telemetry traces:

```bash
curl -X POST "http://localhost:8000/api/telemetry/speed-trace" \
  -H "Content-Type: application/json" \
  -d '{
    "race": "Austrian Grand Prix",
    "session": "Q",
    "drivers": ["VER", "NOR"],
    "lap_numbers": [1, 2]
  }'
```

#### `POST /api/telemetry/session-analysis`
Comprehensive session telemetry analysis:

```bash
curl -X POST "http://localhost:8000/api/telemetry/session-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "race": "Austrian Grand Prix",
    "session": "Q",
    "drivers": ["VER", "NOR"]
  }'
```

### Health & Status

#### `GET /health`
Server health and feature availability:

```bash
curl "http://localhost:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "enhanced_ml": true,
  "telemetry_available": true
}
```

## 🏗️ Architecture

### File Structure

```
backend/
├── main.py                              # FastAPI server with all endpoints
├── f1_data.csv                          # Historical race data (700+ records)
├── download_current_data.py             # Google Drive data loader
├── google_drive_data_loader.py          # Google Drive cache utilities
├── requirements.txt                     # Full dependencies (with ML)
├── requirements-base.txt                # Basic dependencies (lightweight)
├── Dockerfile                           # Optimized for cloud deployment
├── fly.toml                            # Fly.io configuration
├── services/
│   ├── prediction_service.py               # Basic ML predictions
│   ├── enhanced_ensemble_service.py        # Advanced ensemble models
│   ├── enhanced_prediction_service.py      # Enhanced individual predictions
│   ├── race_prediction_service.py          # Full race grid predictions
│   ├── telemetry_analyzer_service.py       # Telemetry processing
│   └── data_service.py                     # Data utilities
├── models/                              # Basic prediction models
│   ├── f1_qualifying_gbm_model.pkl
│   ├── f1_race_gbm_model.pkl
│   └── *.pkl                            # Scalers and encoders
├── enhanced_models/                     # Enhanced ensemble models
│   ├── qualifying_ensemble.pkl
│   ├── race_ensemble.pkl
│   └── *.pkl                            # Enhanced features
└── cache/                               # FastF1 telemetry cache
    ├── 2024/                            # Complete 2024 season
    ├── 2025/                            # 2025 season data
    └── fastf1_http_cache.sqlite         # HTTP cache database
```

### Service Architecture

```mermaid
graph TD
    A[FastAPI Main] --> B[Prediction Service]
    A --> C[Telemetry Service]
    A --> D[Race Prediction Service]
    
    B --> E[Enhanced Ensemble]
    B --> F[Basic Models]
    
    C --> G[FastF1 Cache]
    C --> H[Google Drive Cache]
    
    D --> I[Data-Driven Ratings]
    D --> J[Weather Modeling]
```

## 🌤️ Weather Conditions

### Basic Conditions
- **Dry**: Normal racing conditions
- **Light Rain**: Slight wet conditions
- **Heavy Rain**: Challenging wet conditions  
- **Wet**: Full wet racing

### Mixed/Changing Conditions
- **Mixed**: Variable conditions throughout race
- **Dry → Light Rain**: Strategy critical
- **Light Rain → Dry**: Tire timing crucial
- **Dry → Heavy Rain**: High uncertainty
- **Variable**: Maximum unpredictability

## 🏎️ 2025 F1 Grid Support

**All 20 Drivers & Teams:**
- Red Bull, McLaren, Ferrari, Mercedes
- Aston Martin, Alpine, RB, Williams
- Haas, Kick Sauber
- Includes accurate 2025 transfers (Hamilton → Ferrari, etc.)

**All 24 Circuits:**
- Complete 2025 F1 calendar support
- Track-specific performance modeling

## 📈 Model Performance

### Prediction Accuracy
- **Qualifying MAE**: 0.359 positions (excellent)
- **Race MAE**: 1.638 positions (very good)
- **Training Data**: 700+ race records from 2024-2025

### Telemetry Performance
- **Session Types**: 6 supported (FP2, FP3, SQ, Q, S, R)
- **Cache Size**: ~4GB telemetry data
- **Response Time**: <200ms with cache

### Weather Impact Modeling
- **Dry Conditions**: 80-95% confidence
- **Mixed Conditions**: 60-80% confidence (realistic uncertainty)
- **Driver-Specific**: Hamilton/Verstappen excel in wet

## 🔧 Configuration

### Environment Variables

```bash
# Google Drive Cache (recommended)
GOOGLE_DRIVE_CACHE_FILE_ID=your_drive_file_id

# Optional: API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Google Drive Setup

1. Upload FastF1 cache to Google Drive
2. Make the file publicly shareable
3. Extract file ID from share URL
4. Set `GOOGLE_DRIVE_CACHE_FILE_ID` environment variable

### Docker Configuration

```dockerfile
# Lightweight deployment (500MB)
COPY requirements-base.txt .

# Full ML deployment (4GB)  
COPY requirements.txt .
```

## 🛠️ Development

### Adding New Features

1. **New Prediction Model**: Add to `services/`
2. **New Telemetry Analysis**: Extend `telemetry_analyzer_service.py`
3. **New API Endpoint**: Add to `main.py`

### Testing

```bash
# Test basic predictions
python -c "from services.prediction_service import PredictionService; print(PredictionService().predict_race_position('VER', 'Monaco Grand Prix', 'Dry', 'Red Bull'))"

# Test telemetry
python -c "from services.telemetry_analyzer_service import TelemetryAnalyzerService; print(TelemetryAnalyzerService().get_available_sessions())"
```

### Performance Optimization

- **Cache Strategy**: Google Drive for telemetry, local for predictions
- **Model Loading**: Lazy loading for enhanced models
- **API Response**: Async endpoints for better concurrency

## 🚀 Production Tips

### Scaling

- **Horizontal**: Deploy multiple instances behind load balancer
- **Vertical**: Increase memory for enhanced ML models (recommend 2GB+)
- **Caching**: Use Redis for frequent prediction requests

### Monitoring

- **Health Checks**: `/health` endpoint for container orchestration
- **Logging**: Structured logging for telemetry requests
- **Metrics**: Track prediction accuracy and response times

### Security

- **CORS**: Configured for frontend integration
- **Environment Variables**: Never commit API keys
- **Input Validation**: Pydantic models for all requests