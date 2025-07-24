# F1 Insight Hub

Advanced Formula 1 prediction platform combining ensemble machine learning with intuitive React interface for comprehensive race analysis and predictions.

## Overview

F1 Insight Hub delivers the most advanced F1 prediction system available, featuring data-driven performance ratings, realistic car-driver balance modeling, and comprehensive weather condition analysis. Built with modern React + TypeScript frontend and enhanced Python ML backend.

## Features

### 🏎️ **Enhanced Race Predictions** ⭐ **NEW**

- **Full Race Grid Predictions**: Predict all 20 drivers' positions with confidence scoring
- **Data-Driven Performance**: Car and driver ratings calculated from 718 historical race records
- **Realistic F1 Modeling**: 70% car performance, 30% driver skill (authentic F1 balance)
- **Advanced Weather System**: 9 weather conditions including mixed/changing conditions
- **Real-time Confidence**: Dynamic uncertainty based on conditions and data quality

### 🤖 **Advanced ML Models**

- **Ensemble Architecture**: XGBoost + Random Forest + Neural Networks
- **Hyperparameter Optimization**: Automated tuning with Optuna
- **Strategy Modeling**: Tire strategy and pit stop decision impact
- **Reliability Factors**: DNF probability based on historical data
- **Weather Expertise**: Different drivers/cars excel in different conditions

### 📊 **Comprehensive Analytics**

- **Individual Driver Predictions**: Detailed qualifying and race forecasts
- **Strategy Simulation**: Race strategy optimization and tire management
- **Telemetry Analysis**: Advanced data visualization from FastF1
- **Performance Tracking**: Historical trends and form analysis
- **Gap Time Predictions**: Estimated time differences between drivers

### 🎨 **Modern Interface**

- **Responsive Design**: Seamless desktop and mobile experience
- **Real-time Updates**: Live prediction updates with loading states
- **Interactive Weather**: Visual weather condition selection
- **Confidence Visualization**: Clear uncertainty indicators
- **Professional F1 Styling**: Authentic racing-inspired design

## Tech Stack

### Frontend

- **React 18** with TypeScript for type safety
- **Vite** for lightning-fast development
- **Tailwind CSS** for responsive styling
- **shadcn/ui** premium component library
- **React Router** for navigation
- **Recharts** for data visualization
- **Lucide Icons** for consistent iconography

### Backend

- **Python 3.8+** with FastAPI for high-performance API
- **Enhanced ML Stack**: XGBoost, Random Forest, TensorFlow/Keras
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Optimization**: Optuna for hyperparameter tuning
- **F1 Data**: FastF1 API with comprehensive telemetry
- **Real Data**: 718 race records from 2024-2025 seasons

## Quick Start

### Prerequisites

- Node.js 16+ and npm/yarn
- Python 3.8+ and pip
- Git

### Frontend Setup

1. **Clone Repository**

   ```bash
   git clone <repository-url>
   cd F1-Insight-Hub
   ```

2. **Install Dependencies**

   ```bash
   npm install
   ```

3. **Start Development Server**

   ```bash
   npm run dev
   ```

   Frontend runs on `http://localhost:5173`

### Backend Setup

1. **Navigate to Backend**

   ```bash
   cd backend
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   pip install optuna tensorflow
   ```

3. **Start API Server**

   ```bash
   python main.py
   ```

   Backend runs on `http://localhost:8000`

## Application Structure

### Frontend Pages

- **`/`** - Dashboard with upcoming races and quick predictions
- **`/predictor`** - Individual driver performance predictions
- **`/race-predictor` ⭐ NEW** - Full race grid predictions with weather modeling
- **`/telemetry`** - Advanced telemetry data visualization (FastF1 integration)
- **`/strategy`** - Race strategy simulation and tire management

### Enhanced Component Architecture

```bash
src/
├── components/
│   ├── ui/                    # shadcn/ui premium components
│   ├── Layout.tsx            # Main application layout with navigation
│   ├── DriverSelect.tsx      # 2025 F1 grid driver selection
│   ├── RaceSelect.tsx        # All 24 F1 circuits selection
│   └── PredictionForm.tsx    # Enhanced prediction interface
├── pages/
│   ├── Index.tsx             # Dashboard with upcoming races
│   ├── DriverPredictor.tsx   # Individual driver predictions
│   ├── RacePredictor.tsx     # Full race grid predictions ⭐ NEW
│   ├── TelemetryAnalyzer.tsx # FastF1 telemetry analysis
│   └── StrategySimulator.tsx # Race strategy optimization
├── hooks/                    # Custom React hooks for API calls
└── lib/                      # Utilities and API helpers
```

## API Integration

### Individual Driver Prediction

```typescript
const prediction = await fetch('http://localhost:8000/api/predict/driver', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    driver: 'VER',
    track: 'Monaco Grand Prix',
    weather: 'Dry',
    team: 'Red Bull Racing'
  })
});
```

### Full Race Grid Prediction ⭐ **NEW**

```typescript
const raceResult = await fetch('http://localhost:8000/api/predict/race', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    race_name: 'Austrian Grand Prix',
    weather: 'Dry to Light Rain',
    temperature: 20.0,
    qualifying_results: {
      'VER': 1, 'NOR': 2, 'LEC': 3, 'HAM': 4, 'RUS': 5
    }
  })
});
```

### Enhanced Response Formats

**Driver Prediction Response:**
```typescript
interface PredictionResponse {
  predicted_qualifying_position: number;
  predicted_race_position: number;
  qualifying_confidence: number;
  race_confidence: number;
}
```

**Race Grid Response:**
```typescript
interface RacePredictionResponse {
  success: boolean;
  race_name: string;
  weather_conditions: string;
  predictions: Array<{
    driver_code: string;
    driver_name: string;
    team: string;
    predicted_position: number;
    confidence: number;
    gap_to_winner: string;
    weather_impact: number;
  }>;
  statistics: {
    average_confidence: number;
    weather_impact: boolean;
    total_predictions: number;
  };
}
```

## Supported Data

### 🏎️ 2025 F1 Grid (20 Drivers)

**Accurate 2025 transfers and rookies:**
- **Red Bull**: Max Verstappen (VER), (Teammate TBD)
- **McLaren**: Lando Norris (NOR), Oscar Piastri (PIA)
- **Ferrari**: Lewis Hamilton (HAM) ⭐, Charles Leclerc (LEC)
- **Mercedes**: George Russell (RUS), Kimi Antonelli (ANT) ⭐
- **Aston Martin**: Fernando Alonso (ALO), Lance Stroll (STR)
- **Alpine**: Pierre Gasly (GAS), Esteban Ocon (OCO)
- **RB**: Yuki Tsunoda (TSU), Liam Lawson (LAW)
- **Williams**: Carlos Sainz (SAI) ⭐, Alexander Albon (ALB), Franco Colapinto (COL)
- **Haas**: Nico Hulkenberg (HUL), Oliver Bearman (BEA) ⭐
- **Kick Sauber**: Gabriel Bortoleto (BOR) ⭐, Isack Hadjar (HAD) ⭐

### 🏁 All 24 F1 Circuits

**Complete 2025 calendar:**
Bahrain, Saudi Arabian, Australian, Japanese, Chinese, Miami, Emilia Romagna, Monaco, Canadian, Spanish, Austrian, British, Hungarian, Belgian, Dutch, Italian, Azerbaijan, Singapore, United States, Mexico City, São Paulo, Las Vegas, Qatar, Abu Dhabi

### 🌤️ Advanced Weather Conditions ⭐ **NEW**

**Basic Conditions:**
- **Dry**: Normal racing conditions
- **Light Rain**: Favors wet-weather specialists (Hamilton, Verstappen)
- **Heavy Rain**: High uncertainty, strategy critical
- **Wet**: Full wet conditions with intermediate/wet tires

**Mixed/Changing Conditions:**
- **Mixed Conditions**: Variable throughout race
- **Dry → Light Rain**: Strategy timing crucial
- **Light Rain → Dry**: Tire strategy critical
- **Dry → Heavy Rain**: Chaos factor, unpredictable results
- **Variable Weather**: Maximum uncertainty modeling

## Development

### Available Scripts

```bash
# Frontend
npm run dev          # Start development server with hot reload
npm run build        # Build optimized production bundle
npm run preview      # Preview production build locally
npm run lint         # Run ESLint with TypeScript support

# Backend
python main.py       # Start FastAPI server with auto-reload
python enhanced_ml_model.py    # Train enhanced ensemble models
python download_current_data.py  # Update F1 data from FastF1
```

### Environment Configuration

Create `.env` file in root directory:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=F1 Insight Hub
```

### Adding New Features

1. **New Prediction Models**: Extend ensemble in `backend/enhanced_ml_model.py`
2. **Weather Conditions**: Add to `backend/services/race_prediction_service.py`
3. **UI Components**: Follow shadcn/ui patterns in `src/components/`
4. **New Prediction Types**: Add endpoints in `backend/main.py`
5. **Data Visualization**: Use Recharts for consistent chart styling

## Performance & Accuracy

### Frontend Metrics
- **First Contentful Paint**: < 1.2s
- **Largest Contentful Paint**: < 2.0s
- **Cumulative Layout Shift**: < 0.05
- **Time to Interactive**: < 2.5s

### Enhanced ML Performance ⭐ **IMPROVED**
- **Qualifying Predictions**: 0.359 MAE (excellent - less than half position error)
- **Race Predictions**: 1.638 MAE (very good - within 1.6 positions)
- **API Response Time**: < 150ms average
- **Confidence Accuracy**: 60-98% range based on conditions
- **Data Coverage**: 718 race records, 28 drivers, 2024-2025 complete

### Model Accuracy by Conditions
- **Dry Weather**: 80-95% confidence (highest accuracy)
- **Light Rain**: 70-85% confidence (good accuracy)
- **Mixed Conditions**: 60-80% confidence (realistic uncertainty)
- **Variable Weather**: 60-75% confidence (reflects F1 chaos)

## Deployment

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy dist/ folder with environment variables
```

### Backend (Railway/Render/AWS)

```bash
# Ensure all dependencies are in requirements.txt
pip freeze > requirements.txt

# Include FastF1 cache and models in deployment
# Set CORS origins for production domain
```

## Key Improvements ⭐ **NEW**

### **Data-Driven Revolution:**
- ✅ **No manual ratings** - all performance calculated from real F1 data
- ✅ **Realistic F1 balance** - car performance dominates (70%) with driver skill (30%)
- ✅ **Weather expertise modeled** - Hamilton/Verstappen excel in wet conditions
- ✅ **Team strategy differentiated** - Red Bull/McLaren better at strategic calls
- ✅ **Reliability factors** - some cars/drivers more prone to issues

### **Advanced Prediction Features:**
- ✅ **Full race grid predictions** - predict all 20 drivers simultaneously
- ✅ **Mixed weather modeling** - changing conditions during race affect strategy
- ✅ **Gap time predictions** - estimated time differences between drivers
- ✅ **Weather impact tracking** - see how conditions affect each driver
- ✅ **Enhanced confidence scoring** - realistic uncertainty based on data quality

### **Production-Ready Architecture:**
- ✅ **FastF1 integration** - real F1 telemetry and timing data
- ✅ **Ensemble ML models** - XGBoost + Random Forest + Neural Networks
- ✅ **Cache-optimized** - no internet required for core predictions
- ✅ **2025 season ready** - accurate transfers, rookies, team changes
- ✅ **Professional UI** - race-inspired design with intuitive UX

## Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines

- Follow TypeScript strict mode for type safety
- Use shadcn/ui components for design consistency
- Write meaningful commit messages
- Test new ML features against historical data
- Update API documentation for endpoint changes
- Ensure responsive design across all screen sizes

## Troubleshooting

### Common Frontend Issues

1. **Build Failures**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **API Connection Issues**
   - Verify backend running on port 8000
   - Check CORS settings in FastAPI
   - Confirm VITE_API_URL in environment

3. **Weather Condition Errors**
   - Ensure weather values match backend enum
   - Check network tab for API request format

### Common Backend Issues

1. **Model Loading Errors**
   ```bash
   cd backend
   python enhanced_ml_model.py  # Retrain ensemble models
   ```

2. **Data Calculation Failures**
   - Verify f1_data.csv exists and has 718+ records
   - Check FastF1 cache directory structure
   - Ensure all 2025 driver mappings are correct

3. **Prediction API Errors**
   - Check driver code mappings (VER, HAM, etc.)
   - Verify race name format matches historical data
   - Ensure weather conditions are supported

## License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for F1 fans by combining real data science with modern web technology.**