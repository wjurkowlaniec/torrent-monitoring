#!/usr/bin/env python3
"""
Main Script for Torrent Monitoring

This script runs the scrapers, processes the data, and updates the website.
"""

import os
import argparse
from datetime import datetime
import subprocess

from scrapers.games_scraper import GamesScraper
from scrapers.movies_scraper import MoviesScraper
from data_manager import DataManager

def run_scrapers():
    """
    Run the scrapers to collect data
    
    Returns:
        tuple: (games_data, games_grouped, movies_data, movies_grouped)
    """
    print("Starting to scrape top games from 1337x.to...")
    games_scraper = GamesScraper()
    games_data = games_scraper.scrape()
    
    if games_data:
        print(f"Successfully scraped {len(games_data)} games.")
        games_grouped = games_scraper.group_similar_items(games_data)
        print(f"Grouped into {len(games_grouped)} unique games.")
    else:
        print("Failed to scrape games data.")
        games_grouped = []
    
    print("\nStarting to scrape top movies from 1337x.to...")
    movies_scraper = MoviesScraper()
    movies_data = movies_scraper.scrape()
    
    if movies_data:
        print(f"Successfully scraped {len(movies_data)} movies.")
        movies_grouped = movies_scraper.group_similar_items(movies_data)
        print(f"Grouped into {len(movies_grouped)} unique movies.")
    else:
        print("Failed to scrape movies data.")
        movies_grouped = []
    
    return games_data, games_grouped, movies_data, movies_grouped

def save_data(games_data, games_grouped, movies_data, movies_grouped):
    """
    Save the scraped data
    
    Args:
        games_data (list): Raw games data
        games_grouped (list): Grouped games data
        movies_data (list): Raw movies data
        movies_grouped (list): Grouped movies data
    """
    data_manager = DataManager()
    
    # Save raw data
    if games_data:
        data_manager.save_raw_data(games_data, "games")
    if movies_data:
        data_manager.save_raw_data(movies_data, "movies")
    
    # Save grouped data
    if games_grouped:
        data_manager.save_grouped_data(games_grouped, "games")
    if movies_grouped:
        data_manager.save_grouped_data(movies_grouped, "movies")
    
    # Update summary data
    if games_data and games_grouped:
        data_manager.update_summary_data(games_data, games_grouped, "games")
    if movies_data and movies_grouped:
        data_manager.update_summary_data(movies_data, movies_grouped, "movies")
    
    # Generate chart data
    data_manager.generate_chart_data()

def update_website():
    """
    Update the website files with the latest data
    """
    # Copy the latest data files to the website directory
    os.makedirs("website/data", exist_ok=True)
    
    # Copy all JSON files from data-summary to website/data
    data_dir = "data-summary"
    website_data_dir = "website/data"
    
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            source_path = os.path.join(data_dir, filename)
            dest_path = os.path.join(website_data_dir, filename)
            with open(source_path, 'r', encoding='utf-8') as source_file:
                with open(dest_path, 'w', encoding='utf-8') as dest_file:
                    dest_file.write(source_file.read())
    
    print("Website data files updated.")

def push_to_github():
    """
    Push the updated data and website to GitHub
    """
    try:
        # Add all files
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Update data and website - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("Successfully pushed updates to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing to GitHub: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Torrent Monitoring Tool")
    parser.add_argument("--no-push", action="store_true", help="Don't push to GitHub")
    args = parser.parse_args()
    
    # Run scrapers
    games_data, games_grouped, movies_data, movies_grouped = run_scrapers()
    
    # Save data
    save_data(games_data, games_grouped, movies_data, movies_grouped)
    
    # Update website
    update_website()
    
    # Push to GitHub if not disabled
    if not args.no_push:
        push_to_github()
    
    print("Done!")

if __name__ == "__main__":
    main()
