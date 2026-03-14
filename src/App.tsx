
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import Layout from "./components/Layout";
import LoadingSpinner from "./components/ui/loading-spinner";

const Index = lazy(() => import("./pages/Index"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const DriverPredictor = lazy(() => import("./pages/DriverPredictor"));
const RacePredictor = lazy(() => import("./pages/RacePredictor"));
const TelemetryAnalyzer = lazy(() => import("./pages/TelemetryAnalyzer"));
const StrategySimulator = lazy(() => import("./pages/StrategySimulator"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Layout>
          <Suspense
            fallback={
              <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <LoadingSpinner size="lg" />
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/predictor" element={<DriverPredictor />} />
              <Route path="/race-predictor" element={<RacePredictor />} />
              <Route path="/telemetry" element={<TelemetryAnalyzer />} />
              <Route path="/strategy" element={<StrategySimulator />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </Layout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
