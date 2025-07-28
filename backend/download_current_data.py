#!/usr/bin/env python3
"""
F1 Data Download Script for 2024-2025 Seasons
Downloads comprehensive F1 session data and telemetry using Fast-F1.
Includes FP2, FP3, Qualifying, and Race sessions for telemetry analysis.
"""

import fastf1
import pandas as pd
import os
import sys
import argparse
from datetime import datetime
import logging
from typing import List, Dict, Optional
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, will use system env vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class F1DataDownloader:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = os.path.join(os.path.dirname(__file__), cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.output_file = os.path.join(os.path.dirname(__file__), 'f1_data.csv')

        # Try setting up Google Drive cache
        drive_file_id = os.getenv('GOOGLE_DRIVE_CACHE_FILE_ID')
        self.cache_ready = False

        if drive_file_id:
            from google_drive_data_loader import setup_fastf1_cache_from_drive
            logger.info("Attempting to use Google Drive cache...")
            if setup_fastf1_cache_from_drive(drive_file_id):
                logger.info("✓ Google Drive cache setup complete")
                self.cache_ready = True
            else:
                logger.warning("Google Drive cache failed or incomplete. Falling back to local cache.")

        # Fallback to local cache
        fastf1.Cache.enable_cache(self.cache_dir)
        logger.info(f"Local cache enabled at: {self.cache_dir}")
        
        # Output CSV file
        self.output_file = os.path.join(os.path.dirname(__file__), 'f1_data.csv')
        
        # Driver team mappings for 2024-2025 (using exact FastF1 driver names)
        self.driver_teams = {
            2024: {
                'Lewis Hamilton': 'Mercedes',  # #44
                'Max Verstappen': 'Red Bull Racing Honda RBPT',  # #1
                'Lando Norris': 'McLaren Mercedes',  # #4
                'Oscar Piastri': 'McLaren Mercedes',  # #81
                'Carlos Sainz': 'Scuderia Ferrari',  # #55
                'Nico Hulkenberg': 'MoneyGram Haas F1 Team',  # #27
                'Lance Stroll': 'Aston Martin Aramco Mercedes',  # #18
                'Fernando Alonso': 'Aston Martin Aramco Mercedes',  # #14
                'Alexander Albon': 'Williams Mercedes',  # #23
                'Yuki Tsunoda': 'Scuderia AlphaTauri Honda RBPT',  # #22
                'Logan Sargeant': 'Williams Mercedes',  # #2
                'Kevin Magnussen': 'MoneyGram Haas F1 Team',  # #20
                'Daniel Ricciardo': 'Scuderia AlphaTauri Honda RBPT',  # #3
                'Charles Leclerc': 'Scuderia Ferrari',  # #16
                'Valtteri Bottas': 'Alfa Romeo F1 Team Stake',  # #77
                'Esteban Ocon': 'BWT Alpine F1 Team',  # #31
                'Sergio Perez': 'Red Bull Racing Honda RBPT',  # #11
                'Guanyu Zhou': 'Alfa Romeo F1 Team Stake',  # #24
                'George Russell': 'Mercedes',  # #63
                'Pierre Gasly': 'BWT Alpine F1 Team'  # #10
            },
            2025: {
                'Lando Norris': 'McLaren Mercedes',  # #4
                'Oscar Piastri': 'McLaren Mercedes',  # #81
                'Nico Hulkenberg': 'MoneyGram Haas F1 Team',  # #27
                'Lewis Hamilton': 'Scuderia Ferrari',  # #44
                'Max Verstappen': 'Red Bull Racing Honda RBPT',  # #1
                'Pierre Gasly': 'BWT Alpine F1 Team',  # #10
                'Lance Stroll': 'Aston Martin Aramco Mercedes',  # #18
                'Alexander Albon': 'Williams Mercedes',  # #23
                'Fernando Alonso': 'Aston Martin Aramco Mercedes',  # #14
                'George Russell': 'Mercedes',  # #63
                'Oliver Bearman': 'MoneyGram Haas F1 Team',  # #87
                'Carlos Sainz': 'Williams Mercedes',  # #55
                'Esteban Ocon': 'BWT Alpine F1 Team',  # #31
                'Charles Leclerc': 'Scuderia Ferrari',  # #16
                'Yuki Tsunoda': 'Visa Cash App RB F1 Team',  # #22
                'Kimi Antonelli': 'Mercedes',  # #12
                'Isack Hadjar': 'Kick Sauber F1 Team',  # #6
                'Gabriel Bortoleto': 'Kick Sauber F1 Team',  # #5
                'Liam Lawson': 'Visa Cash App RB F1 Team',  # #30
                'Franco Colapinto': 'Williams Mercedes'  # #43
            }
        }
        
        # 2024 F1 Calendar (completed races)
        self.race_calendar_2024 = [
            'Bahrain Grand Prix',
            'Saudi Arabian Grand Prix', 
            'Australian Grand Prix',
            'Japanese Grand Prix',
            'Chinese Grand Prix',
            'Miami Grand Prix',
            'Emilia Romagna Grand Prix',
            'Monaco Grand Prix',
            'Canadian Grand Prix',
            'Spanish Grand Prix',
            'Austrian Grand Prix',
            'British Grand Prix',
            'Hungarian Grand Prix',
            'Belgian Grand Prix',
            'Dutch Grand Prix',
            'Italian Grand Prix',
            'Azerbaijan Grand Prix',
            'Singapore Grand Prix',
            'United States Grand Prix',
            'Mexico City Grand Prix',
            'São Paulo Grand Prix',
            'Las Vegas Grand Prix',
            'Qatar Grand Prix',
            'Abu Dhabi Grand Prix'
        ]
        
        # 2025 F1 Calendar (will download available races)
        self.race_calendar_2025 = [
            'Australian Grand Prix',
            'Chinese Grand Prix', 
            'Japanese Grand Prix',
            'Bahrain Grand Prix',
            'Saudi Arabian Grand Prix',
            'Miami Grand Prix',
            'Emilia Romagna Grand Prix',
            'Monaco Grand Prix',
            'Spanish Grand Prix',
            'Canadian Grand Prix',
            'Austrian Grand Prix',
            'British Grand Prix',
            'Belgian Grand Prix',
            'Hungarian Grand Prix',
            'Dutch Grand Prix',
            'Italian Grand Prix',
            'Azerbaijan Grand Prix',
            'Singapore Grand Prix',
            'United States Grand Prix',
            'Mexico City Grand Prix',
            'São Paulo Grand Prix',
            'Las Vegas Grand Prix',
            'Qatar Grand Prix',
            'Abu Dhabi Grand Prix'
        ]
        
        # Sessions to download for telemetry analysis - comprehensive set
        self.sessions_to_download = ['FP2', 'FP3', 'SQ', 'Q', 'S', 'R']  # Added Sprint Qualifying
        self.session_names = {
            'FP2': 'Practice 2',
            'FP3': 'Practice 3',
            'SQ': 'Sprint Qualifying',
            'Q': 'Qualifying',
            'S': 'Sprint',
            'R': 'Race'
        }
    
    def is_session_cached(self, season: int, race_name: str, session_type: str) -> bool:
        """Check if session data is already cached"""
        try:
            session = fastf1.get_session(season, race_name, session_type)
            # Check if session info is cached
            cache_key = f"{season}_{race_name}_{session_type}"
            
            # Try to load session with minimal data to check cache
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            
            # If we get here without exception, basic session data exists
            # Now check if telemetry data is cached by trying to load a quick sample
            try:
                session.load(laps=True, telemetry=True, weather=False, messages=False)
                if not session.laps.empty and session.drivers:
                    # Try to get telemetry for first driver's first lap as cache test
                    first_driver = session.drivers[0]
                    driver_laps = session.laps.pick_drivers(first_driver)
                    if not driver_laps.empty:
                        test_lap = driver_laps.iloc[0]
                        test_telemetry = test_lap.get_telemetry()
                        return len(test_telemetry) > 0
            except:
                return False
            
            return False
        except Exception:
            return False
    
    def download_session_telemetry(self, season: int, race_name: str, session_type: str) -> bool:
        """Download and cache telemetry data for a specific session"""
        try:
            # Check if session is already cached
            if self.is_session_cached(season, race_name, session_type):
                logger.info(f"✓ {self.session_names.get(session_type, session_type)} for {race_name} - Already cached, skipping")
                return True
            
            logger.info(f"Downloading {self.session_names.get(session_type, session_type)} telemetry for {season} {race_name}...")
            
            # Get session - handle sprint sessions that may not exist
            try:
                session = fastf1.get_session(season, race_name, session_type)
                session.load()
            except Exception as e:
                if session_type == 'S':  # Sprint session may not exist for all races
                    logger.info(f"Sprint session not available for {race_name} - skipping")
                    return False
                else:
                    raise e
            
            # Load laps data to trigger telemetry caching
            laps = session.laps
            if laps.empty:
                logger.warning(f"No lap data available for {session_type} session")
                return False
            
            # Load telemetry for ALL laps of each driver to comprehensively cache data
            drivers_processed = 0
            for driver in session.drivers:
                try:
                    driver_laps = laps.pick_drivers(driver)
                    if not driver_laps.empty:
                        # Cache telemetry for fastest lap (most important)
                        fastest_lap = driver_laps.pick_fastest()
                        if not fastest_lap.empty:
                            telemetry = fastest_lap.get_telemetry()
                        
                        # Also cache telemetry for a few representative laps for analysis variety
                        sample_laps = driver_laps.iloc[::max(1, len(driver_laps)//5)]  # Sample every 5th lap
                        for _, lap in sample_laps.iterrows():
                            try:
                                lap_telemetry = lap.get_telemetry()
                            except:
                                continue
                        
                        drivers_processed += 1
                except Exception as e:
                    logger.debug(f"Could not load telemetry for driver {driver}: {e}")
                    continue
            
            logger.info(f"✓ {self.session_names.get(session_type, session_type)} - Cached telemetry for {drivers_processed} drivers")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {session_type} telemetry for {race_name}: {str(e)}")
            return False

    def get_session_data(self, season: int, race_name: str) -> Optional[Dict]:
        """Download and process data for a specific race weekend"""
        try:
            logger.info(f"Processing {season} {race_name}...")
            
            # Download telemetry for all sessions - comprehensive caching
            sessions_downloaded = 0
            for session_type in self.sessions_to_download:
                if self.download_session_telemetry(season, race_name, session_type):
                    sessions_downloaded += 1
                # time.sleep(2)  # Removed delay
            
            # Get race and qualifying sessions for results data
            race_weekend = fastf1.get_session(season, race_name, 'R')
            race_weekend.load()
            
            qualifying = fastf1.get_session(season, race_name, 'Q')
            qualifying.load()
            
            # Get race results
            race_results = race_weekend.results
            qualifying_results = qualifying.results
            
            session_data = []
            
            # Process each driver's results
            for idx, driver_result in race_results.iterrows():
                driver_name = driver_result['FullName']
                
                # Skip if driver name is NaN or empty
                if pd.isna(driver_name) or not driver_name:
                    continue
                
                # Get qualifying position
                qualifying_position = None
                try:
                    qual_result = qualifying_results[qualifying_results['FullName'] == driver_name]
                    if not qual_result.empty:
                        qualifying_position = int(qual_result.iloc[0]['Position'])
                except:
                    qualifying_position = 20  # Default if not found
                
                # Get race position
                race_position = None
                try:
                    race_position = int(driver_result['Position'])
                except:
                    race_position = 20  # Default if DNF
                
                # Get team
                team = self.driver_teams.get(season, {}).get(driver_name, 'Unknown')
                
                # Get lap times and calculate average
                try:
                    driver_laps = race_weekend.laps.pick_drivers(driver_result['Abbreviation'])
                    avg_lap_time = driver_laps['LapTime'].mean().total_seconds() if not driver_laps.empty else 90.0
                except:
                    avg_lap_time = 90.0
                
                # Calculate gap to winner
                gap_to_winner = 0.0
                try:
                    if race_position > 1:
                        gap_to_winner = float(driver_result['Time'].total_seconds()) if pd.notna(driver_result['Time']) else 0.0
                except:
                    gap_to_winner = 0.0
                
                # Weather conditions (simplified)
                weather_condition = 'Dry'  # Default - can be enhanced with actual weather data
                
                session_data.append({
                    'season': season,
                    'race': race_name,
                    'driver': driver_name,
                    'team': team,
                    'qualifying_position': qualifying_position,
                    'race_position': race_position,
                    'avg_lap_time': avg_lap_time,
                    'gap_to_winner': gap_to_winner,
                    'weather': weather_condition,
                    'points': int(driver_result['Points']) if pd.notna(driver_result['Points']) else 0,
                    'grid_position': int(driver_result['GridPosition']) if pd.notna(driver_result['GridPosition']) else qualifying_position,
                    'status': str(driver_result['Status']) if pd.notna(driver_result['Status']) else 'Finished'
                })
            
            logger.info(f"Successfully processed {len(session_data)} driver records and {sessions_downloaded} sessions for {race_name}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error processing {season} {race_name}: {str(e)}")
            return None
    
    def check_cache_status(self, season: int) -> None:
        """Check and report cache status for a season"""
        race_calendar = self.race_calendar_2024 if season == 2024 else self.race_calendar_2025
        logger.info(f"\n📊 Cache Status for {season} Season:")
        logger.info("-" * 50)
        
        total_sessions = 0
        cached_sessions = 0
        
        for race_name in race_calendar:
            race_cached = []
            race_missing = []
            
            for session_type in self.sessions_to_download:
                total_sessions += 1
                if self.is_session_cached(season, race_name, session_type):
                    cached_sessions += 1
                    race_cached.append(session_type)
                else:
                    race_missing.append(session_type)
            
            # Show race status
            if race_missing:
                logger.info(f"📥 {race_name}: Missing {', '.join(race_missing)} | Cached {', '.join(race_cached)}")
            else:
                logger.info(f"✅ {race_name}: All sessions cached")
        
        cache_percentage = (cached_sessions / total_sessions * 100) if total_sessions > 0 else 0
        logger.info(f"\n📈 Overall: {cached_sessions}/{total_sessions} sessions cached ({cache_percentage:.1f}%)")
        logger.info("-" * 50)

    def download_season_data(self, season: int) -> List[Dict]:
        """Download all race data for a specific season"""
        logger.info(f"Starting download for {season} season...")
        
        # Check cache status first
        self.check_cache_status(season)
        
        race_calendar = self.race_calendar_2024 if season == 2024 else self.race_calendar_2025
        all_season_data = []
        
        for i, race_name in enumerate(race_calendar):
            try:
                logger.info(f"Progress: {i+1}/{len(race_calendar)} races for {season} season")
                
                # Add delay to avoid overwhelming the API
                # time.sleep(3)
                
                race_data = self.get_session_data(season, race_name)
                if race_data:
                    all_season_data.extend(race_data)
                    logger.info(f"✓ {race_name} - {len(race_data)} records")
                else:
                    logger.warning(f"✗ {race_name} - No data available (race may not have occurred yet)")
                    
            except Exception as e:
                logger.error(f"Failed to download {race_name}: {str(e)}")
                continue
        
        logger.info(f"Season {season} download complete: {len(all_season_data)} total records")
        return all_season_data
    
    def download_all_data(self, seasons: List[int] = [2024, 2025]) -> None:
        """Download comprehensive data for all specified seasons with full telemetry caching"""
        logger.info("="*60)
        logger.info("F1 COMPREHENSIVE DATA DOWNLOAD - 2024-2025 SEASONS")
        logger.info("="*60)
        logger.info(f"Seasons to download: {seasons}")
        logger.info("Sessions per race: FP2, FP3, Qualifying, Sprint (if available), Race")
        logger.info("This will download and cache ALL telemetry data for comprehensive analysis")
        logger.info("Estimated time: 30-60 minutes depending on internet speed")
        logger.info("="*60)
        
        all_data = []
        total_races = sum(len(self.race_calendar_2024 if season == 2024 else self.race_calendar_2025) for season in seasons)
        
        for season in seasons:
            logger.info(f"\n🏁 Starting {season} season download...")
            season_data = self.download_season_data(season)
            all_data.extend(season_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        if df.empty:
            logger.error("No data was downloaded!")
            return
        
        # Save to CSV
        df.to_csv(self.output_file, index=False)
        logger.info(f"\n✅ Data successfully saved to {self.output_file}")
        
        # Check cache size
        cache_size = 0
        if os.path.exists(self.cache_dir):
            for dirpath, dirnames, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    cache_size += os.path.getsize(os.path.join(dirpath, filename))
        
        logger.info(f"📁 Cache directory size: {cache_size / (1024*1024):.1f} MB")
        
        # Print summary statistics
        self.print_summary(df)
    
    def print_summary(self, df: pd.DataFrame) -> None:
        """Print summary statistics of downloaded data"""
        logger.info("\n" + "="*50)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("="*50)
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Seasons: {sorted(df['season'].unique())}")
        logger.info(f"Races: {len(df['race'].unique())}")
        logger.info(f"Drivers: {len(df['driver'].unique())}")
        logger.info(f"Teams: {len(df['team'].unique())}")
        
        logger.info("\nDrivers per season:")
        for season in sorted(df['season'].unique()):
            season_data = df[df['season'] == season]
            logger.info(f"  {season}: {len(season_data['driver'].unique())} drivers, {len(season_data['race'].unique())} races")
        
        logger.info("\nSample of downloaded data:")
        logger.info(df.head().to_string())
        logger.info("="*50)

def main():
    """Main function to run F1 data download or skip if cache is ready"""
    parser = argparse.ArgumentParser(description='F1 Comprehensive Data Downloader')
    parser.add_argument('seasons', nargs='*', type=int, default=[2024, 2025], 
                       help='Seasons to download (default: 2024 2025)')
    parser.add_argument('--races', nargs='+', 
                       help='Specific races to download (e.g. "Las Vegas Grand Prix" "Qatar Grand Prix")')
    parser.add_argument('--force-download', action='store_true',
                       help='Force download even if Google Drive cache is available')
    
    args = parser.parse_args()
    
    print("🏎️  F1 COMPREHENSIVE DATA DOWNLOADER - 2024-2025 SEASONS")
    print("="*60)
    print("This script will download or use cached data for:")
    print("• Race weekend sessions (FP2, FP3, Q, S, R)")
    print("• Full telemetry and lap time data")
    print("• Automatically uses Google Drive cache if available")
    print("="*60)

    seasons = args.seasons

    downloader = F1DataDownloader()
    
    # Override race calendars if specific races are requested
    if args.races:
        print(f"\n🎯 Downloading specific races: {', '.join(args.races)}")
        for season in seasons:
            if season == 2024:
                downloader.race_calendar_2024 = args.races
            elif season == 2025:
                downloader.race_calendar_2025 = args.races

    if downloader.cache_ready and not args.force_download:
        print("\n✅ Google Drive cache detected.")
        print("🚀 Skipping full download — ready to use data for analysis or app.")
        print("💡 Use --force-download to download fresh data anyway.")
        return
    
    if args.force_download and downloader.cache_ready:
        print("\n🔄 Force download enabled - downloading fresh data despite cache availability.")

    try:
        start_time = datetime.now()
        downloader.download_all_data(seasons)
        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n🎉 Download completed successfully in {duration}")
        print(f"📊 Data saved to: {downloader.output_file}")
        print(f"💾 Cache directory: {downloader.cache_dir}")
        print("🚀 You are now ready to run your analysis or serve your app.")

    except KeyboardInterrupt:
        print("\n⏸️  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        import traceback
        logger.error("❌ Download failed:\n" + traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
