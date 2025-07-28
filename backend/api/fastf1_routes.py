#!/usr/bin/env python3
"""
FastAPI routes for FastF1 data integration
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from services.fastf1_service import fastf1_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f1", tags=["FastF1 Data"])

@router.get("/standings/{year}")
async def get_championship_standings(
    year: int,
    limit: Optional[int] = Query(20, description="Maximum number of drivers to return")
):
    """Get 2025 driver championship standings"""
    try:
        # Always use 2025 data regardless of year parameter
        standings = fastf1_service.get_current_season_standings()
        
        if not standings:
            raise HTTPException(status_code=404, detail=f"No standings data found for {year}")
        
        # Limit results if requested
        if limit:
            standings = standings[:limit]
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "standings": standings,
            "total_drivers": len(standings)
        }
        
    except Exception as e:
        logger.error(f"Error fetching standings for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch standings: {str(e)}")

@router.get("/latest-race/{year}")
async def get_latest_race_results(year: int):
    """Get results from the most recent completed race (2025)"""
    try:
        # Always use 2025 data
        race_data = fastf1_service.get_latest_race_results()
        
        if not race_data:
            raise HTTPException(status_code=404, detail=f"No recent race data found for {year}")
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "race_data": race_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching latest race for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch race data: {str(e)}")

@router.get("/performance-trends/{year}")
async def get_performance_trends(
    year: int,
    races: Optional[int] = Query(6, description="Number of recent races to analyze")
):
    """Get recent performance trends for top drivers (2025)"""
    try:
        # Always use 2025 data
        trends = fastf1_service.get_performance_trends()
        
        if not trends:
            raise HTTPException(status_code=404, detail=f"No performance data found for {year}")
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "races_analyzed": len(trends),
            "performance_data": trends
        }
        
    except Exception as e:
        logger.error(f"Error fetching performance trends for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance trends: {str(e)}")

@router.get("/weather-analysis/{year}")
async def get_weather_performance_analysis(year: int):
    """Get driver performance analysis by weather conditions (2025)"""
    try:
        # Always use 2025 data
        weather_data = fastf1_service.get_driver_weather_performance()
        
        if not weather_data:
            raise HTTPException(status_code=404, detail=f"No weather analysis data found for {year}")
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "weather_analysis": weather_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching weather analysis for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather analysis: {str(e)}")

@router.get("/upcoming-race/{year}")
async def get_upcoming_race(year: int):
    """Get information about the next upcoming race (2025)"""
    try:
        # Always use 2025 data
        upcoming_race = fastf1_service.get_upcoming_race()
        
        if not upcoming_race:
            return {
                "success": True,
                "year": 2025,  # Always return 2025
                "upcoming_race": None,
                "message": "No upcoming races found for this year"
            }
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "upcoming_race": upcoming_race
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming race for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming race: {str(e)}")

@router.get("/season-stats/{year}")
async def get_season_statistics(year: int):
    """Get general statistics about the 2025 season"""
    try:
        # Always use 2025 data
        stats = fastf1_service.get_season_statistics()
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "season_statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching season stats for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch season statistics: {str(e)}")

@router.get("/dashboard/{year}")
async def get_dashboard_data(year: int):
    """Get comprehensive dashboard data for 2025 season"""
    try:
        logger.info(f"Fetching comprehensive dashboard data for 2025")
        
        # Always fetch 2025 data regardless of year parameter
        standings = fastf1_service.get_current_season_standings()
        latest_race = fastf1_service.get_latest_race_results()
        performance_trends = fastf1_service.get_performance_trends()
        weather_analysis = fastf1_service.get_driver_weather_performance()
        upcoming_race = fastf1_service.get_upcoming_race()
        season_stats = fastf1_service.get_season_statistics()
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "last_updated": "2025-07-28T10:00:00Z",  # Updated timestamp for 2025
            "data": {
                "championship_standings": standings[:8] if standings else [],
                "latest_race": latest_race,
                "performance_trends": performance_trends,
                "weather_analysis": weather_analysis,
                "upcoming_race": upcoming_race,
                "season_statistics": season_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")