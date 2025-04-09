#!/usr/bin/env python3
"""
1337x Top Games Scraper

This script scrapes the top 100 games from 1337x.to and extracts information about each game,
including title and the combined number of seeders and leechers. It also groups similar game titles
to consolidate information about the same game across different versions or releases.
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import os
import random
import re
from difflib import SequenceMatcher
from collections import defaultdict

# Define user agents to rotate and avoid being blocked
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
]

def get_random_user_agent():
    """Return a random user agent from the list."""
    return random.choice(USER_AGENTS)

def scrape_top_games(url="https://1337x.to/top-100-games"):
    """
    Scrape the top games from 1337x.to
    
    Args:
        url (str): URL to scrape
        
    Returns:
        list: List of dictionaries containing game information
    """
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # Add a delay to be respectful to the server
        time.sleep(2)
        
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing the game list
        table = soup.find('table', class_='table-list')
        if not table:
            print("Could not find the table with games. The website structure might have changed.")
            return []
        
        # Extract rows (skip the header row)
        rows = table.find_all('tr')[1:]
        
        games_data = []
        for row in rows:
            try:
                # Extract columns
                columns = row.find_all('td')
                
                # Extract title
                title_element = columns[0].find('a', href=lambda href: href and '/torrent/' in href)
                title = title_element.text.strip() if title_element else "Unknown Title"
                
                # Extract seeders and leechers
                seeders = int(columns[1].text.strip())
                leechers = int(columns[2].text.strip())
                total_peers = seeders + leechers
                
                games_data.append({
                    'title': title,
                    'seeders': seeders,
                    'leechers': leechers,
                    'total_peers': total_peers
                })
            except (IndexError, AttributeError) as e:
                print(f"Error processing a row: {e}")
                continue
        
        return games_data
    
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        return []

def clean_game_title(title, for_display=False):
    """
    Clean and normalize game title for better matching or display
    
    Args:
        title (str): Original game title
        for_display (bool): If True, clean the title for display purposes
                           If False, clean for matching purposes
        
    Returns:
        str: Cleaned game title
    """
    # Remove common patterns in game titles that indicate versions, repacks, etc.
    patterns = [
        r'\(v[\d\.]+.*?\)',  # Version numbers like (v1.2.3)
        r'v[\d\.]+',  # Version numbers like v1.2.3
        r'\[.*?\]',  # Content in square brackets
        r'\(.*?\)',  # Content in parentheses
        r'Update.*$',  # Updates
        r'Repack',  # Repacks
        r'MULTi\d+',  # Multi-language indicators
        r'DLC',  # DLC mentions
        r'\+.*$',  # Everything after a plus sign
    ]
    
    # Additional patterns for display cleaning (more aggressive)
    display_patterns = [
        r'-[^-]*$',  # Everything after the last hyphen if it's not part of the name
        r'\s*:\s*$',  # Trailing colons with optional spaces
        r'\s*-\s*$',  # Trailing hyphens with optional spaces
    ]
    
    cleaned = title
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Apply additional cleaning for display purposes
    if for_display:
        # Special case for "Edition" - keep it if it's part of the title
        if "Edition" in cleaned:
            # Keep "Edition" in the title
            pass
        
        # Special case for titles with hyphens that are part of the name
        # Don't remove hyphens from titles like "Spider-Man"
        for pattern in display_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove extra whitespace and normalize
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Return lowercase for matching, original case for display
    return cleaned.lower() if not for_display else cleaned

def calculate_similarity(title1, title2):
    """
    Calculate similarity between two game titles
    
    Args:
        title1 (str): First game title
        title2 (str): Second game title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Clean titles first (for matching, not display)
    clean_title1 = clean_game_title(title1, for_display=False)
    clean_title2 = clean_game_title(title2, for_display=False)
    
    # Use SequenceMatcher for similarity calculation
    return SequenceMatcher(None, clean_title1, clean_title2).ratio()

def group_similar_games(games_data, similarity_threshold=0.6):
    """
    Group similar games together based on title similarity
    
    Args:
        games_data (list): List of dictionaries containing game information
        similarity_threshold (float): Threshold for considering games similar
        
    Returns:
        list: List of dictionaries containing grouped game information
    """
    if not games_data:
        return []
    
    # Sort games by total peers (descending) to prioritize more popular versions
    sorted_games = sorted(games_data, key=lambda x: x['total_peers'], reverse=True)
    
    # Initialize groups with the first game
    groups = []
    processed_indices = set()
    
    # For each game, try to find a group or create a new one
    for i, game in enumerate(sorted_games):
        if i in processed_indices:
            continue
            
        # Create a new group with this game as the representative
        current_group = {
            'representative': game,
            'titles': [game['title']],
            'total_seeders': game['seeders'],
            'total_leechers': game['leechers'],
            'total_peers': game['total_peers'],
            'versions': [game]
        }
        processed_indices.add(i)
        
        # Find similar games
        for j, other_game in enumerate(sorted_games):
            if j in processed_indices or i == j:
                continue
                
            similarity = calculate_similarity(game['title'], other_game['title'])
            if similarity >= similarity_threshold:
                current_group['titles'].append(other_game['title'])
                current_group['total_seeders'] += other_game['seeders']
                current_group['total_leechers'] += other_game['leechers']
                current_group['total_peers'] += other_game['total_peers']
                current_group['versions'].append(other_game)
                processed_indices.add(j)
        
        groups.append(current_group)
    
    return groups

def save_to_csv(games_data, grouped_games=None, output_dir="data"):
    """
    Save the games data to CSV files
    
    Args:
        games_data (list): List of dictionaries containing game information
        grouped_games (list): List of dictionaries containing grouped game information
        output_dir (str): Directory to save the CSV files
    """
    if not games_data:
        print("No data to save.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw data
    raw_filename = os.path.join(output_dir, f"top_games_raw_{timestamp}.csv")
    with open(raw_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'seeders', 'leechers', 'total_peers']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for game in games_data:
            writer.writerow(game)
    
    print(f"Raw data saved to {raw_filename}")
    
    # Save grouped data if available
    if grouped_games:
        grouped_filename = os.path.join(output_dir, f"top_games_grouped_{timestamp}.csv")
        with open(grouped_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['main_title', 'total_seeders', 'total_leechers', 'total_peers']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for group in grouped_games:
                # Clean the title for display
                clean_title = clean_game_title(group['representative']['title'], for_display=True)
                writer.writerow({
                    'main_title': clean_title,
                    'total_seeders': group['total_seeders'],
                    'total_leechers': group['total_leechers'],
                    'total_peers': group['total_peers']
                })
        
        print(f"Grouped data saved to {grouped_filename}")
        return grouped_filename
    
    return raw_filename

def main():
    print("Starting to scrape top games from 1337x.to...")
    games_data = scrape_top_games()
    
    if games_data:
        print(f"Successfully scraped {len(games_data)} games.")
        
        # Group similar games
        print("Grouping similar games...")
        grouped_games = group_similar_games(games_data)
        print(f"Grouped into {len(grouped_games)} unique games.")
        
        # Save both raw and grouped data
        csv_file = save_to_csv(games_data, grouped_games)
        
        # Print the top 5 grouped games by total peers
        print("\nTop 5 grouped games by total peers (seeders + leechers):")
        sorted_groups = sorted(grouped_games, key=lambda x: x['total_peers'], reverse=True)
        for i, group in enumerate(sorted_groups[:5], 1):
            versions_count = len(group['versions'])
            versions_text = f"({versions_count} version{'s' if versions_count > 1 else ''})" if versions_count > 1 else ""
            clean_title = clean_game_title(group['representative']['title'], for_display=True)
            print(f"{i}. {clean_title} {versions_text} - {group['total_peers']} peers ({group['total_seeders']} seeders, {group['total_leechers']} leechers)")
            
            # If there are multiple versions, show them
            if versions_count > 1:
                print("   Versions:")
                for j, version in enumerate(group['versions'], 1):
                    print(f"   {j}. {version['title']} - {version['total_peers']} peers ({version['seeders']} seeders, {version['leechers']} leechers)")
    else:
        print("Failed to scrape games data.")

if __name__ == "__main__":
    main()
