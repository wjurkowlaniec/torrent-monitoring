#!/usr/bin/env python3
"""
Data Manager Module

This module handles saving, loading, and processing scraped data.
"""

import os
import csv
import json
from datetime import datetime
import pandas as pd

class DataManager:
    """Class for managing scraped data"""
    
    def __init__(self, raw_data_dir="data-raw", summary_data_dir="data-summary"):
        """
        Initialize the data manager
        
        Args:
            raw_data_dir (str): Directory for raw data
            summary_data_dir (str): Directory for summary data
        """
        self.raw_data_dir = raw_data_dir
        self.summary_data_dir = summary_data_dir
        
        # Create directories if they don't exist
        os.makedirs(raw_data_dir, exist_ok=True)
        os.makedirs(summary_data_dir, exist_ok=True)
    
    def save_raw_data(self, data, category):
        """
        Save raw data to CSV
        
        Args:
            data (list): List of dictionaries containing scraped data
            category (str): Category of data (e.g., 'games', 'movies')
            
        Returns:
            str: Path to the saved file
        """
        if not data:
            print(f"No {category} data to save.")
            return None
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.raw_data_dir, f"{category}_raw_{timestamp}.csv")
        
        # Write data to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'clean_title', 'seeders', 'leechers', 'total_peers', 'category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in data:
                writer.writerow(item)
        
        print(f"Raw {category} data saved to {filename}")
        return filename
    
    def save_grouped_data(self, grouped_data, category):
        """
        Save grouped data to CSV
        
        Args:
            grouped_data (list): List of dictionaries containing grouped data
            category (str): Category of data (e.g., 'games', 'movies')
            
        Returns:
            str: Path to the saved file
        """
        if not grouped_data:
            print(f"No grouped {category} data to save.")
            return None
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.raw_data_dir, f"{category}_grouped_{timestamp}.csv")
        
        # Write data to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['main_title', 'total_seeders', 'total_leechers', 'total_peers']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for group in grouped_data:
                writer.writerow({
                    'main_title': group['representative']['clean_title'],
                    'total_seeders': group['total_seeders'],
                    'total_leechers': group['total_leechers'],
                    'total_peers': group['total_peers']
                })
        
        print(f"Grouped {category} data saved to {filename}")
        return filename
    
    def update_summary_data(self, _, grouped_data, category):
        """
        Update summary data with new scraped data
        
        Args:
            raw_data (list): List of dictionaries containing raw scraped data
            grouped_data (list): List of dictionaries containing grouped data
            category (str): Category of data (e.g., 'games', 'movies')
            
        Returns:
            str: Path to the saved summary file
        """
        # Current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create summary data for the current scrape
        current_summary = []
        for group in grouped_data:
            current_summary.append({
                'title': group['representative']['clean_title'],
                'seeders': group['total_seeders'],
                'leechers': group['total_leechers'],
                'peers': group['total_peers'],
                'category': category,
                'date': current_date,
                'timestamp': timestamp
            })
        
        # Load existing summary data if available
        summary_file = os.path.join(self.summary_data_dir, "summary_data.csv")
        
        if os.path.exists(summary_file):
            # Read existing data
            existing_data = pd.read_csv(summary_file)
            
            # Convert current summary to DataFrame
            current_df = pd.DataFrame(current_summary)
            
            # Append new data
            combined_df = pd.concat([existing_data, current_df], ignore_index=True)
        else:
            # Create new DataFrame if no existing data
            combined_df = pd.DataFrame(current_summary)
        
        # Save updated summary data
        combined_df.to_csv(summary_file, index=False)
        print(f"Summary data updated at {summary_file}")
        
        # Generate daily rankings
        self._generate_daily_rankings(combined_df)
        
        # Generate weekly rankings
        self._generate_weekly_rankings(combined_df)
        
        return summary_file
    
    def _generate_daily_rankings(self, df):
        """
        Generate daily rankings from summary data
        
        Args:
            df (pandas.DataFrame): Summary data
        """
        # Get unique dates
        dates = df['date'].unique()
        
        # If we have at least 2 dates, calculate daily changes
        if len(dates) >= 2:
            # Sort dates and get the two most recent dates
            sorted_dates = sorted(dates)
            current_date = sorted_dates[-1]
            previous_date = sorted_dates[-2]
            
            # Filter data for the two dates
            current_data = df[df['date'] == current_date]
            previous_data = df[df['date'] == previous_date]
            
            # Calculate rankings for each category
            for category in ['games', 'movies']:
                self._calculate_ranking_changes(
                    current_data[current_data['category'] == category],
                    previous_data[previous_data['category'] == category],
                    f"{category}_daily_rankings.json",
                    "daily"
                )
    
    def _generate_weekly_rankings(self, df):
        """
        Generate weekly rankings from summary data
        
        Args:
            df (pandas.DataFrame): Summary data
        """
        # Get unique dates
        dates = df['date'].unique()
        
        # If we have at least 7 dates, calculate weekly changes
        if len(dates) >= 7:
            # Sort dates and get the current date and the date 7 days ago
            sorted_dates = sorted(dates)
            current_date = sorted_dates[-1]
            
            # Find a date approximately 7 days ago
            # This is a simplification; in a real implementation, you'd want to be more precise
            if len(sorted_dates) >= 7:
                previous_date = sorted_dates[-7]
            else:
                previous_date = sorted_dates[0]
            
            # Filter data for the two dates
            current_data = df[df['date'] == current_date]
            previous_data = df[df['date'] == previous_date]
            
            # Calculate rankings for each category
            for category in ['games', 'movies']:
                self._calculate_ranking_changes(
                    current_data[current_data['category'] == category],
                    previous_data[previous_data['category'] == category],
                    f"{category}_weekly_rankings.json",
                    "weekly"
                )
    
    def _calculate_ranking_changes(self, current_data, previous_data, output_filename, period):
        """
        Calculate ranking changes between two datasets
        
        Args:
            current_data (pandas.DataFrame): Current data
            previous_data (pandas.DataFrame): Previous data
            output_filename (str): Filename for output JSON
            period (str): Period for the rankings (e.g., 'daily', 'weekly')
        """
        # Sort by peers (descending)
        current_sorted = current_data.sort_values('peers', ascending=False).reset_index(drop=True)
        previous_sorted = previous_data.sort_values('peers', ascending=False).reset_index(drop=True)
        
        # Create a mapping of title to previous rank
        previous_ranks = {}
        for i, row in previous_sorted.iterrows():
            previous_ranks[row['title']] = i + 1  # 1-based ranking
        
        # Calculate changes for current top items
        rankings = []
        for i, row in current_sorted.head(20).iterrows():
            title = row['title']
            current_rank = i + 1  # 1-based ranking
            
            # Get previous rank or mark as new
            if title in previous_ranks:
                previous_rank = previous_ranks[title]
                rank_change = previous_rank - current_rank  # Positive means improved rank
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
        output_path = os.path.join(self.summary_data_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'period': period,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'rankings': rankings
            }, f, indent=2)
        
        print(f"{period.capitalize()} rankings saved to {output_path}")
    
    def generate_chart_data(self):
        """
        Generate data for charts
        
        This creates JSON files with historical data for charting
        """
        # Load summary data
        summary_file = os.path.join(self.summary_data_dir, "summary_data.csv")
        
        if not os.path.exists(summary_file):
            print("No summary data available for generating charts")
            return
        
        df = pd.read_csv(summary_file)
        
        # Generate chart data for each category
        for category in ['games', 'movies']:
            category_data = df[df['category'] == category]
            
            # Group by date and title, and calculate the max peers for each day
            # This handles multiple scrapes per day by taking the maximum value
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
            output_path = os.path.join(self.summary_data_dir, f"{category}_chart_data.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, indent=2)
            
            print(f"Chart data for {category} saved to {output_path}")
