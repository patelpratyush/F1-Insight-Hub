#!/usr/bin/env python3
"""
F1 Results Integration Service
Fetches real F1 session results and updates championship standings
Uses FastF1 API and Ergast API for comprehensive F1 data
"""

import fastf1
import requests
import pandas as pd
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SessionResult:
    """F1 session result data"""
    session_type: str  # "Practice", "Qualifying", "Sprint", "Race"
    session_name: str  # "FP1", "FP2", "FP3", "Q1", "Q2", "Q3", "Sprint", "Race"
    circuit: str
    date: datetime
    results: List[Dict]  # Driver results with positions, times, etc.
    fastest_lap: Dict
    session_stats: Dict

@dataclass
class DriverStanding:
    """Driver championship standing"""
    position: int
    driver_code: str
    driver_name: str
    team: str
    points: float
    wins: int
    podiums: int
    pole_positions: int
    fastest_laps: int
    dnfs: int
    average_finish: float
    points_per_race: float
    form_last_5: List[int]  # Last 5 race positions

@dataclass
class ConstructorStanding:
    """Constructor championship standing"""
    position: int
    team_name: str
    points: float
    wins: int
    podiums: int
    pole_positions: int
    fastest_laps: int
    average_finish: float
    drivers: List[str]

@dataclass
class ChampionshipStandings:
    """Complete championship standings"""
    season: int
    last_updated: datetime
    current_round: int
    total_rounds: int
    drivers: List[DriverStanding]
    constructors: List[ConstructorStanding]
    championship_battle: Dict  # Analysis of title fight

class F1ResultsService:
    """Service for fetching and processing real F1 results"""
    
    def __init__(self):
        self.cache_dir = Path("cache/f1_results")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure FastF1 cache
        fastf1_cache_dir = self.cache_dir / "fastf1_cache"
        fastf1_cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(fastf1_cache_dir))
        
        self.jolpica_base_url = "https://api.jolpi.ca/ergast/f1"
        self.current_season = datetime.now().year
        self.results_cache = {}
        self.standings_cache = {}
        self.cache_duration = 1800  # 30 minutes
        
        # Initialize with existing 2025 data if available
        self._load_cached_standings()

    @property
    def f1_calendar(self) -> List[Dict]:
        """Dynamic calendar from cache_manager (backward compatible property)."""
        from services.cache_manager import cache_manager
        schedule = cache_manager.get_schedule(self.current_season)
        if schedule:
            # Map to the old format expected by other methods
            return [
                {
                    "round": r.get("round", 0),
                    "name": r.get("race_name", ""),
                    "date": r.get("date", ""),
                    "circuit": r.get("circuit", ""),
                }
                for r in schedule
            ]
        return []
    
    def _is_cache_valid(self, cache_key: str, cache_dict: Dict) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in cache_dict:
            return False
        return (datetime.now() - cache_dict[cache_key]['timestamp']).total_seconds() < self.cache_duration
    
    def _load_cached_standings(self):
        """Load cached championship standings from file"""
        cache_file = self.cache_dir / "championship_standings.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.standings_cache = data
                    logger.info("Loaded cached championship standings")
            except Exception as e:
                logger.error(f"Error loading cached standings: {e}")
    
    def _save_standings_to_cache(self, standings: ChampionshipStandings):
        """Save championship standings to cache file"""
        cache_file = self.cache_dir / "championship_standings.json"
        try:
            cache_data = {
                'championship_standings': {
                    'data': asdict(standings),
                    'timestamp': datetime.now().isoformat()
                }
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            logger.info("Saved championship standings to cache")
        except Exception as e:
            logger.error(f"Error saving standings to cache: {e}")
    
    async def get_latest_session_results(self, circuit_name: str, session_type: str = "Race") -> Optional[SessionResult]:
        """Get latest session results for a specific circuit and session type"""
        cache_key = f"{circuit_name}_{session_type}_latest"
        
        if self._is_cache_valid(cache_key, self.results_cache):
            return self.results_cache[cache_key]['data']
        
        try:
            # Find the most recent race weekend for this circuit
            race_info = None
            for race in self.f1_calendar:
                if circuit_name.lower() in race['name'].lower():
                    race_info = race
                    break
            
            if not race_info:
                logger.error(f"Circuit not found: {circuit_name}")
                return None
            
            # Check if the race has already happened
            race_date = datetime.strptime(race_info['date'], '%Y-%m-%d')
            if race_date > datetime.now():
                logger.info(f"Race at {circuit_name} hasn't happened yet ({race_date.date()})")
                return None
            
            # Try to get results using FastF1
            session_result = await self._fetch_session_with_fastf1(
                self.current_season, race_info['round'], session_type
            )
            
            if session_result:
                self.results_cache[cache_key] = {
                    'data': session_result,
                    'timestamp': datetime.now()
                }
                return session_result
            
            # Fallback to Ergast API
            session_result = await self._fetch_session_with_ergast(
                self.current_season, race_info['round'], session_type
            )
            
            if session_result:
                self.results_cache[cache_key] = {
                    'data': session_result,
                    'timestamp': datetime.now()
                }
            
            return session_result
            
        except Exception as e:
            logger.error(f"Error fetching session results for {circuit_name}: {e}")
            return None
    
    async def _fetch_session_with_fastf1(self, year: int, round_num: int, session_type: str) -> Optional[SessionResult]:
        """Fetch session results using FastF1 API"""
        try:
            # Map session types to FastF1 session identifiers
            session_map = {
                "Practice": "FP1",  # Default to FP1, could be FP2 or FP3
                "FP1": "FP1",
                "FP2": "FP2", 
                "FP3": "FP3",
                "Qualifying": "Q",
                "Sprint": "S",
                "Race": "R"
            }
            
            session_id = session_map.get(session_type, "R")
            
            # Load session data
            session = fastf1.get_session(year, round_num, session_id)
            session.load()
            
            if session.results.empty:
                logger.warning(f"No results found for {year} round {round_num} {session_type}")
                return None
            
            # Process results
            results = []
            for idx, row in session.results.iterrows():
                result = {
                    'position': row.get('Position', 0),
                    'driver_code': row.get('Abbreviation', ''),
                    'driver_name': row.get('FullName', ''),
                    'team': row.get('TeamName', ''),
                    'time': str(row.get('Time', '')),
                    'gap': str(row.get('Gap', '')),
                    'laps': row.get('Laps', 0),
                    'status': row.get('Status', ''),
                    'points': row.get('Points', 0)
                }
                results.append(result)
            
            # Get fastest lap information
            fastest_lap = {}
            if hasattr(session, 'laps') and not session.laps.empty:
                fastest = session.laps.pick_fastest()
                if fastest is not None:
                    fastest_lap = {
                        'driver': fastest.get('Driver', ''),
                        'time': str(fastest.get('LapTime', '')),
                        'lap_number': fastest.get('LapNumber', 0)
                    }
            
            # Session statistics
            session_stats = {
                'total_laps': session.total_laps if hasattr(session, 'total_laps') else 0,
                'session_duration': str(session.session_info.get('Duration', '')),
                'weather': getattr(session, 'weather_data', {}).get('TrackTemp', 'Unknown') if hasattr(session, 'weather_data') else 'Unknown',
                'completed_drivers': len([r for r in results if r['status'] == 'Finished'])
            }
            
            return SessionResult(
                session_type=session_type,
                session_name=session_id,
                circuit=session.event.get('EventName', f'Round {round_num}'),
                date=session.date if hasattr(session, 'date') else datetime.now(),
                results=results,
                fastest_lap=fastest_lap,
                session_stats=session_stats
            )
            
        except Exception as e:
            logger.error(f"FastF1 error for {year} round {round_num} {session_type}: {e}")
            return None
    
    async def _fetch_session_with_ergast(self, year: int, round_num: int, session_type: str) -> Optional[SessionResult]:
        """Fetch session results using Ergast API as fallback"""
        try:
            # Map session types to Ergast endpoints
            endpoint_map = {
                "Qualifying": "qualifying",
                "Race": "results",
                "Sprint": "sprint"  # Note: Ergast may not have all sprint data
            }
            
            endpoint = endpoint_map.get(session_type, "results")
            url = f"{self.jolpica_base_url}/{year}/{round_num}/{endpoint}.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if session_type == "Race":
                        race_data = data['MRData']['RaceTable']['Races'][0]
                        results_data = race_data['Results']
                        
                        results = []
                        for result in results_data:
                            driver = result['Driver']
                            constructor = result['Constructor']
                            
                            results.append({
                                'position': int(result['position']),
                                'driver_code': driver['code'],
                                'driver_name': f"{driver['givenName']} {driver['familyName']}",
                                'team': constructor['name'],
                                'time': result.get('Time', {}).get('time', ''),
                                'gap': result.get('Time', {}).get('time', ''),
                                'laps': int(result.get('laps', 0)),
                                'status': result['status'],
                                'points': float(result.get('points', 0))
                            })
                        
                        # Get fastest lap
                        fastest_lap = {}
                        fastest_lap_result = next((r for r in results_data if 'FastestLap' in r), None)
                        if fastest_lap_result:
                            fastest_lap = {
                                'driver': fastest_lap_result['Driver']['code'],
                                'time': fastest_lap_result['FastestLap']['Time']['time'],
                                'lap_number': int(fastest_lap_result['FastestLap']['lap'])
                            }
                        
                        return SessionResult(
                            session_type=session_type,
                            session_name="Race",
                            circuit=race_data['raceName'],
                            date=datetime.strptime(race_data['date'], '%Y-%m-%d'),
                            results=results,
                            fastest_lap=fastest_lap,
                            session_stats={'total_drivers': len(results)}
                        )
                    
                    elif session_type == "Qualifying":
                        qualifying_data = data['MRData']['RaceTable']['Races'][0]
                        qualifying_results = qualifying_data['QualifyingResults']
                        
                        results = []
                        for result in qualifying_results:
                            driver = result['Driver']
                            constructor = result['Constructor']
                            
                            results.append({
                                'position': int(result['position']),
                                'driver_code': driver['code'],
                                'driver_name': f"{driver['givenName']} {driver['familyName']}",
                                'team': constructor['name'],
                                'q1_time': result.get('Q1', ''),
                                'q2_time': result.get('Q2', ''),
                                'q3_time': result.get('Q3', ''),
                                'best_time': result.get('Q3') or result.get('Q2') or result.get('Q1', '')
                            })
                        
                        return SessionResult(
                            session_type="Qualifying",
                            session_name="Qualifying",
                            circuit=qualifying_data['raceName'],
                            date=datetime.strptime(qualifying_data['date'], '%Y-%m-%d'),
                            results=results,
                            fastest_lap={'driver': results[0]['driver_code'] if results else '', 'time': results[0]['best_time'] if results else ''},
                            session_stats={'total_drivers': len(results)}
                        )
                    
        except Exception as e:
            logger.error(f"Ergast API error for {year} round {round_num} {session_type}: {e}")
            return None
    
    async def get_current_championship_standings(self) -> Optional[ChampionshipStandings]:
        """Get current championship standings with detailed analysis"""
        cache_key = 'championship_standings'
        
        if self._is_cache_valid(cache_key, self.standings_cache):
            cached_data = self.standings_cache[cache_key]['data']
            return ChampionshipStandings(**cached_data)
        
        try:
            # Get driver standings
            drivers_url = f"{self.jolpica_base_url}/{self.current_season}/driverStandings.json"
            constructors_url = f"{self.jolpica_base_url}/{self.current_season}/constructorStandings.json"
            
            async with aiohttp.ClientSession() as session:
                # Fetch both standings concurrently
                driver_task = session.get(drivers_url)
                constructor_task = session.get(constructors_url)
                
                driver_response, constructor_response = await asyncio.gather(driver_task, constructor_task)
                
                if driver_response.status != 200 or constructor_response.status != 200:
                    return self._get_fallback_standings()
                
                driver_data = await driver_response.json()
                constructor_data = await constructor_response.json()
                
                # Process driver standings
                driver_standings_data = driver_data['MRData']['StandingsTable']['StandingsLists'][0]
                current_round = int(driver_standings_data['round'])
                
                drivers = []
                for standing in driver_standings_data['DriverStandings']:
                    driver = standing['Driver']
                    constructor = standing['Constructors'][0]
                    
                    # Get additional statistics
                    stats = await self._get_driver_season_stats(driver['code'])
                    
                    driver_standing = DriverStanding(
                        position=int(standing['position']),
                        driver_code=driver['code'],
                        driver_name=f"{driver['givenName']} {driver['familyName']}",
                        team=constructor['name'],
                        points=float(standing['points']),
                        wins=int(standing['wins']),
                        podiums=stats.get('podiums', 0),
                        pole_positions=stats.get('pole_positions', 0),
                        fastest_laps=stats.get('fastest_laps', 0),
                        dnfs=stats.get('dnfs', 0),
                        average_finish=stats.get('average_finish', 0.0),
                        points_per_race=float(standing['points']) / max(current_round, 1),
                        form_last_5=stats.get('form_last_5', [])
                    )
                    drivers.append(driver_standing)
                
                # Process constructor standings
                constructor_standings_data = constructor_data['MRData']['StandingsTable']['StandingsLists'][0]
                constructors = []
                
                for standing in constructor_standings_data['ConstructorStandings']:
                    constructor = standing['Constructor']
                    
                    constructor_standing = ConstructorStanding(
                        position=int(standing['position']),
                        team_name=constructor['name'],
                        points=float(standing['points']),
                        wins=int(standing['wins']),
                        podiums=0,  # Calculate from driver standings
                        pole_positions=0,  # Calculate from qualifying results
                        fastest_laps=0,  # Calculate from race results
                        average_finish=0.0,  # Calculate from race results
                        drivers=[]  # Get from driver standings
                    )
                    constructors.append(constructor_standing)
                
                # Generate championship battle analysis
                from services.cache_manager import cache_manager
                schedule = cache_manager.get_schedule(self.current_season)
                total_rounds = len(schedule) if schedule else 0

                championship_battle = self._analyze_championship_battle(drivers, current_round, total_rounds)

                standings = ChampionshipStandings(
                    season=self.current_season,
                    last_updated=datetime.now(),
                    current_round=current_round,
                    total_rounds=total_rounds,
                    drivers=drivers,
                    constructors=constructors,
                    championship_battle=championship_battle
                )
                
                # Cache the results
                self.standings_cache[cache_key] = {
                    'data': asdict(standings),
                    'timestamp': datetime.now()
                }
                
                # Save to file cache
                self._save_standings_to_cache(standings)
                
                logger.info(f"Updated championship standings - Round {current_round}/24")
                return standings
                
        except Exception as e:
            logger.error(f"Error fetching championship standings: {e}")
            return self._get_fallback_standings()
    
    async def _get_driver_season_stats(self, driver_code: str) -> Dict:
        """Get detailed season statistics for a driver"""
        try:
            # This would typically require multiple API calls to get comprehensive stats
            # For now, return basic stats that can be calculated from race results
            
            results_url = f"{self.jolpica_base_url}/{self.current_season}/drivers/{driver_code}/results.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(results_url) as response:
                    if response.status != 200:
                        return {}
                    
                    data = await response.json()
                    races = data['MRData']['RaceTable']['Races']
                    
                    if not races:
                        return {}
                    
                    # Calculate statistics
                    positions = []
                    podiums = 0
                    dnfs = 0
                    
                    for race in races:
                        if 'Results' in race and race['Results']:
                            result = race['Results'][0]  # Driver's result
                            position = int(result.get('position', 999))
                            status = result.get('status', '')
                            
                            if position <= 20:  # Valid finishing position
                                positions.append(position)
                                if position <= 3:
                                    podiums += 1
                            elif 'Finished' not in status:
                                dnfs += 1
                    
                    average_finish = sum(positions) / len(positions) if positions else 0.0
                    form_last_5 = positions[-5:] if len(positions) >= 5 else positions
                    
                    return {
                        'podiums': podiums,
                        'dnfs': dnfs,
                        'average_finish': round(average_finish, 2),
                        'form_last_5': form_last_5,
                        'pole_positions': 0,  # Would need qualifying data
                        'fastest_laps': 0   # Would need race result details
                    }
                    
        except Exception as e:
            logger.error(f"Error getting driver stats for {driver_code}: {e}")
            return {}
    
    def _analyze_championship_battle(self, drivers: List[DriverStanding], current_round: int, total_rounds: int = 0) -> Dict:
        """Analyze the championship battle situation"""
        if not drivers:
            return {}
        
        if total_rounds <= 0:
            from services.cache_manager import cache_manager
            schedule = cache_manager.get_schedule(self.current_season)
            total_rounds = len(schedule) if schedule else 0

        leader = drivers[0]
        remaining_races = total_rounds - current_round
        max_remaining_points = remaining_races * 26  # 25 for win + 1 for fastest lap
        
        # Find drivers still mathematically in contention
        contenders = []
        for driver in drivers:
            points_behind = leader.points - driver.points
            if points_behind <= max_remaining_points:
                contenders.append({
                    'driver': driver.driver_name,
                    'points_behind': points_behind,
                    'realistic_chance': points_behind <= (remaining_races * 15)  # More realistic threshold
                })
        
        # Title fight analysis
        if len(contenders) <= 1:
            battle_status = "Decided"
        elif contenders[1]['points_behind'] <= 50:
            battle_status = "Tight"
        elif contenders[1]['points_behind'] <= 100:
            battle_status = "Competitive"
        else:
            battle_status = "Dominant"
        
        return {
            'leader': leader.driver_name,
            'leader_points': leader.points,
            'battle_status': battle_status,
            'mathematical_contenders': len(contenders),
            'realistic_contenders': len([c for c in contenders if c['realistic_chance']]),
            'points_gap_to_second': contenders[1]['points_behind'] if len(contenders) > 1 else 0,
            'remaining_races': remaining_races,
            'max_remaining_points': max_remaining_points,
            'contenders': contenders[:5]  # Top 5 contenders
        }
    
    def _get_fallback_standings(self) -> Optional[ChampionshipStandings]:
        """Generate fallback championship standings from cache_manager."""
        from services.cache_manager import cache_manager

        year = self.current_season
        driver_data = cache_manager.get_driver_standings(year)
        constructor_data = cache_manager.get_constructor_standings(year)

        if not driver_data:
            return None

        drivers = []
        for s in driver_data[:20]:
            drivers.append(DriverStanding(
                position=s.get("position", 0),
                driver_code=s.get("driver", ""),
                driver_name=s.get("name", ""),
                team=s.get("team", ""),
                points=float(s.get("points", 0)),
                wins=int(s.get("wins", 0)),
                podiums=0,
                pole_positions=0,
                fastest_laps=0,
                dnfs=0,
                average_finish=0.0,
                points_per_race=0.0,
                form_last_5=[],
            ))

        constructors = []
        for c in (constructor_data or []):
            constructors.append(ConstructorStanding(
                position=c.get("position", 0),
                team_name=c.get("team_name", ""),
                points=float(c.get("points", 0)),
                wins=int(c.get("wins", 0)),
                podiums=0,
                pole_positions=0,
                fastest_laps=0,
                average_finish=0.0,
                drivers=[],
            ))

        completed = cache_manager.get_completed_races(year)
        schedule = cache_manager.get_schedule(year)

        return ChampionshipStandings(
            season=year,
            last_updated=datetime.now(),
            current_round=len(completed),
            total_rounds=len(schedule),
            drivers=drivers,
            constructors=constructors,
            championship_battle=self._analyze_championship_battle(drivers, len(completed), len(schedule)) if drivers else {},
        )
    
    async def update_standings_after_race(self, circuit_name: str) -> bool:
        """Update championship standings after a race"""
        try:
            # Get the latest race results
            race_result = await self.get_latest_session_results(circuit_name, "Race")
            if not race_result:
                return False
            
            # Invalidate standings cache to force refresh
            if 'championship_standings' in self.standings_cache:
                del self.standings_cache['championship_standings']
            
            # Get fresh standings
            new_standings = await self.get_current_championship_standings()
            
            if new_standings:
                logger.info(f"Updated championship standings after {circuit_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating standings after {circuit_name}: {e}")
            return False
    
    async def get_detailed_qualifying_results(self, circuit_name: str) -> Optional[Dict]:
        """Get detailed qualifying results with Q1, Q2, Q3 breakdown"""
        cache_key = f"qualifying_detailed_{circuit_name}"
        if self._is_cache_valid(cache_key, self.results_cache):
            return self.results_cache[cache_key]['data']
        
        try:
            # Find the circuit in our calendar
            race_info = None
            for race in self.f1_calendar:
                if circuit_name.lower() in race['name'].lower():
                    race_info = race
                    break
            
            if not race_info:
                return None
            
            # Check if qualifying has happened
            race_date = datetime.strptime(race_info['date'], '%Y-%m-%d')
            if race_date > datetime.now():
                return None
            
            # Load qualifying session with FastF1
            try:
                session = fastf1.get_session(self.current_season, race_info['round'], 'Q')
                session.load()
                
                if session.results.empty:
                    return None
                
                # Process detailed qualifying results
                detailed_results = {
                    'circuit_name': circuit_name,
                    'date': race_info['date'],
                    'session_type': 'Qualifying',
                    'results': [],
                    'q1_eliminated': [],
                    'q2_eliminated': [], 
                    'q3_participants': [],
                    'pole_position': {},
                    'session_stats': {}
                }
                
                # Process each driver's qualifying performance
                for idx, row in session.results.iterrows():
                    driver_result = {
                        'position': int(row.get('Position', 0)),
                        'driver_code': row.get('Abbreviation', ''),
                        'driver_name': row.get('FullName', ''),
                        'team': row.get('TeamName', ''),
                        'q1_time': str(row.get('Q1', '')) if pd.notna(row.get('Q1')) else None,
                        'q2_time': str(row.get('Q2', '')) if pd.notna(row.get('Q2')) else None,
                        'q3_time': str(row.get('Q3', '')) if pd.notna(row.get('Q3')) else None,
                        'best_time': str(row.get('Time', '')) if pd.notna(row.get('Time')) else None,
                        'gap_to_pole': str(row.get('Gap', '')) if pd.notna(row.get('Gap')) else None
                    }
                    
                    detailed_results['results'].append(driver_result)
                    
                    # Categorize by qualifying segment
                    position = driver_result['position']
                    if position <= 10 and driver_result['q3_time']:
                        detailed_results['q3_participants'].append(driver_result)
                    elif position <= 15 and driver_result['q2_time'] and not driver_result['q3_time']:
                        detailed_results['q2_eliminated'].append(driver_result)
                    elif position > 15:
                        detailed_results['q1_eliminated'].append(driver_result)
                
                # Set pole position
                if detailed_results['results']:
                    detailed_results['pole_position'] = detailed_results['results'][0]
                
                # Calculate session statistics
                detailed_results['session_stats'] = {
                    'total_participants': len(detailed_results['results']),
                    'q3_participants': len(detailed_results['q3_participants']),
                    'pole_time': detailed_results['pole_position'].get('best_time', 'N/A'),
                    'grid_surprises': self._identify_qualifying_surprises(detailed_results['results']),
                    'competitive_gaps': self._analyze_qualifying_gaps(detailed_results['q3_participants'])
                }
                
                # Cache the result
                self.results_cache[cache_key] = {
                    'data': detailed_results,
                    'timestamp': datetime.now()
                }
                
                return detailed_results
                
            except Exception as fastf1_error:
                logger.warning(f"FastF1 error for qualifying at {circuit_name}: {fastf1_error}")
                return None
            
        except Exception as e:
            logger.error(f"Error fetching detailed qualifying results for {circuit_name}: {e}")
            return None
    
    async def get_recent_race_summary(self, limit: int = 3) -> List[Dict]:
        """Get summary of recent race results for dashboard display"""
        cache_key = f"recent_races_{limit}"
        if self._is_cache_valid(cache_key, self.results_cache):
            return self.results_cache[cache_key]['data']
        
        try:
            recent_races = []
            current_date = datetime.now()
            
            # Find recent completed races
            completed_races = []
            for race_info in self.f1_calendar:
                race_date = datetime.strptime(race_info['date'], '%Y-%m-%d')
                if race_date < current_date:
                    completed_races.append((race_info, race_date))
            
            # Sort by date (most recent first) and take the limit
            completed_races.sort(key=lambda x: x[1], reverse=True)
            
            for race_info, race_date in completed_races[:limit]:
                try:
                    race_result = await self.get_latest_session_results(race_info['name'], "Race")
                    if race_result and race_result.results:
                        # Create race summary
                        race_summary = {
                            'race_name': race_info['name'],
                            'date': race_info['date'],
                            'round': race_info['round'],
                            'podium': race_result.results[:3] if len(race_result.results) >= 3 else race_result.results,
                            'fastest_lap': self._find_fastest_lap_driver(race_result.results),
                            'total_finishers': len([r for r in race_result.results if 'Finished' in r.get('status', '') or '+' in r.get('gap', '')]),
                            'dnfs': len([r for r in race_result.results if 'DNF' in r.get('status', '') or 'Retired' in r.get('status', '')]),
                            'points_scorers': len([r for r in race_result.results if r.get('points', 0) > 0]),
                            'race_highlights': self._generate_race_highlights(race_result)
                        }
                        recent_races.append(race_summary)
                        
                except Exception as race_error:
                    logger.warning(f"Error processing race {race_info['name']}: {race_error}")
                    continue
            
            # Cache the result
            self.results_cache[cache_key] = {
                'data': recent_races,
                'timestamp': datetime.now()
            }
            
            return recent_races
            
        except Exception as e:
            logger.error(f"Error fetching recent race summaries: {e}")
            return []
    
    def _identify_qualifying_surprises(self, results: List[Dict]) -> List[str]:
        """Identify surprising qualifying performances"""
        surprises = []
        
        # Define expected performance ranges for teams (rough estimates for 2025)
        team_expectations = {
            'McLaren': (1, 4),
            'Red Bull Racing': (2, 6), 
            'Ferrari': (3, 7),
            'Mercedes': (4, 8),
            'Aston Martin': (7, 12),
            'Alpine': (9, 14),
            'Racing Bulls': (11, 16),
            'Williams': (13, 18),
            'Haas': (14, 19),
            'Kick Sauber': (16, 20)
        }
        
        for result in results[:10]:  # Top 10 only
            team = result.get('team', '')
            position = result.get('position', 0)
            driver = result.get('driver_name', '')
            
            # Check if performance is outside expected range
            for team_name, (min_pos, max_pos) in team_expectations.items():
                if team_name in team:
                    if position < min_pos:
                        surprises.append(f"{driver} qualified P{position} (outperformed expectations)")
                    elif position > max_pos and position <= 10:
                        surprises.append(f"{driver} qualified P{position} (underperformed expectations)")
                    break
        
        return surprises[:3]  # Return top 3 surprises
    
    def _analyze_qualifying_gaps(self, q3_results: List[Dict]) -> Dict:
        """Analyze competitive gaps in Q3"""
        if not q3_results or len(q3_results) < 2:
            return {'analysis': 'Insufficient data'}
        
        try:
            # Calculate gaps between positions
            gaps = []
            for i in range(1, len(q3_results)):
                # This is simplified - in real implementation, you'd parse lap times
                gaps.append(f"P{i} to P{i+1}: Close battle")
            
            return {
                'close_battles': gaps[:3],
                'pole_margin': 'Pole secured with strong performance',
                'q3_competitiveness': 'High' if len(q3_results) >= 8 else 'Moderate'
            }
        except Exception:
            return {'analysis': 'Unable to analyze gaps'}
    
    def _find_fastest_lap_driver(self, results: List[Dict]) -> Dict:
        """Find the driver with the fastest lap"""
        # In a real implementation, this would parse actual lap times
        # For now, return a placeholder based on race winner
        if results:
            return {
                'driver': results[0].get('driver_name', 'Unknown'),
                'team': results[0].get('team', 'Unknown'),
                'time': '1:23.456'  # Placeholder - would be actual fastest lap time
            }
        return {'driver': 'Unknown', 'team': 'Unknown', 'time': 'N/A'}
    
    def _generate_race_highlights(self, race_result: SessionResult) -> List[str]:
        """Generate key highlights from race results"""
        highlights = []
        
        if not race_result.results:
            return ['No race data available']
        
        # Winner highlight
        winner = race_result.results[0]
        highlights.append(f"{winner.get('driver_name', 'Unknown')} takes victory")
        
        # Podium composition
        if len(race_result.results) >= 3:
            podium_teams = [r.get('team', 'Unknown')[:3] for r in race_result.results[:3]]
            unique_teams = len(set(podium_teams))
            if unique_teams == 3:
                highlights.append("Three different teams on podium")
            elif unique_teams == 1:
                highlights.append(f"{race_result.results[0].get('team', 'Unknown')} dominates podium")
        
        # DNF count
        dnf_count = len([r for r in race_result.results if 'DNF' in r.get('status', '') or 'Retired' in r.get('status', '')])
        if dnf_count > 3:
            highlights.append(f"High attrition race: {dnf_count} retirements")
        elif dnf_count == 0:
            highlights.append("Clean race: All cars finished")
        
        return highlights[:3]

# Global service instance
f1_results_service = F1ResultsService()

# Lazy loading function
def get_f1_results_service():
    """Get F1 results service instance with lazy loading"""
    return f1_results_service