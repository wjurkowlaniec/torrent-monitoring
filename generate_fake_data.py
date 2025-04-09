#!/usr/bin/env python3
"""
Generate Fake Historical Data

This script generates fake historical data for the past 7 days to demonstrate
how the website works with data over time.
"""

import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta

# Sample game and movie titles
GAME_TITLES = [
    "Elden Ring", "Baldur's Gate 3", "Cyberpunk 2077", "Red Dead Redemption 2",
    "The Witcher 3", "Grand Theft Auto V", "Hogwarts Legacy", "Starfield",
    "Diablo IV", "Call of Duty: Modern Warfare III", "Resident Evil 4",
    "Star Wars Jedi: Survivor", "Mortal Kombat 1", "Assassin's Creed Mirage",
    "Forza Horizon 5", "Dead Space", "The Last of Us Part I", "Lies of P",
    "Alan Wake 2", "Street Fighter 6"
]

MOVIE_TITLES = [
    "Dune: Part Two", "Oppenheimer", "Barbie", "The Batman", "Killers of the Flower Moon",
    "Mission: Impossible - Dead Reckoning", "John Wick: Chapter 4", "Guardians of the Galaxy Vol. 3",
    "Spider-Man: Across the Spider-Verse", "The Super Mario Bros. Movie", "Wonka",
    "The Color Purple", "Poor Things", "Aquaman and the Lost Kingdom", "Ant-Man and the Wasp: Quantumania",
    "The Marvels", "Fast X", "Creed III", "Napoleon", "Transformers: Rise of the Beasts"
]

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs("data-summary", exist_ok=True)
    os.makedirs("data", exist_ok=True)

def generate_daily_data(category, titles, start_date, days=7):
    """
    Generate daily data for a category
    
    Args:
        category (str): 'games' or 'movies'
        titles (list): List of titles
        start_date (datetime): Start date
        days (int): Number of days to generate data for
        
    Returns:
        pandas.DataFrame: Generated data
    """
    data = []
    
    for day in range(days):
        current_date = start_date - timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        timestamp = current_date.strftime("%Y%m%d_%H%M%S")
        
        # Generate data for each title with some randomness
        for title in titles:
            # Base values that increase over time (more recent = higher values)
            base_seeders = random.randint(500, 5000) + (days - day) * random.randint(50, 200)
            base_leechers = random.randint(100, 1000) + (days - day) * random.randint(10, 50)
            
            # Add some random variation
            seeders = max(1, int(base_seeders * random.uniform(0.9, 1.1)))
            leechers = max(1, int(base_leechers * random.uniform(0.9, 1.1)))
            peers = seeders + leechers
            
            data.append({
                'title': title,
                'seeders': seeders,
                'leechers': leechers,
                'peers': peers,
                'category': category,
                'date': date_str,
                'timestamp': timestamp
            })
    
    return pd.DataFrame(data)

def generate_summary_data():
    """Generate summary data for the past 7 days"""
    # Start date (today)
    end_date = datetime.now()
    
    # Generate data for games and movies
    games_data = generate_daily_data('games', GAME_TITLES, end_date)
    movies_data = generate_daily_data('movies', MOVIE_TITLES, end_date)
    
    # Combine data
    combined_data = pd.concat([games_data, movies_data], ignore_index=True)
    
    # Save to CSV
    combined_data.to_csv("data-summary/summary_data.csv", index=False)
    print(f"Generated summary data with {len(combined_data)} entries")
    
    return combined_data

def generate_rankings(df, category, period):
    """
    Generate rankings data
    
    Args:
        df (pandas.DataFrame): Summary data
        category (str): 'games' or 'movies'
        period (str): 'daily' or 'weekly'
    """
    # Get unique dates
    dates = sorted(df['date'].unique())
    
    if period == 'daily' and len(dates) >= 2:
        current_date = dates[-1]
        previous_date = dates[-2]
    elif period == 'weekly' and len(dates) >= 7:
        current_date = dates[-1]
        previous_date = dates[-7] if len(dates) >= 7 else dates[0]
    else:
        return
    
    # Filter data for the two dates
    current_data = df[(df['date'] == current_date) & (df['category'] == category)]
    previous_data = df[(df['date'] == previous_date) & (df['category'] == category)]
    
    # Sort by peers
    current_sorted = current_data.sort_values('peers', ascending=False).reset_index(drop=True)
    previous_sorted = previous_data.sort_values('peers', ascending=False).reset_index(drop=True)
    
    # Create previous rank mapping
    previous_ranks = {}
    for i, row in previous_sorted.iterrows():
        previous_ranks[row['title']] = i + 1
    
    # Calculate rankings
    rankings = []
    for i, row in current_sorted.head(20).iterrows():
        title = row['title']
        current_rank = i + 1
        
        if title in previous_ranks:
            previous_rank = previous_ranks[title]
            rank_change = previous_rank - current_rank
        else:
            previous_rank = None
            rank_change = "new"
        
        rankings.append({
            'title': title,
            'current_rank': current_rank,
            'previous_rank': previous_rank,
            'rank_change': rank_change,
            'seeders': row['seeders'],
            'leechers': row['leechers'],
            'peers': row['peers']
        })
    
    # Save to JSON
    output = {
        'period': period,
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'rankings': rankings
    }
    
    filename = f"{category}_{period}_rankings.json"
    
    # Save to data-summary and data directories
    for directory in ["data-summary", "data"]:
        output_path = os.path.join(directory, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    
    print(f"Generated {category} {period} rankings")

def generate_chart_data(df, category):
    """
    Generate chart data
    
    Args:
        df (pandas.DataFrame): Summary data
        category (str): 'games' or 'movies'
    """
    category_data = df[df['category'] == category]
    
    # Group by date and title
    daily_data = category_data.groupby(['date', 'title'])['peers'].max().reset_index()
    
    # Pivot to get titles as columns and dates as rows
    pivot_data = daily_data.pivot(index='date', columns='title', values='peers')
    
    # Fill NaN values with 0
    pivot_data = pivot_data.fillna(0)
    
    # Sort columns by the most recent values
    if not pivot_data.empty:
        most_recent_date = pivot_data.index[-1]
        sorted_columns = pivot_data.loc[most_recent_date].sort_values(ascending=False).index
        pivot_data = pivot_data[sorted_columns]
    
    # Keep only top 20 titles
    pivot_data = pivot_data.iloc[:, :20]
    
    # Convert to the format needed for charts
    chart_data = {
        'dates': pivot_data.index.tolist(),
        'titles': pivot_data.columns.tolist(),
        'data': pivot_data.values.tolist()
    }
    
    # Save to JSON
    filename = f"{category}_chart_data.json"
    
    # Save to data-summary and data directories
    for directory in ["data-summary", "data"]:
        output_path = os.path.join(directory, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, indent=2)
    
    print(f"Generated {category} chart data")

def main():
    """Main function"""
    print("Generating fake historical data...")
    ensure_directories()
    
    # Generate summary data
    df = generate_summary_data()
    
    # Generate rankings
    for category in ['games', 'movies']:
        for period in ['daily', 'weekly']:
            generate_rankings(df, category, period)
    
    # Generate chart data
    for category in ['games', 'movies']:
        generate_chart_data(df, category)
    
    print("Done! Fake data has been generated for the past 7 days.")

if __name__ == "__main__":
    main()
