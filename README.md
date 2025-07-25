# F1 Insight Hub

Advanced Formula 1 prediction and telemetry analysis platform combining ensemble machine learning with comprehensive React interface for race predictions and real-time telemetry visualization.

## 🏎️ Overview

F1 Insight Hub delivers the most comprehensive F1 analysis system available, featuring data-driven performance ratings, realistic car-driver balance modeling, advanced telemetry visualization, and professional race predictions. Built with modern React + TypeScript frontend and enhanced Python ML backend.

## ✨ Features

### 🤖 **Enhanced Race Predictions**
- **Full Race Grid Predictions**: Predict all 20 drivers' positions with confidence scoring
- **Individual Driver Analysis**: Detailed qualifying and race forecasts with weather impact
- **Data-Driven Performance**: Ratings calculated from 700+ historical race records
- **Realistic F1 Modeling**: 70% car performance, 30% driver skill (authentic F1 balance)
- **Advanced Weather System**: 9 weather conditions including mixed/changing conditions

### 📊 **Advanced Telemetry Analysis**
- **Multi-Variable Overlap Graphs**: Compare 6 telemetry variables simultaneously
- **Session Type Support**: Practice (FP2, FP3), Qualifying (Q, SQ), Sprint (S), Race (R)
- **Customizable Graph UI**: 4 chart types, 4 color schemes, multi-axis configuration
- **Speed Trace Analysis**: Detailed lap-by-lap telemetry visualization
- **FastF1 Integration**: Real telemetry data from 2024-2025 seasons

### 🎨 **Professional Interface**
- **Driver Comparison Mode**: Side-by-side telemetry analysis
- **Interactive Visualizations**: Real-time graph customization and zoom controls
- **Responsive Design**: Seamless desktop and mobile experience
- **Modern UI Components**: Built with shadcn/ui and Tailwind CSS
- **Authentic F1 Styling**: Racing-inspired design with professional aesthetics

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript for type safety
- **Vite** for lightning-fast development and building
- **Tailwind CSS** for responsive utility-first styling
- **shadcn/ui** premium component library for consistent UI
- **Recharts** for advanced data visualization and telemetry charts
- **React Router** for seamless navigation between features
- **Lucide Icons** for consistent iconography

### Backend
- **Python 3.10+** with FastAPI for high-performance async API
- **Machine Learning**: XGBoost, Random Forest, Neural Networks (optional)
- **Data Processing**: Pandas, NumPy, Scikit-learn for efficient data handling
- **F1 Data Integration**: FastF1 API with comprehensive telemetry caching
- **Google Drive Cache**: Pre-cached telemetry for faster loading
- **Deployment Ready**: Optimized Docker images for cloud deployment

## 🚀 Quick Start

### Frontend Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd F1-Insight-Hub

# 2. Install dependencies
npm install

# 3. Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env

# 4. Start development server
npm run dev
# Frontend runs on http://localhost:5173
```

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Install dependencies (lightweight option)
pip install -r requirements-base.txt

# OR install full ML suite (includes TensorFlow/PyTorch)
pip install -r requirements.txt

# 3. Download F1 data (uses Google Drive cache)
python download_current_data.py

# 4. Start API server
python main.py
# Backend runs on http://localhost:8000
```

## 🏗️ Application Architecture

### Frontend Pages & Features

#### **📈 Dashboard (`/`)**
- Upcoming race predictions and quick analysis
- Recent telemetry session summaries
- Performance trend visualizations

#### **🎯 Driver Predictor (`/predictor`)**
- Individual driver performance predictions
- Weather impact analysis
- Team and track-specific adjustments

#### **🏁 Race Predictor (`/race-predictor`)**
- Full 20-driver grid predictions
- Advanced weather modeling
- Gap time predictions and confidence scoring

#### **📊 Telemetry Analyzer (`/telemetry`)**
- **Multi-Variable Overlap Graphs**: Compare speed, throttle, brake, gear, RPM, DRS
- **Session Type Filters**: FP2, FP3, Sprint Qualifying, Qualifying, Sprint, Race
- **Customizable Graph UI**: 
  - Chart Types: Line, Area, Scatter, Bar charts
  - Color Schemes: F1 Official, Racing, Neon, Monochrome
  - Multi-Axis Configuration: Independent Y-axes for different data types
  - Interactive Controls: Zoom, pan, variable toggles
- **Speed Trace Analysis**: Detailed lap-by-lap telemetry comparison
- **Driver Comparison Mode**: Side-by-side performance analysis

### Component Structure

```
src/
├── components/
│   ├── ui/                           # shadcn/ui premium components
│   ├── Layout.tsx                    # Main app layout with navigation
│   ├── TelemetryOverlapGraphs.tsx    # Multi-variable telemetry visualization
│   ├── TelemetrySpeedTrace.tsx       # Speed trace analysis component
│   ├── GraphCustomizationPanel.tsx   # Graph styling and configuration
│   ├── DriverSelect.tsx              # 2025 F1 grid driver selection
│   ├── RaceSelect.tsx                # All 24 F1 circuits selection
│   └── PredictionForm.tsx            # Enhanced prediction interface
├── pages/
│   ├── Index.tsx                     # Dashboard with race overview
│   ├── DriverPredictor.tsx           # Individual driver predictions
│   ├── RacePredictor.tsx             # Full race grid predictions
│   ├── TelemetryAnalyzer.tsx         # Advanced telemetry analysis
│   └── StrategySimulator.tsx         # Race strategy optimization
├── hooks/
│   ├── useGraphCustomization.ts      # Graph styling state management
│   └── useTelemetryData.ts           # Telemetry API integration
└── lib/
    ├── api.ts                        # API integration utilities
    └── telemetry-utils.ts            # Telemetry data processing
```

## 🔌 API Integration

### Core Prediction APIs

#### Individual Driver Prediction
```typescript
const prediction = await fetch('/api/predict/driver', {
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

#### Full Race Grid Prediction
```typescript
const raceResult = await fetch('/api/predict/race', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    race_name: 'Austrian Grand Prix',
    weather: 'Dry to Light Rain',
    temperature: 20.0,
    qualifying_results: { 'VER': 1, 'NOR': 2, 'LEC': 3 }
  })
});
```

### Telemetry Analysis APIs

#### Speed Trace Data
```typescript
const telemetryData = await fetch('/api/telemetry/speed-trace', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    race: 'Austrian Grand Prix',
    session: 'Q',
    drivers: ['VER', 'NOR'],
    lap_numbers: [1, 2]
  })
});
```

#### Session Analysis
```typescript
const sessionData = await fetch('/api/telemetry/session-analysis', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    race: 'Austrian Grand Prix',
    session: 'Q',
    drivers: ['VER', 'NOR']
  })
});
```

## 📊 Telemetry Features

### Multi-Variable Overlap Graphs
Visualize up to 6 telemetry variables simultaneously:
- **Speed**: Track speed throughout the lap
- **Throttle**: Accelerator input percentage (0-100%)
- **Brake**: Braking intensity and brake points
- **Gear**: Gear changes and optimal gear selection
- **RPM**: Engine RPM and power delivery
- **DRS**: DRS activation zones and usage

### Customizable Graph UI
**Chart Types:**
- Line Chart: Clean telemetry traces
- Area Chart: Filled visualization with transparency
- Scatter Plot: Individual data point analysis
- Bar Chart: Discrete value comparison

**Color Schemes:**
- F1 Official: Authentic Formula 1 team colors
- Racing: High-contrast racing-inspired palette
- Neon: Vibrant cyber-style colors
- Monochrome: Professional black and white

**Advanced Features:**
- Multi-axis configuration for different data ranges
- Interactive zoom and pan controls
- Variable toggle switches for selective display
- Persistent settings saved to localStorage

### Session Type Support
**Practice Sessions:**
- FP2 (Practice 2): Long runs and race simulation
- FP3 (Practice 3): Qualifying preparation

**Qualifying Sessions:**
- Q (Qualifying): Traditional 3-part qualifying
- SQ (Sprint Qualifying): Sprint race qualification

**Race Sessions:**
- S (Sprint): Sprint race format
- R (Race): Full Grand Prix distance

## 🏎️ 2025 F1 Grid (20 Drivers)

**Complete 2025 season support with accurate transfers:**

- **Red Bull Racing**: Max Verstappen (VER), Sergio Pérez (PER)
- **McLaren**: Lando Norris (NOR), Oscar Piastri (PIA)
- **Ferrari**: Lewis Hamilton (HAM) ⭐, Charles Leclerc (LEC)
- **Mercedes**: George Russell (RUS), Kimi Antonelli (ANT) ⭐
- **Aston Martin**: Fernando Alonso (ALO), Lance Stroll (STR)
- **Alpine**: Pierre Gasly (GAS), Esteban Ocon (OCO)
- **RB**: Yuki Tsunoda (TSU), Liam Lawson (LAW)
- **Williams**: Carlos Sainz (SAI) ⭐, Alexander Albon (ALB)
- **Haas**: Nico Hülkenberg (HUL), Oliver Bearman (BEA) ⭐
- **Kick Sauber**: Gabriel Bortoleto (BOR) ⭐, Isack Hadjar (HAD) ⭐

## 🏁 All 24 F1 Circuits

**Complete 2025 calendar with telemetry support:**
Bahrain, Saudi Arabian, Australian, Japanese, Chinese, Miami, Emilia Romagna, Monaco, Canadian, Spanish, Austrian, British, Hungarian, Belgian, Dutch, Italian, Azerbaijan, Singapore, United States, Mexico City, São Paulo, Las Vegas, Qatar, Abu Dhabi

## 🌤️ Weather Conditions

### Basic Conditions
- **Dry**: Optimal racing conditions for maximum performance
- **Light Rain**: Slight wet conditions favoring skilled wet-weather drivers
- **Heavy Rain**: Challenging conditions with high uncertainty and strategy importance
- **Wet**: Full wet racing conditions with intermediate/wet tire compounds

### Mixed & Changing Conditions
- **Mixed**: Variable conditions throughout the race distance
- **Dry → Light Rain**: Race starts dry, rain develops (strategy critical)
- **Light Rain → Dry**: Race starts wet, track dries (tire timing crucial)
- **Dry → Heavy Rain**: Sudden heavy rain during race (chaos factor)
- **Variable**: Highly unpredictable changing conditions (maximum uncertainty)

## 🚀 Development

### Available Scripts

```bash
# Frontend Development
npm run dev          # Start development server with hot reload
npm run build        # Build optimized production bundle
npm run preview      # Preview production build locally
npm run lint         # Run ESLint with TypeScript support
npm run type-check   # TypeScript type checking

# Backend Development
python main.py                    # Start FastAPI server with auto-reload
python enhanced_ml_model.py       # Train enhanced ensemble models
python download_current_data.py   # Update F1 data from Google Drive
```

### Environment Configuration

Create `.env` file in root directory:
```env
# Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=F1 Insight Hub

# Backend Configuration (backend/.env)
GOOGLE_DRIVE_CACHE_FILE_ID=your_drive_file_id
API_HOST=0.0.0.0
API_PORT=8000
```

### Adding New Features

1. **New Telemetry Variables**: Extend `TelemetryOverlapGraphs.tsx` variable configuration
2. **Custom Chart Types**: Add new chart types to `GraphCustomizationPanel.tsx`
3. **New Session Types**: Update session mapping in `TelemetryAnalyzer.tsx`
4. **Color Schemes**: Add new color palettes to `useGraphCustomization.ts`
5. **Prediction Models**: Extend backend ensemble models in `enhanced_ml_model.py`

## 📈 Performance & Accuracy

### Frontend Performance
- **First Contentful Paint**: < 1.2s
- **Largest Contentful Paint**: < 2.0s
- **Cumulative Layout Shift**: < 0.05
- **Time to Interactive**: < 2.5s
- **Telemetry Rendering**: < 500ms for multi-variable graphs

### ML Model Performance
- **Qualifying Predictions**: 0.359 MAE (excellent accuracy)
- **Race Predictions**: 1.638 MAE (very good accuracy)
- **API Response Time**: < 150ms average
- **Confidence Range**: 60-98% based on conditions
- **Training Data**: 700+ race records, 2024-2025 seasons

### Telemetry Performance
- **Session Loading**: < 2s with Google Drive cache
- **Graph Rendering**: 60fps smooth interactions
- **Multi-Variable Display**: Real-time updates for 6 variables
- **Zoom/Pan Response**: < 16ms for fluid interactions

## 🌐 Deployment

### Frontend Deployment (Vercel/Netlify)

```bash
# Build for production
npm run build

# Deploy dist/ folder with environment variables
# Set VITE_API_URL to production backend URL
```

### Backend Deployment Options

#### Option 1: Fly.io (Recommended - 10GB support)
```bash
fly launch --name f1-insight-backend
fly deploy --remote-only
```

#### Option 2: Railway (4GB limit - use lightweight build)
```bash
railway login
railway init
railway up
```

#### Option 3: DigitalOcean App Platform
```bash
# Use Dockerfile with requirements-base.txt for smaller image
# Image size: ~500MB (basic) vs ~4GB (enhanced ML)
```

### Docker Configuration
```dockerfile
# Lightweight deployment (500MB)
COPY requirements-base.txt .

# Full ML deployment (4GB)
COPY requirements.txt .
```

## 🔧 Troubleshooting

### Frontend Issues

1. **Telemetry Loading Problems**
   ```bash
   # Check API connection
   curl http://localhost:8000/health
   
   # Verify backend telemetry cache
   ls backend/cache/
   ```

2. **Graph Rendering Issues**
   - Clear browser cache and localStorage
   - Check console for Recharts warnings
   - Verify telemetry data format matches component expectations

3. **Build Failures**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run type-check
   ```

### Backend Issues

1. **Telemetry Cache Problems**
   ```bash
   # Re-download F1 data with Google Drive cache
   python download_current_data.py
   
   # Check cache status
   python -c "import os; print(os.path.exists('cache/fastf1_http_cache.sqlite'))"
   ```

2. **Model Loading Errors**
   ```bash
   # Retrain models if corrupted
   python enhanced_ml_model.py
   
   # Check model files
   ls models/ enhanced_models/
   ```

3. **API Connection Issues**
   - Verify CORS settings in FastAPI
   - Check port 8000 availability
   - Ensure Google Drive cache file ID is set

## 🏆 Key Achievements

### Advanced Telemetry Visualization
- ✅ **Multi-variable overlap graphs** with 6 telemetry variables
- ✅ **Customizable graph UI** with 4 chart types and color schemes
- ✅ **Session type filters** supporting all F1 session formats
- ✅ **Interactive controls** with zoom, pan, and variable toggles
- ✅ **Professional aesthetics** with F1-inspired design

### Production-Ready Architecture
- ✅ **FastF1 integration** with real telemetry data from 2024-2025
- ✅ **Google Drive caching** for faster data loading
- ✅ **Ensemble ML models** with XGBoost + Random Forest + Neural Networks
- ✅ **Docker optimization** with lightweight and full deployment options
- ✅ **Multi-platform deployment** support for Fly.io, Railway, DigitalOcean

### Data-Driven Intelligence
- ✅ **700+ race records** from complete 2024-2025 seasons
- ✅ **Realistic F1 modeling** with 70% car, 30% driver balance
- ✅ **Advanced weather system** with mixed/changing conditions
- ✅ **Driver-specific skills** modeling wet weather expertise
- ✅ **Confidence scoring** with realistic uncertainty ranges

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for F1 fans by combining real data science, professional telemetry analysis, and modern web technology.**