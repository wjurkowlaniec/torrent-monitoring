#!/usr/bin/env python3
"""
Data Manager Module

This module handles saving, loading, and processing scraped data.
"""

import os
import csv
import json
# Make sure pandas errors are accessible
try:
    from pandas.errors import ParserError
except ImportError: # Older pandas versions might not have this specific error separated
    ParserError = ValueError
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
        # Current timestamp in ISO 8601 format
        timestamp_iso = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
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
                'timestamp': timestamp_iso,
            })
        
        # Convert the list of new summary data points to a DataFrame
        new_df = pd.DataFrame(current_summary)

        # Append new data to summary file
        summary_file = os.path.join(self.summary_data_dir, "summary_data.csv")
        file_exists = os.path.exists(summary_file)
        new_df.to_csv(
            summary_file, 
            mode='a', 
            header=not file_exists, # Write header only if file doesn't exist
            index=False, 
            encoding='utf-8'
            # No date_format needed as we write ISO strings
        )
        print(f"Summary data updated at {summary_file}")

        # Load the *complete* updated data for ranking generation
        try:
            full_summary_df = pd.read_csv(summary_file)
            # Generate daily rankings
            self._generate_daily_rankings(full_summary_df)
            # Generate weekly rankings
            self._generate_weekly_rankings(full_summary_df)
        except Exception as e:
            print(f"Error reading full summary file {summary_file} after update for ranking generation: {e}")
        
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
                    'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), # ISO Format
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
        df = None # Initialize df to handle case where file reading fails completely

        try:
            # Read CSV without initial date parsing
            df = pd.read_csv(summary_file)

            # Explicitly convert ISO string timestamp column to datetime, coercing errors to NaT
            # Attempt parsing ISO 8601 format; this is often default but specifying can help
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='ISO8601')

            # Check for NaT values (from read or explicit conversion) and drop them
            initial_rows = len(df)
            df.dropna(subset=['timestamp'], inplace=True) # Drops rows where parsing failed (NaT)
            dropped_rows = initial_rows - len(df)
            if dropped_rows > 0:
                 print(f"Warning: Dropped {dropped_rows} rows from {summary_file} due to invalid/unparseable timestamps during read.")

        except FileNotFoundError: # Use specific exception
             print(f"Error: Summary file {summary_file} not found. Skipping chart generation.")
             return
        except (ValueError, TypeError, ParserError) as e:
            print(f"Warning: Error reading {summary_file}: {e}. Attempting to delete corrupted file and skipping chart generation.")
            try:
                # Check if file exists before attempting removal
                if os.path.exists(summary_file):
                    os.remove(summary_file)
                    print(f"Successfully deleted potentially corrupted {summary_file}")
                else:
                    print(f"File {summary_file} not found, cannot delete.")
            except OSError as remove_error:
                print(f"Error deleting file {summary_file}: {remove_error}")
            return # Exit the function since we can't generate charts
        except Exception as e: # Catch other potential errors during read/initial processing
            print(f"An unexpected error occurred while processing {summary_file}: {e}. Skipping chart generation.")
            return

        # Check if df is None (file not found or other major error) or empty after processing
        if df is None or df.empty:
             print(f"Warning: No valid timestamp data loaded from {summary_file}. Skipping chart generation.")
             return

        # Generate chart data for each category
        for category in ['games', 'movies']:
            category_data = df[df['category'] == category]
            
            # Use pivot_table to handle potential duplicate timestamps for a title
            # We use 'timestamp' directly for the index to preserve time information
            pivot_data = pd.pivot_table(category_data, values='peers', index='timestamp', columns='title', aggfunc='max')
            
            # Fill NaN values with 0
            pivot_data = pivot_data.fillna(0)

            # Sort columns by the most recent values
            if not pivot_data.empty:
                most_recent_timestamp = pivot_data.index[-1]
                try:
                    # Ensure the timestamp exists in the index before accessing
                    if most_recent_timestamp in pivot_data.index:
                        sorted_columns = pivot_data.loc[most_recent_timestamp].sort_values(ascending=False).index
                        pivot_data = pivot_data[sorted_columns]
                    else:
                        print(f"Warning: Most recent timestamp {most_recent_timestamp} not found in pivot_data index for sorting.")
                except KeyError:
                     print(f"Warning: KeyError accessing {most_recent_timestamp} for sorting columns.")

            # Keep only top 20 titles
            pivot_data = pivot_data.iloc[:, :20]

            # Convert to the format needed for charts
            # Convert datetime index to ISO format strings
            iso_dates = [ts.strftime('%Y-%m-%dT%H:%M:%S') for ts in pivot_data.index] # Apply strftime to each timestamp

            chart_data = {
                'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), # ISO Format
                'dates': iso_dates, # Use ISO formatted timestamps
                'titles': pivot_data.columns.tolist(),
                'data': pivot_data.values.tolist()
            }
            
            # Define output path
            output_path = os.path.join(self.summary_data_dir, f"{category}_chart_data.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, indent=2)
            
            print(f"Chart data for {category} saved to {output_path}")
