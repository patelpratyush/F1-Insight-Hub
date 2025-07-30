# F1 Insight Hub

Advanced Formula 1 prediction and telemetry analysis platform combining ensemble machine learning with a beautifully animated React interface for race predictions and real-time telemetry visualization.

## 🏎️ Overview

F1 Insight Hub delivers the most comprehensive F1 analysis system available, featuring data-driven performance ratings, realistic car-driver balance modeling, advanced telemetry visualization, and professional race predictions. Built with modern React + TypeScript frontend and enhanced Python ML backend.

## ✨ Features

### 🏆 **Enhanced F1 Dashboard**
- **Real-time 2025 F1 Championship**: Live standings with Oscar Piastri leading McLaren's title charge
- **Performance Trends Analysis**: Toggle between last 5 races or full season data with driver selection
- **Latest Race Results**: Belgium Grand Prix 2025 podium (Piastri, Norris, Leclerc)
- **Weather Impact Analysis**: Driver performance comparison across different weather conditions
- **Championship Pressure Visualization**: Advanced pressure metrics with mathematical championship possibilities
- **Responsive Card Layout**: Perfectly balanced dashboard with consistent card sizing

### 🤖 **Enhanced Race Predictions**
- **Full Race Grid Predictions**: Predict all 20 drivers' positions with confidence scoring
- **Individual Driver Analysis**: Detailed qualifying and race forecasts with weather impact
- **Data-Driven Performance**: Ratings calculated from 718+ historical race records (2024-2025)
- **Realistic F1 Modeling**: 70% car performance, 30% driver skill (authentic F1 balance)
- **Advanced Weather System**: 9 weather conditions including mixed/changing conditions
- **Enhanced Ensemble Models**: XGBoost + Random Forest + Neural Networks with Optuna optimization

### 📊 **Advanced Telemetry Analysis**
- **Multi-Variable Overlap Graphs**: Compare 6 telemetry variables simultaneously
- **Session Type Support**: Practice (FP2, FP3), Qualifying (Q, SQ), Sprint (S), Race (R)
- **Customizable Graph UI**: 4 chart types, 4 color schemes, multi-axis configuration
- **Speed Trace Analysis**: Detailed lap-by-lap telemetry visualization
- **FastF1 Integration**: Real telemetry data from 2024-2025 seasons with caching

### 🎨 **Professional Animated Interface**
- **Smooth Page Transitions**: Elegant fade-in animations with staggered timing
- **Interactive Visualizations**: Real-time graph customization with animated transitions
- **Animated Background Elements**: Dynamic floating orbs with F1-themed color schemes
- **Enhanced Error Handling**: Loading spinners, error displays, and retry mechanisms
- **Responsive Design**: Seamless desktop and mobile experience with consistent animations
- **Modern UI Components**: Built with shadcn/ui and Tailwind CSS with custom animation system
- **Authentic F1 Styling**: Racing-inspired design with professional aesthetics and motion

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript for type safety and modern hooks
- **Vite** for lightning-fast development and building
- **Tailwind CSS** for responsive utility-first styling with animation utilities
- **shadcn/ui** premium component library for consistent UI components
- **Custom Animation System**: Reusable AnimatedPageWrapper and StaggeredAnimation components
- **Recharts** for advanced data visualization and telemetry charts
- **React Router** for seamless navigation between features
- **Lucide Icons** for consistent iconography throughout the interface

### Backend
- **Python 3.10+** with FastAPI for high-performance async API
- **Enhanced Machine Learning**: XGBoost, Random Forest, Neural Networks with Optuna optimization
- **Advanced Feature Engineering**: Driver momentum, championship pressure, team dynamics
- **Data Processing**: Pandas, NumPy, Scikit-learn for efficient data handling
- **F1 Data Integration**: FastF1 API with comprehensive telemetry caching and corner annotations
- **Google Drive Cache**: Pre-cached telemetry for sub-200ms response times
- **Deployment Ready**: Multi-configuration Docker images for lightweight and full ML deployment

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

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create environment file (optional)
cp .env.example .env
# Edit .env with your Google Drive cache file ID if available

# 4. Start API server
python main.py
# Backend runs on http://localhost:8000
# FastF1 cache will be automatically initialized on first run
```

## 🏗️ Application Architecture

### Frontend Pages & Features

#### **📈 Dashboard (`/`)**
- **Real-time Championship Standings**: 2025 F1 season with Piastri leading at 266 points
- **Performance Trends Chart**: Interactive line chart with Last 5/All Races toggle and driver selection
- **Latest Race Results**: Belgium GP 2025 podium results with lap times and statistics
- **Weather Impact Analysis**: Bar chart showing driver performance across different weather conditions
- **Championship Pressure Visualization**: Advanced pressure metrics for top 6 championship contenders
- **Responsive Card Layout**: Perfectly sized cards with consistent spacing and professional styling

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
│   │   ├── loading-spinner.tsx       # Reusable loading spinner component
│   │   ├── error-display.tsx         # Enhanced error display with retry functionality
│   │   └── data-wrapper.tsx          # Wrapper component for loading states and error handling
│   ├── Layout.tsx                    # Main app layout with navigation
│   ├── AnimatedPageWrapper.tsx       # Reusable page transition animations
│   ├── StaggeredAnimation.tsx        # List/grid item staggered animations
│   ├── ChampionshipPressureChart.tsx # Advanced championship pressure visualization
│   ├── TelemetryOverlapGraphs.tsx    # Multi-variable telemetry visualization
│   ├── TelemetrySpeedTrace.tsx       # Speed trace analysis component
│   ├── GraphCustomizationPanel.tsx   # Graph styling and configuration
│   ├── DriverSelect.tsx              # 2025 F1 grid driver selection
│   ├── RaceSelect.tsx                # All 24 F1 circuits selection
│   └── PredictionForm.tsx            # Enhanced prediction interface
├── pages/
│   ├── Index.tsx                     # Dashboard with race overview (animated)
│   ├── DriverPredictor.tsx           # Individual driver predictions (animated)
│   ├── RacePredictor.tsx             # Full race grid predictions (animated)
│   ├── TelemetryAnalyzer.tsx         # Advanced telemetry analysis (animated)
│   ├── StrategySimulator.tsx         # Race strategy optimization (animated)
│   └── NotFound.tsx                  # Enhanced 404 page (animated)
├── hooks/
│   ├── useApiCall.ts                 # Enhanced API call hook with loading states, error handling, and retry logic
│   ├── useGraphCustomization.ts      # Graph styling state management
│   └── useTelemetryData.ts           # Telemetry API integration
└── lib/
    ├── api.ts                        # API integration utilities
    └── telemetry-utils.ts            # Telemetry data processing
```

## ✨ Animation System

### Custom Animation Components

#### **AnimatedPageWrapper**
Reusable component for smooth page entrance animations:

```typescript
<AnimatedPageWrapper delay={300}>
  <div className="page-content">
    {/* Page content with fade-in animation */}
  </div>
</AnimatedPageWrapper>
```

**Features:**
- Configurable delay timing for progressive loading
- Smooth translate-y and opacity transitions
- 1-second duration for professional feel
- Automatic trigger on component mount

#### **StaggeredAnimation**
Creates sequential animations for lists and grids:

```typescript
<StaggeredAnimation
  delay={500}
  staggerDelay={150}
  className="grid grid-cols-3 gap-4"
>
  {items.map((item, index) => (
    <Card key={index}>
      {/* Each card animates with increasing delay */}
    </Card>
  ))}
</StaggeredAnimation>
```

**Features:**
- Individual item delays for visual hierarchy
- Customizable stagger timing between items
- Support for any grid or list layout
- Smooth translate-y and opacity effects

### Page-Specific Animations

#### **Animated Backgrounds**
Each page features unique floating orb animations:

```typescript
{/* Animated Background Effects */}
<div className="fixed inset-0 overflow-hidden pointer-events-none">
  <div className="absolute -top-4 -right-4 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
  <div className="absolute top-1/2 -left-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
  <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-green-500/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
</div>
```

**Color Themes by Page:**
- **Index**: Red, Blue, Purple orbs for F1 branding
- **Driver Predictor**: Red, Blue, Green for trophy/performance theme
- **Race Predictor**: Blue, Purple, Green for race/strategy theme
- **Telemetry Analyzer**: Green, Blue, Purple for data/analysis theme
- **Strategy Simulator**: Purple, Yellow, Blue for strategy/optimization theme
- **NotFound**: Red, Yellow, Orange for warning/alert theme

#### **Progressive Loading**
Content appears in sequence for better UX:

```typescript
const [isVisible, setIsVisible] = useState(false);

useEffect(() => {
  setIsVisible(true);
}, []);

// Header (100ms delay)
<AnimatedPageWrapper delay={100}>
  <header>{/* Header content */}</header>
</AnimatedPageWrapper>

// Controls (600ms delay)
<AnimatedPageWrapper delay={600}>
  <div className="controls">{/* Control panels */}</div>
</AnimatedPageWrapper>

// Results (800ms delay)
<AnimatedPageWrapper delay={800}>
  <div className="results">{/* Results display */}</div>
</AnimatedPageWrapper>
```

### Interactive Animations

#### **Hover Effects**
Enhanced hover states with scaling and shadow effects:

```css
.hover\\:scale-105:hover {
  transform: scale(1.05);
}

.hover\\:shadow-2xl:hover {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.hover\\:shadow-red-500\\/25:hover {
  box-shadow: 0 25px 50px -12px rgba(239, 68, 68, 0.25);
}
```

#### **Button Animations**
Professional button interactions with smooth transitions:

```typescript
<Button className="transform transition-all duration-300 hover:scale-105 hover:shadow-xl">
  <span className="relative flex items-center">
    Get Started
    <ChevronRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
  </span>
</Button>
```

### Performance Optimizations

#### **Animation Performance**
- **CSS Transforms**: Hardware-accelerated animations using transform and opacity
- **Reduced Motion**: Respects user preference for reduced motion
- **Efficient Triggers**: useEffect hooks with proper cleanup
- **Stagger Optimization**: Calculated delays prevent animation overlap

#### **Memory Management**
```typescript
useEffect(() => {
  const timer = setTimeout(() => {
    setIsVisible(true);
  }, delay);

  // Cleanup timer to prevent memory leaks
  return () => clearTimeout(timer);
}, [delay]);
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

- **Red Bull Racing**: Max Verstappen (VER) #1, Sergio Pérez (PER) #11
- **Ferrari**: Lewis Hamilton (HAM) #44 ⭐, Charles Leclerc (LEC) #16
- **Mercedes**: George Russell (RUS) #63, Kimi Antonelli (ANT) #12 ⭐
- **McLaren**: Lando Norris (NOR) #4, Oscar Piastri (PIA) #81
- **Aston Martin**: Fernando Alonso (ALO) #14, Lance Stroll (STR) #18
- **Alpine**: Pierre Gasly (GAS) #10, Esteban Ocon (OCO) #31
- **RB**: Yuki Tsunoda (TSU) #22, Liam Lawson (LAW) #30 ⭐
- **Williams**: Carlos Sainz (SAI) #55 ⭐, Alexander Albon (ALB) #23
- **Haas**: Nico Hülkenberg (HUL) #27, Oliver Bearman (BEA) #38 ⭐
- **Kick Sauber**: Gabriel Bortoleto (BOR) #5 ⭐, Isack Hadjar (HAD) #6 ⭐

⭐ = New for 2025 season

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

### Enhanced F1 Dashboard
- ✅ **Real-time 2025 F1 Championship** with live standings showing Piastri's McLaren title lead
- ✅ **Interactive Performance Trends** with Last 5/All Races toggle and multi-driver selection
- ✅ **Weather Impact Analysis** with driver performance comparison across weather conditions
- ✅ **Championship Pressure Visualization** showing mathematical championship possibilities
- ✅ **Responsive Card Layout** with perfectly balanced sizing and professional aesthetics
- ✅ **Enhanced Error Handling** with loading states, error displays, and retry mechanisms

### Advanced Telemetry Visualization
- ✅ **Multi-variable overlap graphs** with 6 telemetry variables
- ✅ **Customizable graph UI** with 4 chart types and color schemes
- ✅ **Session type filters** supporting all F1 session formats
- ✅ **Interactive controls** with zoom, pan, and variable toggles
- ✅ **Professional aesthetics** with F1-inspired design and smooth animations

### Professional Animation System
- ✅ **Custom Animation Components** with AnimatedPageWrapper and StaggeredAnimation
- ✅ **Page-Specific Themes** with unique color-coded floating background orbs
- ✅ **Progressive Loading** with carefully timed content appearance
- ✅ **Interactive Hover Effects** with scaling and shadow animations
- ✅ **Performance Optimized** using hardware-accelerated CSS transforms

### Production-Ready Architecture
- ✅ **FastF1 integration** with real telemetry data from 2024-2025
- ✅ **FastF1 cache optimization** with automatic initialization and error handling
- ✅ **Ensemble ML models** with XGBoost + Random Forest + Neural Networks
- ✅ **Enhanced API architecture** with comprehensive FastF1 championship service
- ✅ **Multi-platform deployment** support for various cloud providers

### Data-Driven Intelligence
- ✅ **718+ race records** from complete 2024-2025 seasons with enhanced ML models
- ✅ **Realistic F1 modeling** with 70% car, 30% driver balance and advanced feature engineering
- ✅ **Advanced weather system** with realistic driver-specific weather performance data
- ✅ **Driver-specific skills** modeling wet weather expertise and momentum trends
- ✅ **Enhanced confidence scoring** with ensemble model variance analysis and Optuna optimization

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for F1 fans by combining real data science, professional telemetry analysis, and modern web technology.**