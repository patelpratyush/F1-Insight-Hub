# 🏎️ F1 Insight Hub

> **Comprehensive Formula 1 Data Analytics Platform with Live Integration, Monte Carlo Predictions, and Advanced Telemetry Analysis**

F1 Insight Hub is a cutting-edge platform that brings together real-time F1 data, rating-based Monte Carlo race predictions, advanced telemetry analysis, and strategic race simulation in a unified dashboard experience.

---

## ✨ Key Features

### 🌐 Live Data Integration

- **Real-time Weather**: Live weather conditions for all F1 circuits using OpenWeatherMap API
- **Race Weekend Forecasting**: 3-day weather forecasts with tire strategy recommendations
- **Championship Standings**: Auto-updating driver and constructor standings with battle analysis
- **Session Results**: Live qualifying results, race analysis, and session comparisons

### 🧠 Rating-Based Monte Carlo Predictions

- **Weighted Rating Engine**: Combines driver skill, team pace, season form, weather modifier, and track affinity into a single per-driver score
- **Monte Carlo Race Simulation**: Each prediction runs 1,000 simulated races with Gaussian noise to produce win/podium/points probabilities and a genuine confidence interval
- **Driver Performance Prediction**: Individual driver race position predictions with a real per-factor rating breakdown
- **Full Grid Prediction**: Complete race grid predictions with simulation-derived confidence scoring
- **Honest Accuracy Metric**: Reports rank concordance between the rating engine's driver ordering and actual current championship standings — not a claimed out-of-sample accuracy

### 📊 Advanced Telemetry Analysis

- **Session Telemetry**: Comprehensive race and qualifying session analysis
- **Speed Trace Analysis**: Detailed speed traces with throttle/brake overlay
- **Driver Comparisons**: Side-by-side telemetry comparison between drivers
- **Track Mapping**: Interactive track maps with racing line visualization

### 🎯 Strategy Simulation

- **Monte Carlo Simulation**: Advanced tire strategy simulation with race events
- **AI-Powered Optimization**: Google Gemini AI integration for intelligent strategy recommendations
- **Multi-Strategy Comparison**: Compare different tire strategies for optimal race planning
- **Real-time Strategy Adaptation**: Dynamic strategy adjustments based on race conditions

### 🎨 Modern Dashboard

- **Real-time Updates**: Live data refresh with auto-updating components
- **Interactive Visualizations**: Charts, graphs, and track maps powered by Recharts
- **Responsive Design**: Optimized for desktop and mobile viewing
- **Dark Theme**: Professional dark theme with F1-inspired color scheme

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **OpenWeatherMap API Key** (free tier available)

### Backend Setup

1. **Clone and navigate to backend**

   ```bash
   cd backend
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the FastAPI server**

   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

   **First startup**: The system will automatically download F1 data (5-10 minutes)

### Frontend Setup

1. **Navigate to frontend root**

   ```bash
   cd ..  # Back to project root
   ```

2. **Install Node.js dependencies**

   ```bash
   npm install
   ```

3. **Start the development server**

   ```bash
   npm run dev
   ```

   The dashboard will be available at `http://localhost:5173`

### Live Data Setup (Required)

To enable live weather and championship data, you need API keys:

1. **Get OpenWeatherMap API Key** (Required):
   - Visit [OpenWeatherMap](https://openweathermap.org/api)
   - Sign up for free account (1000 calls/day free tier)
   - Copy your API key from dashboard
   - Add to `backend/.env` as `OPENWEATHER_API_KEY=your_key_here`

2. **Get Google Gemini API Key** (Optional - for AI strategy):
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create API key for Gemini Pro
   - Add to `backend/.env` as `GEMINI_API_KEY=your_key_here`

---

## 🏗️ Project Structure

```bash
F1-Insight-Hub/
├── backend/                     # FastAPI backend
│   ├── services/               # Business logic services
│   │   ├── live_weather_service.py      # Weather API integration
│   │   ├── f1_results_service.py        # F1 results & standings
│   │   ├── enhanced_prediction_service.py # ML predictions
│   │   ├── strategy_simulation_service.py # Strategy simulation
│   │   └── telemetry_analyzer_service.py  # Telemetry analysis
│   ├── api/                    # API route handlers
│   ├── cache/                  # FastF1 data cache
│   ├── main.py                 # FastAPI application
│   └── requirements.txt        # Python dependencies
├── src/                        # React frontend
│   ├── components/             # Reusable UI components
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx       # Main dashboard with live data
│   │   ├── DriverPredictor.tsx # Individual predictions
│   │   ├── RacePredictor.tsx   # Grid predictions
│   │   ├── TelemetryAnalyzer.tsx # Telemetry analysis
│   │   └── StrategySimulator.tsx # Strategy simulation
│   └── hooks/                  # Custom React hooks
└── README.md                   # This file
```

---

## 🛠️ Tech Stack

### Frontend

- **React 18** with TypeScript for type safety
- **Vite** for lightning-fast development
- **Tailwind CSS** for responsive styling
- **shadcn/ui** for premium components
- **Recharts** for data visualization
- **React Router** for navigation

### Backend

- **Python 3.11+** with FastAPI for high-performance API
- **Prediction Engine**: Weighted rating model + NumPy-vectorized Monte Carlo simulation (1,000 trials/prediction)
- **Data Processing**: NumPy
- **F1 Data**: FastF1 API with telemetry caching, Jolpica-F1 for standings/results
- **Live APIs**: OpenWeatherMap, Google Gemini (optional strategy insight)

---

## 📖 Dashboard Features

### Main Dashboard (`/`)

- **Live Weather Conditions**: Real-time weather for upcoming races with circuit selection
- **Race Weekend Forecast**: 3-day weather timeline with tire strategy recommendations
- **Championship Standings**: Current driver and constructor standings with battle analysis
- **Dynamic Race Detection**: Automatically shows next upcoming race
- **Weekend Analysis**: Weather trends, temperature ranges, strategy impact

### Driver Predictor (`/predictor`)

- Individual driver performance predictions
- Weather impact analysis with 9+ weather conditions
- Rating-based Monte Carlo simulation with simulation-derived confidence scoring
- Driver and team ratings computed from live championship standings

### Race Predictor (`/race-predictor`)

- Full 20-driver grid predictions
- Championship impact analysis
- Weather-adjusted performance modeling
- Confidence intervals and uncertainty ranges

### Telemetry Analyzer (`/telemetry`)

- Multi-variable overlap graphs (Speed, Throttle, Brake, Gear, RPM, DRS)
- Session type support (Practice, Qualifying, Sprint, Race)
- Customizable graph UI with 4 chart types and color schemes
- Driver comparison mode with side-by-side analysis

### Strategy Simulator (`/strategy`)

- Monte Carlo race strategy simulation
- AI-powered optimization with Google Gemini
- Multi-strategy comparison
- Tire degradation modeling

---

## 📋 Environment Configuration

### Backend Environment Variables

Create `backend/.env` file:

```bash
# Required: OpenWeatherMap API Integration
OPENWEATHER_API_KEY=your_openweathermap_api_key_here

# Optional: Google Gemini AI Integration  
GEMINI_API_KEY=your_google_gemini_api_key_here

# Optional: Database Configuration
DATABASE_URL=sqlite:///./f1_data.db

# Optional: Cache Configuration
CACHE_DIR=./cache
FASTF1_CACHE_ENABLED=true

# Optional: Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend Environment Variables

Create `.env` file in project root:

```bash
# API Endpoint Configuration
VITE_API_URL=http://localhost:8000

# Optional: Application Configuration
VITE_APP_TITLE=F1 Insight Hub
```

### API Key Setup Guide

**OpenWeatherMap API Key (Required)**:

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Create free account (1,000 calls/day limit)
3. Navigate to "API keys" in dashboard
4. Copy your API key
5. Add to `backend/.env` as `OPENWEATHER_API_KEY=your_key`

**Free Tier Limits**:

- 1,000 API calls per day
- 60 calls per minute
- Current weather + 5-day forecast

**Google Gemini API Key (Optional)**:

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create new API key for Gemini Pro
4. Add to `backend/.env` as `GEMINI_API_KEY=your_key`

**Gemini Features**:

- AI-powered strategy optimization
- Intelligent race analysis
- Advanced weather recommendations
- Contextual strategy insights

---

## 📊 API Reference

### Live Data APIs

#### Get Current Weather

```bash
curl -X POST "http://localhost:8000/api/weather/current" \
  -H "Content-Type: application/json" \
  -d '{"circuit_name": "Silverstone"}'
```

#### Get Race Weekend Forecast  

```bash
curl -X POST "http://localhost:8000/api/weather/race-weekend" \
  -H "Content-Type: application/json" \
  -d '{"circuit_name": "Silverstone", "race_date": "2025-08-31"}'
```

#### Get Championship Standings

```bash
curl -X GET "http://localhost:8000/api/championship/standings"
```

#### Get Next Upcoming Race

```bash
curl -X GET "http://localhost:8000/api/results/next-race"
```

### Prediction APIs

#### Individual Driver Prediction

```bash
curl -X POST "http://localhost:8000/api/predict/driver" \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "VER",
    "track": "British Grand Prix",
    "weather": "dry"
  }'
```

#### Full Race Grid Prediction

```bash
curl -X POST "http://localhost:8000/api/predict/race" \
  -H "Content-Type: application/json" \
  -d '{
    "track": "Hungarian Grand Prix",
    "weather": "dry"
  }'
```

### Strategy & Telemetry APIs

#### Strategy Simulation

```bash
curl -X POST "http://localhost:8000/api/strategy/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "VER",
    "track": "Silverstone",
    "tire_strategy": "Medium-Hard-Hard"
  }'
```

#### Telemetry Analysis

```bash
curl -X POST "http://localhost:8000/api/telemetry/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2024,
    "race": "British Grand Prix",
    "session": "R",
    "drivers": ["VER", "NOR"]
  }'
```

---

## 🚀 Deployment

### Development Setup

**Frontend**:

```bash
npm run dev          # Development server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build
```

**Backend**:

```bash
python main.py                    # FastAPI server with auto-reload
python enhanced_ml_model.py       # Train ML models
python download_current_data.py   # Download F1 data cache
```

### Production Deployment

**Frontend Deployment (Vercel/Netlify)**:

```bash
npm run build
# Deploy dist/ folder
# Set VITE_API_URL to production backend URL
```

**Backend Deployment Options**:

1. **Fly.io (Recommended - handles large ML models)**:

   ```bash
   fly launch --name f1-insight-backend
   fly deploy --remote-only
   ```

2. **Railway (4GB limit - use lightweight build)**:

   ```bash
   railway login
   railway init
   railway up
   ```

3. **Docker Deployment**:

   ```bash
   # Full ML deployment (4GB)
   docker build -t f1-insight-hub .
   docker run -p 8000:8000 f1-insight-hub
   
   # Lightweight deployment (500MB)
   docker build -f Dockerfile.light -t f1-insight-hub-light .
   ```

**Production Environment Variables**:

```bash
export OPENWEATHER_API_KEY="your_production_key"
export GEMINI_API_KEY="your_production_key"
export DATABASE_URL="postgresql://user:pass@localhost/f1db"
```

---

## 🔧 Troubleshooting

### Common Issues

**Backend Won't Start**:

- Check Python version: `python --version` (need 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Verify API keys in `backend/.env`
- Check port 8000 availability: `lsof -i :8000`

**Frontend Build Issues**:

```bash
rm -rf node_modules package-lock.json
npm install
npm run type-check
```

**API Key Issues**:

```bash
# Test if API key is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENWEATHER_API_KEY'))"
```

**Data Download Issues**:

- First startup downloads ~2GB F1 data (10-15 minutes)
- Ensure stable internet connection
- Check `backend/cache/` directory exists
- Restart if download fails: `python download_current_data.py`

**Live Data Not Updating**:

- Verify OpenWeatherMap API key is valid
- Check API quota usage
- Restart backend after adding API keys
- Test API directly: `curl localhost:8000/api/weather/circuits`

### Performance Issues

**Slow API Responses**:

- Clear cache: `rm -rf backend/cache/`
- Rebuild cache: `python download_current_data.py`
- Use SSD storage for cache directory
- Consider PostgreSQL for production database

**Memory Issues**:

- Monte Carlo simulation is lightweight (NumPy vectorized, ~1000 trials/prediction)
- Use lightweight deployment for resource-constrained environments
- Monitor memory usage: `htop` or `top`

---

## 📈 Model Performance

### Prediction Accuracy

The rating engine reports a **rank concordance** score with every prediction: the
percentage of driver pairs where the rating engine's ordering agrees with the
actual current championship order. This is an honest, always-computable metric —
it is not a claim about predicting future race results, since the model isn't
trained on historical outcomes.

- **Simulation Trials**: 1,000 per prediction
- **Rank Concordance**: typically 75-90%, varies with season progress (`model_info.concordant_pct` in API responses)
- **API Response Time**: < 150ms average

### System Performance

- **Frontend**: < 1.2s First Contentful Paint
- **Telemetry Loading**: < 2s with cache
- **Live Data Refresh**: Real-time updates every 5 minutes
- **Graph Rendering**: 60fps smooth interactions

---

## 🌟 Recent Updates

### Live Data Integration (Completed)

✅ Real-time weather API integration  
✅ Dynamic race weekend forecasting  
✅ Auto-updating championship standings  
✅ Live session results integration  

### Rating-Based Monte Carlo Engine (Completed)

✅ Weighted rating model (driver skill, team pace, form, weather, track affinity)  
✅ Vectorized 1,000-trial Monte Carlo race simulation  
✅ Percentile-based confidence intervals from simulation spread  
✅ Rank-concordance accuracy reporting  

### Dashboard Improvements (Completed)

✅ Live weather conditions display  
✅ Race weekend forecast timeline  
✅ Dynamic next race detection  
✅ Championship battle analysis  

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and add tests
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new features  
- Update documentation as needed
- Ensure all tests pass before submitting

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastF1**: Formula 1 telemetry data library
- **OpenWeatherMap**: Live weather data API
- **Google Gemini**: AI-powered strategy optimization
- **Ergast API**: Historical F1 data
- **Shadcn/ui**: Beautiful UI components
- **F1 Community**: For inspiration and feedback

---

**Ready to explore F1 data like never before?** 🏁

Get started with the setup instructions above and dive into the world of Formula 1 analytics with real-time data, Monte Carlo race predictions, and professional telemetry analysis!

---

*Built with ❤️ for F1 fans by combining real data science, professional telemetry analysis, and modern web technology.*
