import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  ChevronRight,
  Flag,
  Gauge,
  Globe,
  Timer,
  TrendingUp,
  Trophy,
  Users,
  Zap,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => navigate("/dashboard");

  return (
    <div className="bg-black text-white font-sans w-full min-h-screen overflow-x-hidden relative selection:bg-red-600/30 selection:text-white">
      {/* Fixed High-Quality Video Background - NO BLUR, NO BLEND MODES */}
      <div className="fixed inset-0 w-full h-full z-0 bg-black">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover"
        >
          <source src="/hero-bg.mp4" type="video/mp4" />
        </video>
        {/* Simple dark overlay to preserve readability without blur */}
        <div className="absolute inset-0 bg-black/50"></div>
        {/* Falloff gradient for text contrast at the bottom */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
      </div>

      {/* Hero Section */}
      <div className="relative w-full min-h-screen flex flex-col items-center justify-center overflow-hidden z-10 pt-20">
        <div className="w-full max-w-screen-2xl mx-auto px-[32px] md:px-[64px] flex flex-col items-center text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-red-500/30 bg-[#1a0505] mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-sm font-medium text-red-100 tracking-wider uppercase">
              Live Telemetry Active
            </span>
          </motion.div>

          <motion.h1
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1, delay: 0.2, type: "spring" }}
            className="text-[56px] md:text-[100px] lg:text-[140px] font-black tracking-tighter text-white leading-[0.85] mb-8 pb-4"
          >
            FEEL THE SPEED
          </motion.h1>

          <motion.p
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1, delay: 0.4, type: "spring" }}
            className="text-lg md:text-2xl font-light text-white/80 max-w-2xl leading-relaxed mb-12"
          >
            The pinnacle of Formula 1 analytics. Powered by massive datasets,
            machine learning models, and real-time telemetry to give you the
            ultimate racing edge.
          </motion.p>

          <motion.div
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1, delay: 0.6, type: "spring" }}
            className="flex flex-col sm:flex-row gap-6 items-center"
          >
            <Button
              size="lg"
              onClick={handleGetStarted}
              className="bg-red-600 text-white hover:bg-red-500 px-12 py-8 text-xl font-bold rounded-full transition-all duration-300 hover:scale-[1.05] relative overflow-hidden shadow-lg border border-transparent"
            >
              <div className="absolute inset-0 bg-white/20 translate-y-[100%] group-hover:translate-y-[0%] transition-transform duration-500 ease-out rounded-full"></div>
              <span className="relative flex items-center gap-2">
                Start Engine{" "}
                <Zap className="w-5 h-5 group-hover:fill-white transition-colors" />
              </span>
            </Button>

            <Link
              to="/predictor"
              className="group flex items-center gap-4 text-white/70 hover:text-white transition-colors px-6 py-4"
            >
              <div className="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center group-hover:border-white/60 transition-colors bg-white/5">
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </div>
              <span className="font-semibold tracking-wide text-lg uppercase">
                See It In Action
              </span>
            </Link>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2, duration: 1 }}
          className="absolute bottom-12 left-0 right-0 mx-auto w-fit flex flex-col items-center gap-2 opacity-50"
        >
          <span className="text-xs uppercase tracking-[0.3em] font-medium text-white/50">
            Scroll
          </span>
          <div className="w-[1px] h-16 bg-gradient-to-b from-white/50 to-transparent"></div>
        </motion.div>
      </div>

      {/* Modern Bento Grid Features Section */}
      <div
        id="features"
        className="w-full px-[16px] md:px-[64px] py-32 relative z-20 bg-black/40 border-t border-white/10"
      >
        <div className="max-w-screen-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="mb-20"
          >
            <h2 className="text-3xl md:text-6xl font-black text-white mb-6 tracking-tighter">
              PRECISION <span className="text-red-500">ENGINEERED</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl font-light">
              Experience the paddock from the pit wall. Four specialized modules
              designed for absolute clarity.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 auto-rows-[300px]">
            {/* Large Feature 1 - Spans 2 cols, 2 rows */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, type: "spring" }}
              className="md:col-span-2 md:row-span-2"
            >
              <Link to="/telemetry" className="group block h-full">
                <div className="h-full bg-black/60 border border-white/10 rounded-[40px] p-10 flex flex-col justify-between overflow-hidden hover:bg-black/80 hover:border-red-500/50 transition-all duration-500 relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-red-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                  {/* Decorative abstract elements */}
                  <div className="absolute top-10 right-10 flex items-end gap-1 opacity-20 group-hover:opacity-60 transition-opacity duration-500">
                    <div className="w-2 h-16 bg-white rounded-full"></div>
                    <div className="w-2 h-8 bg-white rounded-full"></div>
                    <div className="w-2 h-24 bg-red-500 rounded-full"></div>
                    <div className="w-2 h-12 bg-white rounded-full"></div>
                  </div>

                  <div className="relative z-10">
                    <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-8 border border-red-500/30 group-hover:scale-110 transition-transform duration-500">
                      <Activity className="w-8 h-8 text-red-500" />
                    </div>
                  </div>
                  <div className="relative z-10 w-3/4">
                    <h3 className="text-4xl font-bold mb-4 tracking-tight">
                      Live Telemetry
                    </h3>
                    <p className="text-white/60 text-lg font-light leading-relaxed mb-6">
                      Analyze down to the microsecond. Throttle, braking, gear
                      shifts, and G-forces mapped perfectly for driver
                      comparisons.
                    </p>
                    <div className="inline-flex items-center gap-2 text-red-400 font-medium">
                      Explore Analyzer{" "}
                      <ChevronRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>

            {/* Feature 2 - Small */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.1, type: "spring" }}
              className="md:col-span-1 lg:col-span-2"
            >
              <Link to="/predictor" className="group block h-full">
                <div className="h-full bg-black/60 border border-white/10 rounded-[40px] p-10 flex flex-col justify-between hover:bg-black/80 hover:border-white/30 transition-all duration-500 relative overflow-hidden">
                  <div className="relative z-10 flex justify-between items-start">
                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:bg-white/10 transition-colors">
                      <Trophy className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-6 h-6 text-white/30 group-hover:text-white group-hover:translate-x-2 transition-all" />
                  </div>
                  <div className="relative z-10">
                    <h3 className="text-2xl font-bold mb-2 tracking-tight">
                      Driver Performance
                    </h3>
                    <p className="text-white/60 font-light">
                      Machine learning predictions for track-specific pace and
                      podium probability.
                    </p>
                  </div>
                </div>
              </Link>
            </motion.div>

            {/* Feature 3 - Tall */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.2, type: "spring" }}
              className="md:col-span-1 md:row-span-2 lg:col-span-1 lg:row-span-2"
            >
              <Link to="/race-predictor" className="group block h-full">
                <div className="h-full bg-red-950/40 border border-red-500/20 rounded-[40px] p-8 flex flex-col items-center text-center justify-center hover:bg-red-950/60 hover:border-red-500/60 transition-all duration-500 relative overflow-hidden group">
                  <div className="w-24 h-24 rounded-full bg-red-600 flex items-center justify-center mb-8 border border-red-500/50 group-hover:bg-red-500 transition-all duration-700 relative z-10">
                    <Gauge className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-3xl font-bold mb-4 tracking-tight relative z-10">
                    Race Result Forecast
                  </h3>
                  <p className="text-red-200/60 font-light mb-8 relative z-10">
                    Complete grid predictions calculating weather, degradation,
                    and historical confidence scores.
                  </p>
                  <div className="w-full h-[1px] bg-red-500/30 relative z-10"></div>
                </div>
              </Link>
            </motion.div>

            {/* Feature 4 - Medium */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.3, type: "spring" }}
              className="md:col-span-2 lg:col-span-1"
            >
              <Link to="/strategy" className="group block h-full">
                <div className="h-full bg-black/60 border border-white/10 rounded-[40px] p-10 flex flex-col justify-between hover:bg-black/80 hover:border-white/30 transition-all duration-500 relative overflow-hidden">
                  <div className="relative z-10 flex justify-between items-start">
                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:bg-white/10 transition-colors">
                      <Timer className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-6 h-6 text-white/30 group-hover:text-white group-hover:translate-x-2 transition-all" />
                  </div>
                  <div className="relative z-10">
                    <h3 className="text-2xl font-bold mb-2 tracking-tight">
                      Pit Strategy
                    </h3>
                    <p className="text-white/60 font-light">
                      Simulate overcuts, tire degradation offsets, and safety
                      car windows.
                    </p>
                  </div>
                </div>
              </Link>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Trust & Data Section - Minimalist approach */}
      <div
        id="stats"
        className="w-full relative z-20 overflow-hidden border-t border-white/5 bg-black/50"
      >
        <div className="max-w-screen-2xl mx-auto px-[32px] md:px-[64px] py-32 flex flex-col lg:flex-row items-center justify-between gap-16">
          <div className="flex-1">
            <h2 className="text-4xl md:text-6xl font-black mb-6 tracking-tighter">
              DATA IS <br />
              <span className="text-red-500">KING.</span>
            </h2>
            <p className="text-xl text-white/60 max-w-lg font-light leading-relaxed">
              We process millions of telemetry data points per second during a
              race weekend. Built on robust APIs delivering sub-second accuracy.
            </p>
          </div>

          <div className="flex-1 grid grid-cols-2 gap-8 w-full">
            {[
              { value: "20+", label: "Seasons of Data", icon: Users },
              { value: "400+", label: "Grand Prix", icon: Trophy },
              { value: "0.1s", label: "Latency", icon: Zap },
              { value: "100M+", label: "Data Points", icon: BarChart3 },
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="group border border-white/5 rounded-[32px] p-8 bg-black/40 hover:bg-black/60 hover:border-red-500/30 transition-colors"
              >
                <stat.icon className="w-6 h-6 text-red-500 mb-6 opacity-50 group-hover:opacity-100 group-hover:scale-110 transition-all" />
                <div className="text-4xl md:text-5xl font-black tracking-tighter mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-white/40 uppercase tracking-widest font-bold font-mono">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer CTA */}
      <div className="relative z-20 py-32 px-[32px] border-t border-white/5 text-center bg-black/60">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto"
        >
          <h2 className="text-5xl md:text-7xl font-black mb-8 tracking-tighter uppercase">
            Ready to dive in?
          </h2>
          <Button
            size="lg"
            onClick={handleGetStarted}
            className="bg-white text-black hover:bg-red-600 hover:text-white px-12 py-8 text-xl font-bold rounded-full transition-all duration-500 hover:scale-[1.05]"
          >
            Launch The Dashboard
          </Button>
        </motion.div>
      </div>
    </div>
  );
};

export default Index;
