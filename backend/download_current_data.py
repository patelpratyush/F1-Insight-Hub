#!/usr/bin/env python3
"""
F1 Data Download Script for 2024-2025 Seasons
Downloads F1 session data using Fast-F1 and caches it for ML model training.
"""

import fastf1
import pandas as pd
import os
import sys
from datetime import datetime
import logging
from typing import List, Dict, Optional
import time

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
        """Initialize the F1 data downloader with cache directory"""
        self.cache_dir = os.path.join(os.path.dirname(__file__), cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Try to setup cache from Google Drive first
        drive_file_id = os.getenv('GOOGLE_DRIVE_CACHE_FILE_ID')
        if drive_file_id:
            from google_drive_data_loader import setup_fastf1_cache_from_drive
            logger.info("Attempting to use Google Drive cache...")
            if setup_fastf1_cache_from_drive(drive_file_id):
                logger.info("Using Google Drive cache")
                return
        
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
        
        # 2025 F1 Calendar (from Fast-F1 API - races completed up to British Grand Prix)
        self.race_calendar_2025 = [
            # Skip Pre-Season Testing as it's not a race
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
            'British Grand Prix'
            # Remaining races (not yet completed):
            # 'Belgian Grand Prix',
            # 'Hungarian Grand Prix',
            # 'Dutch Grand Prix',
            # 'Italian Grand Prix',
            # 'Azerbaijan Grand Prix',
            # 'Singapore Grand Prix',
            # 'United States Grand Prix',
            # 'Mexico City Grand Prix',
            # 'São Paulo Grand Prix',
            # 'Las Vegas Grand Prix',
            # 'Qatar Grand Prix',
            # 'Abu Dhabi Grand Prix'
        ]
    
    def get_session_data(self, season: int, race_name: str) -> Optional[Dict]:
        """Download and process data for a specific race session"""
        try:
            logger.info(f"Processing {season} {race_name}...")
            
            # Get race weekend
            race_weekend = fastf1.get_session(season, race_name, 'R')
            race_weekend.load()
            
            # Get qualifying session
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
            
            logger.info(f"Successfully processed {len(session_data)} driver records for {race_name}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error processing {season} {race_name}: {str(e)}")
            return None
    
    def download_season_data(self, season: int) -> List[Dict]:
        """Download all race data for a specific season"""
        logger.info(f"Starting download for {season} season...")
        
        race_calendar = self.race_calendar_2024 if season == 2024 else self.race_calendar_2025
        all_season_data = []
        
        for race_name in race_calendar:
            try:
                # Add delay to avoid overwhelming the API
                time.sleep(2)
                
                race_data = self.get_session_data(season, race_name)
                if race_data:
                    all_season_data.extend(race_data)
                    logger.info(f"✓ {race_name} - {len(race_data)} records")
                else:
                    logger.warning(f"✗ {race_name} - No data available")
                    
            except Exception as e:
                logger.error(f"Failed to download {race_name}: {str(e)}")
                continue
        
        logger.info(f"Season {season} download complete: {len(all_season_data)} total records")
        return all_season_data
    
    def download_all_data(self, seasons: List[int] = [2024, 2025]) -> None:
        """Download data for all specified seasons"""
        logger.info("Starting F1 data download...")
        logger.info(f"Seasons to download: {seasons}")
        
        all_data = []
        
        for season in seasons:
            season_data = self.download_season_data(season)
            all_data.extend(season_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        if df.empty:
            logger.error("No data was downloaded!")
            return
        
        # Save to CSV
        df.to_csv(self.output_file, index=False)
        logger.info(f"Data saved to {self.output_file}")
        
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
    """Main function to run the data download"""
    print("F1 Data Downloader - 2024-2025 Seasons")
    print("="*40)
    
    # Check command line arguments
    seasons = [2024, 2025]
    if len(sys.argv) > 1:
        try:
            seasons = [int(year) for year in sys.argv[1:]]
        except ValueError:
            print("Invalid season format. Use: python download_current_data.py 2024 2025")
            sys.exit(1)
    
    downloader = F1DataDownloader()
    
    try:
        downloader.download_all_data(seasons)
        print("\n✓ Download completed successfully!")
        print(f"Data saved to: {downloader.output_file}")
        print(f"Cache directory: {downloader.cache_dir}")
        
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
