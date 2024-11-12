
# Automated Torrent Manager

This project is designed to automatically download torrents from the YTS.mx RSS feed using Transmission and manage the downloaded files. The script will monitor the RSS feed, download new torrents, and move the .mp4 files to a specified directory.

## Prerequisites

Before you begin, you'll need to install the following packages:

```sh
sudo apt-get update
sudo apt-get install -y transmission-daemon python3 python3-pip

Additionally, install the required Python packages using the requirements.txt file:

pip3 install -r requirements.txt

Configuration
1. RSS Feed URL: Replace RSS_URL in main.py with your desired RSS feed URL.

2. Export Directory: Replace EXPORT_DIRECTORY in main.py with your desired export path.

3. Download History: Replace DOWNLOAD_HISTORY in main.py with the path where you want to store the download history JSON file.

Changing Transmission Default Username and Password
To change the default username and password for Transmission's web UI, follow these steps:

sudo systemctl stop transmission-daemon
sudo nano /etc/transmission-daemon/settings.json

Find and update the following fields:

"rpc-username": "your-username",
"rpc-password": "your-password",
"rpc-whitelist-enabled": false,

Save the changes and restart the Transmission daemon:

sudo systemctl start transmission-daemon

Allow Access to the Public IP Address
To allow access to Transmission's web UI from a public IP address, update the following field in the settings.json file:

"rpc-bind-address": "0.0.0.0",

Running the Script
Store the program in /var/lib/transmission-daemon/downloads.

Running the Script as a Service
Create the service file:

sudo nano /etc/systemd/system/torrent-manager.service

Add the following content:

[Unit]
Description=Automated Torrent Manager
After=network.target transmission-daemon.service

[Service]
Type=simple
User=debian-transmission
Group=debian-transmission
ExecStart=/usr/bin/python3 /var/lib/transmission-daemon/downloads/torrent_manager.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target

Start the service:

sudo systemctl daemon-reload
sudo systemctl enable torrent-manager
sudo systemctl start torrent-manager

Monitor the logs:

tail -f /var/lib/transmission-daemon/downloads/download_history.log

Notes
Make sure to adjust the paths and configurations according to your setup. The script will continuously monitor the RSS feed and download new torrents as they are published.
