# Imports
import feedparser
import os
import time
import shutil
from transmissionrpc import Client
from pathlib import Path
import requests
import json
from urllib3.exceptions import InsecureRequestWarning
import warnings
from datetime import datetime
import logging

# Before running make sure to store the Program files in "/var/lib/transmission-daemon/downloads"
# to avoid permission problems

# Suppress insecure HTTPS warnings
warnings.simplefilter('ignore', InsecureRequestWarning)

# Configuration
RSS_URL = "https://yts.mx/rss/0/1080p/all/4/en"  # Replace with your RSS feed URL
EXPORT_DIRECTORY = "Directory Where you want to store the .mp4 files"  # Replace with your desired export path
# LOG files used for user refrence and to prevent multiples
LOG_FILE = "/var/lib/transmission-daemon/downloads/download_history.log"
DOWNLOAD_HISTORY = "/var/lib/transmission-daemon/downloads/download_history.json"

class TorrentManager:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize transmission client
            self.transmission = Client(
                address='localhost',
                port=9091,
# Replace if you have changed the default Username and Password
                user='transmission',
                password='transmission'
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to transmission: {e}")
            raise
        
        # Set up directories
        self.base_dir = Path("/var/lib/transmission-daemon/downloads")
        self.export_dir = Path(EXPORT_DIRECTORY)
        
        # Create export directory if it doesn't exist
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Load download history
        self.download_history = self.load_history()

    def load_history(self):
        """Load download history from JSON file"""
        try:
            if os.path.exists(DOWNLOAD_HISTORY):
                with open(DOWNLOAD_HISTORY, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading download history: {e}")
            return {}

    def save_history(self):
        """Save download history to JSON file"""
        try:
            with open(DOWNLOAD_HISTORY, 'w') as f:
                json.dump(self.download_history, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving download history: {e}")

    def is_already_downloaded(self, title, url):
        """Check if torrent has already been downloaded"""
        return url in self.download_history

    def add_to_history(self, title, url):
        """Add downloaded torrent to history"""
        self.download_history[url] = {
            'title': title,
            'timestamp': datetime.now().isoformat()
        }
        self.save_history()

    def get_torrent_url(self, item):
        """Extract the torrent URL from the RSS item's enclosure"""
        if hasattr(item, 'enclosures') and item.enclosures:
            return item.enclosures[0].get('href', '')
        return None

    def download_torrent_file(self, url):
        """Download torrent file and save it temporarily"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            
            temp_path = self.base_dir / "temp.torrent"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"Error downloading torrent file: {e}")
            return None

    def add_torrent(self, torrent_url):
        """Add torrent to transmission"""
        try:
            if torrent_url.startswith('magnet:?'):
                torrent = self.transmission.add_torrent(
                    torrent_url,
                    download_dir=str(self.base_dir)
                )
            else:
                temp_torrent_path = self.download_torrent_file(torrent_url)
                
                if not temp_torrent_path:
                    raise Exception("Failed to download torrent file")
                
                try:
                    torrent = self.transmission.add_torrent(
                        'file://' + temp_torrent_path,
                        download_dir=str(self.base_dir)
                    )
                finally:
                    if os.path.exists(temp_torrent_path):
                        os.remove(temp_torrent_path)
            
            return torrent
            
        except Exception as e:
            raise Exception(f"Failed to add torrent: {e}")

    def monitor_torrent(self, torrent):
        """Monitor torrent progress and handle completion"""
        self.logger.info(f"Starting download of: {torrent.name}")
        
        while True:
            try:
                torrent.update()
                if torrent.progress >= 100:
                    self.logger.info(f"Download complete for: {torrent.name}")
                    self.transmission.remove_torrent(torrent.id, delete_data=False)
                    break
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Error monitoring torrent: {e}")
                break

# Move the import :) movie files to directory specifed above 
# run cleanup.py to remove trash made from torrents downloading
    def move_mp4_files(self):
        """Move all .mp4 files to export directory"""
        for file in self.base_dir.glob("**/*.mp4"):
            try:
                target_path = self.export_dir / file.name
                shutil.move(str(file), str(target_path))
                self.logger.info(f"Moved {file.name} to export directory")
            except Exception as e:
                self.logger.error(f"Error moving file {file.name}: {e}")

    def process_feed(self):
        """Process RSS feed and download new torrents"""
        try:
            feed = feedparser.parse(RSS_URL)
            
            for item in feed.entries:
                title = item.title
                torrent_url = self.get_torrent_url(item)
                
                if not torrent_url:
                    self.logger.warning(f"No torrent URL found for {title}")
                    continue
                
                # Check if it's a 1080p release and hasn't been downloaded
                if '[1080p]' in title and not self.is_already_downloaded(title, torrent_url):
                    self.logger.info(f"New 1080p release found: {title}")
                    
                    try:
                        torrent = self.add_torrent(torrent_url)
                        self.monitor_torrent(torrent)
                        self.add_to_history(title, torrent_url)
                        self.move_mp4_files()
                    except Exception as e:
                        self.logger.error(f"Error processing torrent {title}: {e}")
                
        except Exception as e:
            self.logger.error(f"Error processing RSS feed: {e}")

    def run_continuously(self):
        """Run the feed checker continuously"""
        self.logger.info("Starting automatic torrent manager")
        
        while True:
            try:
                self.process_feed()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying if there's an error

if __name__ == "__main__":
    manager = TorrentManager()
    manager.run_continuously()