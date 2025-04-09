#!/bin/bash

# Setup script for torrent games scraper scheduled job
# This script will install PM2 if not already installed and set up the scheduled job

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm first."
    echo "Visit https://nodejs.org/ to download and install Node.js"
    exit 1
fi

# Check if PM2 is installed globally
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2 globally..."
    npm install -g pm2
fi

# Check if required Python packages are installed
echo "Checking required Python packages..."
pip install -r requirements.txt

# Start the PM2 process
echo "Setting up PM2 scheduled job..."
pm2 start ecosystem.config.js

# Save the PM2 process list
echo "Saving PM2 process list..."
pm2 save

# Setup PM2 to start on system boot (optional)
echo "To set up PM2 to start on system boot, run the following command:"
echo "pm2 startup"
echo "Then follow the instructions provided by the command."

echo ""
echo "Job setup complete! The scraper will run every 12 hours."
echo "To check the status of the job, run: pm2 status"
echo "To view logs, run: pm2 logs torrent-games-scraper"
echo "To stop the job, run: pm2 stop torrent-games-scraper"
