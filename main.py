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
from scrapers.base_scraper import get_movie_grouping_key, get_game_grouping_key
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
        # --- Custom Game Grouping Logic ---
        game_groups = {}
        for game in games_data:
            current_peers = game.get('seeders', 0) + game.get('leechers', 0)
            grouping_key, display_title = get_game_grouping_key(game['title'])
            
            if grouping_key not in game_groups:
                game_groups[grouping_key] = {
                    'display_title': display_title,
                    'torrents': [],
                    'total_seeders': 0,
                    'total_leechers': 0,
                    'total_peers': 0
                }
            
            game_groups[grouping_key]['torrents'].append(game)
            game_groups[grouping_key]['total_seeders'] += game.get('seeders', 0)
            game_groups[grouping_key]['total_leechers'] += game.get('leechers', 0)
            game_groups[grouping_key]['total_peers'] += current_peers

        games_grouped = []
        for _, group_data in game_groups.items():
            if not group_data['torrents']: continue
            
            representative_game = max(group_data['torrents'], key=lambda x: x.get('seeders', 0) + x.get('leechers', 0))
            representative_game_copy = representative_game.copy()
            representative_game_copy['clean_title'] = group_data['display_title']

            games_grouped.append({
                'representative': representative_game_copy,
                'total_seeders': group_data['total_seeders'],
                'total_leechers': group_data['total_leechers'],
                'total_peers': group_data['total_peers'],
                'torrents': group_data['torrents']
            })
        # --- End Custom Grouping ---
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
        # --- Custom Movie Grouping Logic ---
        movie_groups = {}
        for movie in movies_data:
            # Calculate peers for this item (without modifying the dict)
            current_peers = movie.get('seeders', 0) + movie.get('leechers', 0)
            # Get both the key for grouping and the prefix for display
            grouping_key, display_prefix = get_movie_grouping_key(movie['title'])
            
            if grouping_key not in movie_groups:
                movie_groups[grouping_key] = {
                    'display_prefix': display_prefix, # Store the prefix for the group
                    'torrents': [],
                    'total_seeders': 0,
                    'total_leechers': 0,
                    'total_peers': 0
                }
            
            # Store original movie dict
            movie_groups[grouping_key]['torrents'].append(movie)
            # Add to totals
            movie_groups[grouping_key]['total_seeders'] += movie.get('seeders', 0)
            movie_groups[grouping_key]['total_leechers'] += movie.get('leechers', 0)
            movie_groups[grouping_key]['total_peers'] += current_peers

        movies_grouped = []
        for _, group_data in movie_groups.items():
            if not group_data['torrents']: continue # Skip empty groups
            
            # Select representative (e.g., highest peers, calculate peers on the fly)
            # Note: representative_movie is still one of the original dicts
            representative_movie = max(group_data['torrents'], key=lambda x: x.get('seeders', 0) + x.get('leechers', 0))
            
            # Create a copy to avoid modifying the original dict in movies_data
            representative_movie_copy = representative_movie.copy()
            # Set the 'clean_title' to the stored display_prefix for the group
            representative_movie_copy['clean_title'] = group_data['display_prefix'] 

            movies_grouped.append({
                # Use the modified copy as the representative
                'representative': representative_movie_copy, 
                'total_seeders': group_data['total_seeders'],
                'total_leechers': group_data['total_leechers'],
                'total_peers': group_data['total_peers'],
                'torrents': group_data['torrents'] # Keep the list of original torrents if needed later
            })
        # --- End Custom Grouping ---
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
