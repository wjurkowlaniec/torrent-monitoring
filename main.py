#!/usr/bin/env python3
"""
Torrent Monitoring Dashboard

This script scrapes top games and movies from 1337x.to and generates a dashboard.
"""

import argparse
from datetime import datetime
import subprocess
from scrapers.games_scraper import GamesScraper
from scrapers.movies_scraper import MoviesScraper
from data_manager import DataManager

def scrape_data():
    """
    Scrape data from the torrent website
    
    Returns:
        tuple: (games_data, games_grouped, movies_data, movies_grouped)
    """
    # Scrape games data
    print("Starting to scrape top games from 1337x.to...")
    games_scraper = GamesScraper()
    games_data = games_scraper.scrape()
    
    if games_data:
        print(f"Successfully scraped {len(games_data)} games.")
        games_grouped = games_scraper.group_similar_items(games_data)
        print(f"Grouped into {len(games_grouped)} unique games.")
    else:
        games_grouped = []
        print("Failed to scrape games data.")
    
    # Scrape movies data
    print("\nStarting to scrape top movies from 1337x.to...")
    movies_scraper = MoviesScraper()
    movies_data = movies_scraper.scrape()
    
    if movies_data:
        print(f"Successfully scraped {len(movies_data)} movies.")
        movies_grouped = movies_scraper.group_similar_items(movies_data)
        print(f"Grouped into {len(movies_grouped)} unique movies.")
    else:
        movies_grouped = []
        print("Failed to scrape movies data.")
    
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

def push_to_github():
    """
    Push the updated data and website to GitHub
    Note: This function is kept for manual usage, but GitHub Actions
    will handle the push automatically when running in the cloud.
    """
    try:
        # Add all files
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Update data and website - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "master"], check=True)
        
        print("Successfully pushed updates to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing to GitHub: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Torrent Monitoring Tool")
    parser.add_argument("--push", action="store_true", help="Push to GitHub (only needed for local runs)")
    args = parser.parse_args()
    
    # Run scrapers
    games_data, games_grouped, movies_data, movies_grouped = scrape_data()
    
    # Save data
    save_data(games_data, games_grouped, movies_data, movies_grouped)
    

    # Push to GitHub only if explicitly requested (for local runs)
    # GitHub Actions will handle this automatically
    if args.push:
        push_to_github()
    
    print("Done!")

if __name__ == "__main__":
    main()
