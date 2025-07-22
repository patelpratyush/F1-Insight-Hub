#!/usr/bin/env python3
"""
Google Drive Cache Loader for F1 Data
Downloads and extracts FastF1 cache from Google Drive to speed up data loading.
"""
import os
import zipfile
import tempfile
import logging
from typing import Optional
import fastf1

logger = logging.getLogger(__name__)

def download_from_google_drive(file_id: str, destination: str) -> bool:
    """Download a file from Google Drive using direct download link"""
    try:
        import requests
        
        logger.info(f"Downloading cache from Google Drive (ID: {file_id[:10]}...)")
        
        session = requests.Session()
        
        # For large files, Google Drive shows a warning page first
        # Get the warning page to extract the download link
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(url)
        
        # Check if we got the virus scan warning page
        if 'virus scan warning' in response.text.lower() or 'exceeds the maximum file size' in response.text:
            logger.info("File too large for virus scan - extracting direct download link...")
            import re
            # Extract the form action URL and parameters
            form_action = re.search(r'action=\"([^\"]+)\"', response.text)
            if form_action:
                base_url = form_action.group(1)
                
                # Extract all form parameters
                inputs = re.findall(r'<input[^>]*name=\"([^\"]+)\"[^>]*value=\"([^\"]+)\"', response.text)
                params = {name: value for name, value in inputs}
                
                logger.info("Found download form, proceeding with large file download...")
                response = session.get(base_url, params=params, stream=True)
            else:
                logger.error("Could not find download form in warning page")
                return False
        else:
            # Regular download - make it streaming
            response = session.get(url, stream=True)
        
        if response.status_code != 200:
            logger.error(f"Failed to download from Google Drive: HTTP {response.status_code}")
            return False
        
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rDownloading cache: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f} MB")
        return True
        
    except ImportError:
        logger.error("requests library not available. Install with: pip install requests")
        return False
    except Exception as e:
        logger.error(f"Error downloading from Google Drive: {str(e)}")
        return False

def extract_cache_zip(zip_path: str, cache_dir: str) -> bool:
    """Extract cache zip file to cache directory"""
    try:
        logger.info(f"Extracting cache to {cache_dir}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cache_dir)
        
        # Count extracted files
        file_count = sum(len(files) for _, _, files in os.walk(cache_dir))
        logger.info(f"Extracted {file_count} cache files")
        
        return True
        
    except Exception as e:
        logger.error(f"Error extracting cache: {str(e)}")
        return False

def setup_fastf1_cache_from_drive(file_id: str, cache_dir: str = "cache") -> bool:
    """Download and setup FastF1 cache from Google Drive"""
    try:
        # Create cache directory
        full_cache_dir = os.path.join(os.path.dirname(__file__), cache_dir)
        os.makedirs(full_cache_dir, exist_ok=True)
        
        # Check if cache already exists and has content
        if os.path.exists(full_cache_dir) and os.listdir(full_cache_dir):
            file_count = sum(len(files) for _, _, files in os.walk(full_cache_dir))
            if file_count > 100:  # Reasonable cache should have many files
                logger.info(f"Using existing cache with {file_count} files")
                fastf1.Cache.enable_cache(full_cache_dir)
                return True
        
        # Download cache zip
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            temp_zip_path = tmp_file.name
        
        if not download_from_google_drive(file_id, temp_zip_path):
            os.unlink(temp_zip_path)
            return False
        
        # Extract cache
        if not extract_cache_zip(temp_zip_path, full_cache_dir):
            os.unlink(temp_zip_path)
            return False
        
        # Clean up temp file
        os.unlink(temp_zip_path)
        
        # Enable FastF1 cache
        fastf1.Cache.enable_cache(full_cache_dir)
        logger.info("✓ Google Drive cache setup complete")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Google Drive cache: {str(e)}")
        return False

def create_cache_zip(cache_dir: str, output_zip: str) -> bool:
    """Create a zip file from existing cache directory for uploading to Google Drive"""
    try:
        logger.info(f"Creating cache zip: {output_zip}")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, cache_dir)
                    zipf.write(file_path, arc_name)
        
        zip_size = os.path.getsize(output_zip) / 1024 / 1024
        logger.info(f"Created cache zip: {zip_size:.1f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating cache zip: {str(e)}")
        return False

if __name__ == "__main__":
    """Utility to create a cache zip from existing cache directory"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python google_drive_data_loader.py <cache_dir> <output_zip>")
        print("Example: python google_drive_data_loader.py cache fastf1_cache.zip")
        sys.exit(1)
    
    cache_dir = sys.argv[1]
    output_zip = sys.argv[2]
    
    if not os.path.exists(cache_dir):
        print(f"Cache directory {cache_dir} does not exist")
        sys.exit(1)
    
    if create_cache_zip(cache_dir, output_zip):
        print(f"✓ Cache zip created: {output_zip}")
        print("Upload this to Google Drive and share with public read access to use as cache")
    else:
        print("✗ Failed to create cache zip")
        sys.exit(1)