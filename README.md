# F1 Insight Hub

Modern React-based Formula 1 prediction application with advanced machine learning backend for race and qualifying position predictions.

## Overview

F1 Insight Hub combines cutting-edge machine learning with intuitive user interface to deliver accurate F1 predictions. Built with React + TypeScript frontend and Python FastAPI backend using ensemble ML models.

## Features

### 🏎️ Driver Performance Predictions

- **Real-time Predictions**: Get qualifying and race position forecasts
- **Advanced ML Models**: XGBoost + Random Forest + Neural Network ensemble
- **Confidence Scoring**: Understand prediction reliability
- **2025 Season Ready**: Updated with latest driver transfers and team changes

### 📊 Comprehensive Analytics

- **Driver Profiles**: Complete statistics and performance history  
- **Track Analysis**: Circuit-specific performance insights
- **Weather Impact**: Condition-based prediction adjustments
- **Team Comparisons**: Head-to-head performance analysis

### 🎨 Modern Interface

- **Responsive Design**: Works seamlessly on desktop and mobile
- **Dark/Light Mode**: Customizable theme preferences
- **Interactive Charts**: Visual data representation with Recharts
- **Real-time Updates**: Live prediction updates and results

## Tech Stack

### Frontend

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for responsive styling
- **shadcn/ui** component library
- **React Router** for navigation
- **TanStack Query** for data fetching
- **Recharts** for data visualization

### Backend

- **Python 3.8+** with FastAPI
- **Machine Learning**: XGBoost, Random Forest, TensorFlow
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Hyperparameter Tuning**: Optuna
- **F1 Data**: FastF1 API integration

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
- **`/predictor`** - Driver performance predictor with detailed analytics
- **`/race-predictor`** - Full race grid predictions and analysis
- **`/telemetry`** - Advanced telemetry data visualization
- **`/strategy`** - Race strategy simulation and optimization

### Component Architecture

```bash
src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   ├── Layout.tsx            # Main application layout
│   ├── DriverSelect.tsx      # Driver selection component
│   ├── RaceSelect.tsx        # Race/track selection
│   └── PredictionForm.tsx    # Main prediction interface
├── pages/
│   ├── Index.tsx             # Dashboard page
│   ├── DriverPredictor.tsx   # Driver prediction page
│   ├── RacePredictor.tsx     # Race prediction page
│   ├── TelemetryAnalyzer.tsx # Telemetry analysis
│   └── StrategySimulator.tsx # Strategy simulation
├── hooks/                    # Custom React hooks
└── lib/                      # Utilities and helpers
```

## API Integration

### Prediction Endpoint

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

### Response Format

```typescript
interface PredictionResponse {
  predicted_qualifying_position: number;
  predicted_race_position: number;
  qualifying_confidence: number;
  race_confidence: number;
}
```

## Supported Data

### Drivers (20 active drivers)

- Max Verstappen (VER) - Red Bull
- Lando Norris (NOR) - McLaren  
- Lewis Hamilton (HAM) - Ferrari
- Charles Leclerc (LEC) - Ferrari
- George Russell (RUS) - Mercedes
- Carlos Sainz (SAI) - Williams
- Oscar Piastri (PIA) - McLaren
- Fernando Alonso (ALO) - Aston Martin
- And 12 more current F1 drivers

### Tracks (24 circuits)

All Formula 1 Grand Prix circuits including:

- Monaco Grand Prix
- British Grand Prix (Silverstone)
- Italian Grand Prix (Monza)
- Belgian Grand Prix (Spa-Francorchamps)
- And 20 more official F1 tracks

### Weather Conditions

- Dry conditions
- Wet conditions  
- Mixed conditions
- Temperature and humidity factors

## Development

### Available Scripts

```bash
# Frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint

# Backend
python main.py       # Start FastAPI server
python enhanced_ml_model.py  # Train enhanced models
python download_current_data.py  # Update F1 data
```

### Environment Configuration

Create `.env` file in root directory:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=F1 Insight Hub
```

### Adding New Features

1. **New Prediction Types**: Extend the ML models in `backend/enhanced_ml_model.py`
2. **UI Components**: Add to `src/components/` following shadcn/ui patterns
3. **New Pages**: Create in `src/pages/` and add routes to `App.tsx`
4. **Data Visualization**: Use Recharts components for new chart types

## Deployment

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy dist/ folder
```

### Backend (Railway/Heroku)

```bash
# Ensure requirements.txt is updated
pip freeze > requirements.txt

# Deploy using platform-specific instructions
```

## Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines

- Follow TypeScript strict mode
- Use shadcn/ui components for consistency
- Write meaningful commit messages
- Test new features thoroughly
- Update documentation for API changes

## Performance

### Frontend Metrics

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Time to Interactive**: < 3s

### Backend Performance

- **API Response Time**: < 200ms average
- **Prediction Accuracy**:
  - Qualifying: 0.359 MAE (excellent)
  - Race: 1.638 MAE (good)
- **Model Loading**: < 5s on startup
- **Data Processing**: < 1s per prediction

## Troubleshooting

### Common Frontend Issues

1. **Build Failures**

   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **API Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS settings in FastAPI
   - Confirm API URL in environment variables

3. **Styling Problems**

   ```bash
   npm run build:dev  # Build with development mode
   ```

### Common Backend Issues

1. **Model Loading Errors**

   ```bash
   cd backend
   python enhanced_ml_model.py  # Retrain models
   ```

2. **Data Download Failures**
   - Check internet connection
   - Verify FastF1 API status
   - Clear cache directory if corrupted

## License

MIT License - See LICENSE file for details.

---
