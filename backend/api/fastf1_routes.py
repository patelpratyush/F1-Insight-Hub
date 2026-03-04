#!/usr/bin/env python3
"""
FastAPI routes for F1 data - powered by CacheManager (Jolpica API).
All routes now use dynamic year and cached data instead of hardcoded values.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime, timezone

from services.cache_manager import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/f1", tags=["F1 Data"])


@router.get("/standings/{year}")
async def get_championship_standings(
    year: int,
    limit: Optional[int] = Query(20, description="Maximum number of drivers to return"),
):
    """Get driver championship standings"""
    try:
        await cache_manager.ensure_year_loaded(year)
        standings = cache_manager.get_driver_standings(year)

        if not standings:
            raise HTTPException(status_code=404, detail=f"No standings data found for {year}")

        if limit:
            standings = standings[:limit]

        return {
            "success": True,
            "year": year,
            "data": standings,
            "total_drivers": len(standings),
            "data_source": "Jolpica F1 API",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching standings for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch standings: {str(e)}")


@router.get("/latest-race/{year}")
async def get_latest_race_results(year: int):
    """Get results from the most recent completed race"""
    try:
        await cache_manager.ensure_year_loaded(year)
        latest = cache_manager.get_latest_race(year)

        if not latest:
            raise HTTPException(status_code=404, detail=f"No recent race data found for {year}")

        # Transform to match the expected frontend shape
        podium = []
        for dr in latest.get("results", [])[:3]:
            podium.append({
                "position": dr.get("position", 0),
                "driver": dr.get("code", ""),
                "name": dr.get("name", ""),
                "team": dr.get("team", ""),
                "time": dr.get("time", ""),
            })

        race_data = {
            "raceName": latest.get("raceName", ""),
            "date": latest.get("date", ""),
            "weather": "Dry",
            "temperature": 25,
            "podium": podium,
            "fastestLap": latest.get("fastestLap", {}),
            "totalLaps": latest.get("totalLaps", 0),
            "safetyCarPeriods": 0,
        }

        return {
            "success": True,
            "year": year,
            "race_data": race_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest race for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch race data: {str(e)}")


@router.get("/performance-trends/{year}")
async def get_performance_trends(
    year: int,
    races: Optional[int] = Query(6, description="Number of recent races to analyze"),
):
    """Get recent performance trends for top drivers"""
    try:
        await cache_manager.ensure_year_loaded(year)
        trends = cache_manager.get_performance_trends(year, all_races=False)

        if not trends:
            raise HTTPException(status_code=404, detail=f"No performance data found for {year}")

        return {
            "success": True,
            "year": year,
            "races_analyzed": len(trends),
            "performance_data": trends,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance trends for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance trends: {str(e)}")


@router.get("/weather-analysis/{year}")
async def get_weather_performance_analysis(year: int):
    """Get driver performance analysis by weather conditions.
    This still uses FastF1 session data since weather info requires session loading.
    Falls back gracefully if FastF1 service is unavailable.
    """
    try:
        # Weather analysis genuinely needs FastF1 session data
        try:
            from services.fastf1_service import fastf1_service
            weather_data = fastf1_service.get_driver_weather_performance(year)
        except Exception:
            weather_data = []

        if not weather_data:
            raise HTTPException(status_code=404, detail=f"No weather analysis data found for {year}")

        return {
            "success": True,
            "year": year,
            "weather_analysis": weather_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather analysis for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather analysis: {str(e)}")


@router.get("/upcoming-race/{year}")
async def get_upcoming_race(year: int):
    """Get information about the next upcoming race"""
    try:
        await cache_manager.ensure_year_loaded(year)
        upcoming_race = cache_manager.get_next_race(year)

        if not upcoming_race:
            return {
                "success": True,
                "year": year,
                "upcoming_race": None,
                "message": "No upcoming races found for this year",
            }

        return {
            "success": True,
            "year": year,
            "upcoming_race": upcoming_race,
        }

    except Exception as e:
        logger.error(f"Error fetching upcoming race for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming race: {str(e)}")


@router.get("/season-stats/{year}")
async def get_season_statistics(year: int):
    """Get general statistics about the season"""
    try:
        await cache_manager.ensure_year_loaded(year)
        stats = cache_manager.get_season_statistics(year)

        return {
            "success": True,
            "year": year,
            "season_statistics": stats,
        }

    except Exception as e:
        logger.error(f"Error fetching season stats for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch season statistics: {str(e)}")


@router.get("/dashboard-trends/{year}")
async def get_dashboard_performance_trends(year: int, all_races: bool = False):
    """Get performance trends data for dashboard with option for all races or last 5"""
    try:
        await cache_manager.ensure_year_loaded(year)
        logger.info(f"Fetching dashboard performance trends (all_races={all_races}) for {year}")

        performance_trends = cache_manager.get_performance_trends(year, all_races=all_races)

        data_year = year
        if not performance_trends:
            data_year = year - 1
            await cache_manager.ensure_year_loaded(data_year)
            performance_trends = cache_manager.get_performance_trends(data_year, all_races=all_races)

        return {
            "success": True,
            "year": year,
            "data_year": data_year,
            "all_races": all_races,
            "performance_trends": performance_trends,
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard performance trends for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance trends: {str(e)}")


@router.get("/dashboard/{year}")
async def get_dashboard_data(year: int):
    """Get comprehensive dashboard data.
    When the requested year has no race data yet (pre-season), historical data
    (standings, results, trends) is sourced from the previous year while
    upcoming-race and schedule info still come from the requested year.
    """
    try:
        await cache_manager.ensure_year_loaded(year)
        logger.info(f"Fetching comprehensive dashboard data for {year}")

        standings = cache_manager.get_driver_standings(year)
        completed = cache_manager.get_completed_races(year)

        # If the requested year has no race data yet, pull historical data
        # from the previous year so the dashboard isn't empty.
        data_year = year
        if not standings and not completed:
            data_year = year - 1
            await cache_manager.ensure_year_loaded(data_year)
            standings = cache_manager.get_driver_standings(data_year)
            logger.info(f"No data for {year} yet, using {data_year} for historical data")

        latest_race = cache_manager.get_latest_race(data_year)
        performance_trends = cache_manager.get_performance_trends(data_year, all_races=False)

        # Upcoming race always comes from the requested (current) year
        upcoming_races = cache_manager.get_upcoming_races(year)
        upcoming_race = upcoming_races[0] if upcoming_races else None
        season_stats = cache_manager.get_season_statistics(year)

        latest_race_data = None
        if latest_race:
            podium = []
            for dr in latest_race.get("results", [])[:3]:
                podium.append({
                    "position": dr.get("position", 0),
                    "driver": dr.get("code", ""),
                    "name": dr.get("name", ""),
                    "team": dr.get("team", ""),
                    "time": dr.get("time", ""),
                })
            latest_race_data = {
                "raceName": latest_race.get("raceName", ""),
                "date": latest_race.get("date", ""),
                "weather": "Dry",
                "temperature": 25,
                "podium": podium,
                "fastestLap": latest_race.get("fastestLap", {}),
                "totalLaps": latest_race.get("totalLaps", 0),
                "safetyCarPeriods": 0,
            }

        weather_analysis = []
        try:
            from services.fastf1_service import fastf1_service
            weather_analysis = fastf1_service.get_driver_weather_performance(data_year)
        except Exception:
            pass

        return {
            "success": True,
            "year": year,
            "data_year": data_year,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data": {
                "championship_standings": standings if standings else [],
                "latest_race": latest_race_data,
                "performance_trends": performance_trends,
                "weather_analysis": weather_analysis,
                "upcoming_race": upcoming_race,
                "season_statistics": season_stats,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard data for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")


@router.get("/race-summaries/{year}")
async def get_race_summaries(year: int):
    """Get comprehensive summaries for all completed races"""
    try:
        await cache_manager.ensure_year_loaded(year)
        race_summaries = cache_manager.get_race_summaries(year)

        return {
            "success": True,
            "year": year,
            "total_races": len(race_summaries),
            "race_summaries": race_summaries,
            "data_source": "Jolpica F1 API",
        }

    except Exception as e:
        logger.error(f"Error fetching race summaries for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch race summaries: {str(e)}")


@router.get("/upcoming-races/{year}")
async def get_upcoming_races(year: int):
    """Get all upcoming races for the season"""
    try:
        await cache_manager.ensure_year_loaded(year)
        upcoming_races = cache_manager.get_upcoming_races(year)

        return {
            "success": True,
            "year": year,
            "total_upcoming": len(upcoming_races),
            "upcoming_races": upcoming_races,
            "data_source": "Jolpica F1 API",
        }

    except Exception as e:
        logger.error(f"Error fetching upcoming races for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming races: {str(e)}")


@router.get("/points-breakdown/{year}")
async def get_points_breakdown(year: int):
    """Get detailed points breakdown for each driver by race"""
    try:
        await cache_manager.ensure_year_loaded(year)
        points_breakdown = cache_manager.get_points_breakdown(year)

        return {
            "success": True,
            "year": year,
            "points_breakdown": points_breakdown,
            "data_source": "Jolpica F1 API",
        }

    except Exception as e:
        logger.error(f"Error fetching points breakdown for {year}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch points breakdown: {str(e)}")
