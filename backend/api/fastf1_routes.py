#!/usr/bin/env python3
"""
FastAPI routes for FastF1 data integration
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime
from services.fastf1_service import fastf1_service
from services.fastf1_championship_service import fastf1_championship_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f1", tags=["FastF1 Data"])

@router.get("/standings/{year}")
async def get_championship_standings(
    year: int,
    limit: Optional[int] = Query(20, description="Maximum number of drivers to return")
):
    """Get 2025 driver championship standings"""
    try:
        # Use real FastF1 data for 2025 championship standings
        standings = fastf1_championship_service.get_2025_championship_standings()
        
        if not standings:
            raise HTTPException(status_code=404, detail=f"No standings data found for {year}")
        
        # Limit results if requested
        if limit:
            standings = standings[:limit]
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "data": standings,
            "total_drivers": len(standings),
            "data_source": "Real 2025 Race Results"
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
        # Always use 2025 data - use championship service for real trends
        trends = fastf1_championship_service.get_performance_trends()
        
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
        # Use real FastF1 data for upcoming races
        upcoming_races = fastf1_championship_service.get_upcoming_races()
        upcoming_race = upcoming_races[0] if upcoming_races else None
        
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

@router.get("/dashboard-trends/{year}")
async def get_dashboard_performance_trends(year: int, all_races: bool = False):
    """Get performance trends data for dashboard with option for all races or last 5"""
    try:
        logger.info(f"Fetching dashboard performance trends (all_races={all_races}) for 2025")
        
        if year == 2025:
            performance_trends = fastf1_championship_service.get_performance_trends(all_races=all_races)
        else:
            performance_trends = []
        
        return {
            "success": True,
            "year": 2025,
            "all_races": all_races,
            "performance_trends": performance_trends
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard performance trends for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance trends: {str(e)}")

@router.get("/dashboard/{year}")
async def get_dashboard_data(year: int):
    """Get comprehensive dashboard data for 2025 season"""
    try:
        logger.info(f"Fetching comprehensive dashboard data for 2025")
        
        # Use real FastF1 data for 2025 dashboard
        standings = fastf1_championship_service.get_2025_championship_standings()
        latest_race = fastf1_service.get_latest_race_results()
        performance_trends = fastf1_championship_service.get_performance_trends(all_races=False)  # Default to last 5
        weather_analysis = fastf1_service.get_driver_weather_performance()
        upcoming_races = fastf1_championship_service.get_upcoming_races()
        upcoming_race = upcoming_races[0] if upcoming_races else None
        season_stats = fastf1_service.get_season_statistics()
        
        return {
            "success": True,
            "year": 2025,  # Always return 2025
            "last_updated": "2025-07-28T10:00:00Z",  # Updated timestamp for 2025
            "data": {
                "championship_standings": standings if standings else [],
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

@router.get("/race-summaries/{year}")
async def get_race_summaries(year: int):
    """Get comprehensive summaries for all completed 2025 races"""
    try:
        if year == 2025:
            race_summaries = fastf1_championship_service.get_race_summaries()
        else:
            race_summaries = []  # Only support 2025 for now
        
        return {
            "success": True,
            "year": year,
            "total_races": len(race_summaries),
            "race_summaries": race_summaries,
            "data_source": "FastF1" if year == 2025 else "Not Available"
        }
        
    except Exception as e:
        logger.error(f"Error fetching race summaries for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch race summaries: {str(e)}")

@router.get("/upcoming-races/{year}")
async def get_upcoming_races(year: int):
    """Get all upcoming races for the 2025 season"""
    try:
        if year == 2025:
            upcoming_races = fastf1_championship_service.get_upcoming_races()
        else:
            upcoming_races = []  # Only support 2025 for now
        
        return {
            "success": True,
            "year": year,
            "total_upcoming": len(upcoming_races),
            "upcoming_races": upcoming_races,
            "data_source": "FastF1" if year == 2025 else "Not Available"
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming races for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming races: {str(e)}")

@router.get("/points-breakdown/{year}")
async def get_points_breakdown(year: int):
    """Get detailed points breakdown for each driver by race"""
    try:
        if year == 2025:
            points_breakdown = fastf1_championship_service.get_driver_points_breakdown()
        else:
            points_breakdown = {}  # Only support 2025 for now
        
        return {
            "success": True,
            "year": year,
            "points_breakdown": points_breakdown,
            "data_source": "FastF1" if year == 2025 else "Not Available"
        }
        
    except Exception as e:
        logger.error(f"Error fetching points breakdown for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch points breakdown: {str(e)}")