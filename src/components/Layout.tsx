import { Button } from "@/components/ui/button";
import { AnimatePresence, motion } from "framer-motion";
import {
    Activity,
    BarChart3,
    Flag,
    Home,
    Menu,
    TrendingUp,
    Trophy,
    X,
    Zap,
} from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

const Layout = ({ children }: { children: React.ReactNode }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
    { name: "Driver Predictor", href: "/predictor", icon: Trophy },
    { name: "Race Predictor", href: "/race-predictor", icon: TrendingUp },
    { name: "Telemetry", href: "/telemetry", icon: Activity },
    { name: "Strategy", href: "/strategy", icon: Zap },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div
      className={`min-h-screen flex flex-col ${isHome ? "bg-black" : "bg-[#0a0a0a]"}`}
    >
      {/* Floating Pill Navigation */}
      <motion.nav
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, type: "spring" }}
        className={`fixed top-4 md:top-6 left-0 right-0 mx-auto z-50 w-[95%] max-w-5xl bg-[#111111] border border-white/10 shadow-2xl ${
          isMenuOpen ? "rounded-3xl" : "rounded-full"
        } transition-all duration-300`}
      >
        <div className="flex items-center justify-between px-6 py-4 relative">
          {/* Logo */}
          <Link
            to="/"
            onClick={() => setIsMenuOpen(false)}
            className="flex items-center gap-3 group relative z-10 lg:w-[150px]"
          >
            <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-[0_0_15px_rgba(220,38,38,0.5)]">
              <Flag className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-wide text-white">
              Insight Hub
            </span>
          </Link>

          {/* Desktop Navigation (Absolute Centered) */}
          <div className="hidden lg:flex items-center justify-center gap-6 text-sm font-medium absolute left-1/2 -translate-x-1/2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`transition-colors ${
                  isActive(item.href)
                    ? "text-red-500 font-bold"
                    : "text-white/60 hover:text-white"
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          <div className="hidden lg:flex justify-end relative z-10 lg:w-[150px]">
            <Button
              onClick={() => {
                window.location.href = "/dashboard";
              }}
              className="bg-white text-black hover:bg-gray-200 rounded-full px-6 text-sm font-bold transition-all hover:scale-105"
            >
              Launch App
            </Button>
          </div>

          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden text-white hover:bg-white/10 rounded-full w-10 h-10 p-0"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Mobile Navigation Dropdown */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="lg:hidden overflow-hidden border-t border-white/5"
            >
              <div className="p-4 space-y-2 flex flex-col">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-4 px-4 py-3 rounded-2xl transition-all ${
                        isActive(item.href)
                          ? "bg-red-500/10 text-red-500 border border-red-500/20"
                          : "text-white/70 hover:bg-white/5 hover:text-white"
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="font-semibold">{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Main Content */}
      <main
        className={`flex-1 relative z-10 w-full ${!isHome ? "pt-32 pb-16 w-full" : ""}`}
      >
        {children}
      </main>

      {/* Footer */}
      {!isHome && (
        <footer className="bg-[#050505] border-t border-white/5 py-8 mt-auto z-10 relative">
          <div className="container mx-auto px-6 max-w-screen-2xl">
            <div className="flex flex-col md:flex-row items-center justify-between text-white/40 text-sm font-medium">
              <div className="flex items-center gap-2 mb-4 md:mb-0">
                <Flag className="w-4 h-4 text-red-500" />
                <span>&copy; {new Date().getFullYear()} F1 Insight Hub.</span>
              </div>
              <p>Powered by Fast-F1 & Advanced Machine Learning</p>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
};

export default Layout;
