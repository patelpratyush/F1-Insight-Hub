#!/usr/bin/env python3
"""
Gemini AI-Powered F1 Strategy Optimization Service
Uses Google's Gemini API for intelligent race strategy recommendations
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import google.generativeai as genai
from services.strategy_simulation_service import F1StrategySimulator, StrategyResult

logger = logging.getLogger(__name__)

@dataclass
class GeminiOptimizationResult:
    """Enhanced optimization result with AI insights"""
    optimal_strategy: str
    strategy_result: StrategyResult
    ai_reasoning: str
    alternative_strategies: List[Dict]
    confidence_score: float
    risk_assessment: str
    contextual_insights: List[str]
    weather_specific_advice: str

class GeminiF1StrategyOptimizer:
    """AI-powered F1 strategy optimizer using Google Gemini"""
    
    def __init__(self, api_key: str = None):
        # Initialize Gemini API
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize traditional strategy simulator for performance data
        self.strategy_simulator = F1StrategySimulator()
        
        logger.info("Gemini F1 Strategy Optimizer initialized successfully")
    
    def optimize_strategy(
        self,
        driver: str,
        track: str,
        weather: str,
        target_metric: str = "position",
        risk_tolerance: float = 0.5,
        prioritize_consistency: bool = True,
        qualifying_position: int = 10,
        safety_car_probability: float = 30.0,
        team: str = "Ferrari",
        temperature: float = 25.0
    ) -> GeminiOptimizationResult:
        """
        Use Gemini AI to find optimal F1 race strategy
        
        Args:
            driver: Driver code (e.g., 'HAM')
            track: Track name
            weather: Weather condition
            target_metric: 'position', 'time', or 'points'
            risk_tolerance: 0.0 (conservative) to 1.0 (aggressive)
            prioritize_consistency: Whether to favor reliable results
            qualifying_position: Starting grid position
            safety_car_probability: Safety car likelihood (0-100)
            team: Team name
            temperature: Track temperature
        
        Returns:
            GeminiOptimizationResult with AI-powered recommendations
        """
        logger.info(f"Starting Gemini optimization for {driver} at {track}")
        
        try:
            # Step 1: Get candidate strategies from traditional simulator
            candidate_strategies = self._get_candidate_strategies(weather)
            strategy_results = {}
            
            # Simulate each candidate strategy
            for strategy in candidate_strategies:
                try:
                    result = self.strategy_simulator.simulate_race_strategy(
                        driver=driver,
                        track=track,
                        weather=weather,
                        tire_strategy=strategy,
                        safety_car_probability=safety_car_probability,
                        qualifying_position=qualifying_position,
                        team=team,
                        temperature=temperature
                    )
                    strategy_results[strategy] = result
                except Exception as e:
                    logger.warning(f"Failed to simulate strategy {strategy}: {e}")
                    continue
            
            if not strategy_results:
                raise Exception("No valid strategy simulations available")
            
            # Step 2: Prepare context for Gemini AI
            context = self._prepare_ai_context(
                driver=driver,
                track=track,
                weather=weather,
                target_metric=target_metric,
                risk_tolerance=risk_tolerance,
                prioritize_consistency=prioritize_consistency,
                qualifying_position=qualifying_position,
                safety_car_probability=safety_car_probability,
                team=team,
                temperature=temperature,
                strategy_results=strategy_results
            )
            
            # Step 3: Get AI recommendation
            ai_response = self._query_gemini(context)
            
            # Step 4: Parse AI response and select optimal strategy
            optimal_result = self._parse_ai_response(ai_response, strategy_results)
            
            logger.info(f"Gemini optimization completed: {optimal_result.optimal_strategy}")
            return optimal_result
            
        except Exception as e:
            logger.error(f"Gemini optimization failed: {e}")
            # Fallback to traditional optimization
            return self._fallback_optimization(
                driver, track, weather, strategy_results if 'strategy_results' in locals() else {}
            )
    
    def _get_candidate_strategies(self, weather: str) -> List[str]:
        """Get relevant strategy candidates based on weather"""
        base_strategies = [
            "Soft-Medium-Hard",
            "Medium-Hard-Hard",
            "Soft-Soft-Medium",
            "Medium-Medium-Hard",
            "Hard-Hard-Medium",
            "Soft-Hard",
            "Medium-Hard"
        ]
        
        if weather in ['light_rain', 'mixed']:
            wet_strategies = [
                "Soft-Medium-Intermediate",
                "Medium-Intermediate-Hard",
                "Intermediate-Medium-Hard",
                "Soft-Intermediate"
            ]
            return base_strategies + wet_strategies
        elif weather == 'heavy_rain':
            return [
                "Wet-Intermediate",
                "Intermediate-Wet",
                "Wet-Wet-Intermediate",
                "Intermediate-Intermediate"
            ]
        else:
            return base_strategies
    
    def _prepare_ai_context(
        self,
        driver: str,
        track: str,
        weather: str,
        target_metric: str,
        risk_tolerance: float,
        prioritize_consistency: bool,
        qualifying_position: int,
        safety_car_probability: float,
        team: str,
        temperature: float,
        strategy_results: Dict[str, StrategyResult]
    ) -> str:
        """Prepare comprehensive context for Gemini AI"""
        
        # Convert strategy results to readable format
        strategies_summary = []
        for strategy, result in strategy_results.items():
            strategies_summary.append({
                "strategy": strategy,
                "predicted_position": result.predicted_position,
                "total_time": result.total_race_time,
                "efficiency": result.efficiency_score,
                "confidence": result.confidence
            })
        
        context = f"""
You are an expert Formula 1 race strategist with deep knowledge of tire management, pit stop timing, and race dynamics. 
Analyze the following race scenario and recommend the optimal strategy.

RACE CONTEXT:
- Driver: {driver} ({team})
- Circuit: {track}
- Weather: {weather} (Temperature: {temperature}°C)
- Starting Position: P{qualifying_position}
- Safety Car Probability: {safety_car_probability}%

OPTIMIZATION PARAMETERS:
- Target Metric: {target_metric} (optimize for best finishing position, fastest time, or maximum points)
- Risk Tolerance: {risk_tolerance:.1f} (0.0 = very conservative, 1.0 = very aggressive)
- Prioritize Consistency: {prioritize_consistency}

SIMULATED STRATEGIES PERFORMANCE:
{json.dumps(strategies_summary, indent=2)}

TRACK-SPECIFIC CONSIDERATIONS:
Please consider the following track characteristics for {track}:
- Overtaking difficulty and DRS zones
- Tire degradation patterns
- Historical safety car frequency
- Weather impact on performance
- Pit stop loss time

ANALYSIS REQUIRED:
1. Identify the optimal strategy considering all factors
2. Explain your reasoning with specific F1 tactical knowledge
3. Assess risks and benefits of the chosen strategy
4. Provide 2-3 alternative strategies with brief explanations
5. Give weather-specific tactical advice
6. Consider the driver's strengths and team's pit stop performance

Please respond with a JSON object containing:
{{
    "optimal_strategy": "strategy_name",
    "reasoning": "detailed_explanation",
    "confidence_score": 0.85,
    "risk_assessment": "low/medium/high risk with explanation",
    "alternatives": [
        {{"strategy": "name", "reason": "why this could work"}},
        {{"strategy": "name", "reason": "why this could work"}}
    ],
    "insights": [
        "tactical insight 1",
        "tactical insight 2",
        "tactical insight 3"
    ],
    "weather_advice": "specific weather-related recommendations"
}}
"""
        return context
    
    def _query_gemini(self, context: str) -> Dict:
        """Query Gemini API with race context"""
        try:
            # Configure generation parameters for JSON response
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent responses
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
            
            response = self.model.generate_content(
                context,
                generation_config=generation_config
            )
            
            # Parse JSON response
            ai_response = json.loads(response.text)
            logger.info("Successfully received Gemini AI response")
            
            return ai_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Raw response: {response.text}")
            raise Exception("Invalid JSON response from Gemini AI")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise Exception(f"Failed to query Gemini AI: {str(e)}")
    
    def _parse_ai_response(
        self,
        ai_response: Dict,
        strategy_results: Dict[str, StrategyResult]
    ) -> GeminiOptimizationResult:
        """Parse Gemini response and create optimization result"""
        
        optimal_strategy_name = ai_response.get("optimal_strategy", "Medium-Hard")
        
        # Get the corresponding simulation result
        if optimal_strategy_name in strategy_results:
            optimal_result = strategy_results[optimal_strategy_name]
        else:
            # Fallback to best performing strategy from simulations
            optimal_result = min(strategy_results.values(), key=lambda x: x.predicted_position)
            optimal_strategy_name = next(
                strategy for strategy, result in strategy_results.items() 
                if result == optimal_result
            )
        
        # Format alternative strategies
        alternatives = []
        for alt in ai_response.get("alternatives", []):
            if alt.get("strategy") in strategy_results:
                alt_result = strategy_results[alt["strategy"]]
                alternatives.append({
                    "strategy": alt["strategy"],
                    "predicted_position": alt_result.predicted_position,
                    "total_race_time": alt_result.total_race_time,
                    "efficiency_score": alt_result.efficiency_score,
                    "confidence": alt_result.confidence,
                    "reason": alt.get("reason", "Alternative strategy option")
                })
        
        return GeminiOptimizationResult(
            optimal_strategy=optimal_strategy_name,
            strategy_result=optimal_result,
            ai_reasoning=ai_response.get("reasoning", "AI-optimized strategy selection"),
            alternative_strategies=alternatives,
            confidence_score=ai_response.get("confidence_score", 0.8),
            risk_assessment=ai_response.get("risk_assessment", "Medium risk"),
            contextual_insights=ai_response.get("insights", []),
            weather_specific_advice=ai_response.get("weather_advice", "Standard weather considerations apply")
        )
    
    def _fallback_optimization(
        self,
        driver: str,
        track: str,
        weather: str,
        strategy_results: Dict[str, StrategyResult]
    ) -> GeminiOptimizationResult:
        """Fallback to traditional optimization if Gemini fails"""
        logger.warning("Using fallback optimization due to Gemini API failure")
        
        if not strategy_results:
            # Run basic simulation if no results available
            fallback_strategy = "Medium-Hard"
            try:
                result = self.strategy_simulator.simulate_race_strategy(
                    driver=driver,
                    track=track,
                    weather=weather,
                    tire_strategy=fallback_strategy,
                    safety_car_probability=30.0,
                    qualifying_position=10
                )
            except:
                # Create minimal fallback result
                from services.strategy_simulation_service import StrategyResult
                result = StrategyResult(
                    strategy_id="fallback",
                    driver=driver,
                    track=track,
                    weather=weather,
                    total_race_time="1:30:00.000",
                    total_seconds=5400.0,
                    predicted_position=10,
                    confidence=0.7,
                    efficiency_score=70.0,
                    stints=[],
                    pit_stops=[],
                    timeline=[],
                    optimization_metrics={},
                    risk_analysis={}
                )
        else:
            # Use best result from available simulations
            result = min(strategy_results.values(), key=lambda x: x.predicted_position)
            fallback_strategy = next(
                strategy for strategy, res in strategy_results.items() if res == result
            )
        
        return GeminiOptimizationResult(
            optimal_strategy=fallback_strategy,
            strategy_result=result,
            ai_reasoning="Fallback optimization used due to AI service unavailability",
            alternative_strategies=[],
            confidence_score=0.7,
            risk_assessment="Medium risk - standard strategy recommendation",
            contextual_insights=[
                "Using traditional optimization method",
                "Strategy based on simulation performance only",
                "AI insights unavailable - contact support if this persists"
            ],
            weather_specific_advice="Standard tire strategy for current conditions"
        )