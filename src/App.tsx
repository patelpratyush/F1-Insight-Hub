
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Index from "./pages/Index";
import DriverPredictor from "./pages/DriverPredictor";
import RacePredictor from "./pages/RacePredictor";
import TelemetryAnalyzer from "./pages/TelemetryAnalyzer";
import StrategySimulator from "./pages/StrategySimulator";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/predictor" element={<DriverPredictor />} />
            <Route path="/race-predictor" element={<RacePredictor />} />
            <Route path="/telemetry" element={<TelemetryAnalyzer />} />
            <Route path="/strategy" element={<StrategySimulator />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
