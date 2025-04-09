#!/usr/bin/env python3
"""
Archive Scraper Module

This module provides functionality for scraping web archives instead of directly
accessing potentially blocked websites. It attempts to retrieve data from various
archive services like the Wayback Machine.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote

class ArchiveScraper:
    """Class for scraping web archives"""
    
    def __init__(self, target_url, category):
        """
        Initialize the archive scraper
        
        Args:
            target_url (str): Original URL that would be blocked
            category (str): Category to scrape (e.g., 'games', 'movies')
        """
        self.target_url = target_url
        self.category = category
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def get_random_user_agent(self):
        """Return a random user agent"""
        return random.choice(self.user_agents)
    
    def get_headers(self):
        """Get headers for HTTP requests"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def try_wayback_machine(self):
        """
        Try to get data from the Wayback Machine
        
        Returns:
            BeautifulSoup or None: Parsed HTML if successful, None otherwise
        """
        print(f"Trying to fetch data from Wayback Machine for {self.target_url}")
        
        # First, get the most recent snapshot
        cdx_url = f"https://web.archive.org/cdx/search/cdx?url={self.target_url}&output=json&limit=1&fl=timestamp"
        
        try:
            response = requests.get(cdx_url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if len(data) > 1:  # First row is header
                timestamp = data[1][0]  # Get the timestamp of the most recent snapshot
                
                # Now get the actual snapshot
                wayback_url = f"https://web.archive.org/web/{timestamp}/{self.target_url}"
                print(f"Found snapshot from {timestamp}, fetching from {wayback_url}")
                
                time.sleep(2)  # Be respectful to the archive
                response = requests.get(wayback_url, headers=self.get_headers(), timeout=15)
                response.raise_for_status()
                
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print("No snapshots found in Wayback Machine")
                return None
                
        except Exception as e:
            print(f"Error accessing Wayback Machine: {e}")
            return None
    
    def try_archive_today(self):
        """
        Try to get data from Archive.today
        
        Returns:
            BeautifulSoup or None: Parsed HTML if successful, None otherwise
        """
        print(f"Trying to fetch data from Archive.today for {self.target_url}")
        
        archive_url = f"https://archive.ph/{self.target_url}"
        
        try:
            response = requests.get(archive_url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"Archive.today returned status code {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error accessing Archive.today: {e}")
            return None
    
    def try_google_cache(self):
        """
        Try to get data from Google Cache
        
        Returns:
            BeautifulSoup or None: Parsed HTML if successful, None otherwise
        """
        print(f"Trying to fetch data from Google Cache for {self.target_url}")
        
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{quote(self.target_url)}"
        
        try:
            response = requests.get(cache_url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"Google Cache returned status code {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error accessing Google Cache: {e}")
            return None
    
    def get_archived_content(self):
        """
        Try multiple archive sources to get content
        
        Returns:
            BeautifulSoup or None: Parsed HTML if successful, None otherwise
        """
        # Try different archive sources in order of reliability
        soup = self.try_wayback_machine()
        if soup:
            return soup
            
        soup = self.try_archive_today()
        if soup:
            return soup
            
        soup = self.try_google_cache()
        if soup:
            return soup
            
        print("Failed to retrieve content from any archive source")
        return None
    
    def parse_games_data(self, soup):
        """
        Parse games data from the soup
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            list: List of dictionaries containing game information
        """
        if not soup:
            return []
            
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
                
                games_data.append({
                    'title': title,
                    'seeders': seeders,
                    'leechers': leechers,
                    'peers': seeders + leechers,
                    'category': 'games',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
                })
            except (IndexError, ValueError, AttributeError) as e:
                print(f"Error parsing row: {e}")
                continue
        
        return games_data
    
    def parse_movies_data(self, soup):
        """
        Parse movies data from the soup
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            list: List of dictionaries containing movie information
        """
        if not soup:
            return []
            
        # Find the table containing the movie list
        table = soup.find('table', class_='table-list')
        if not table:
            print("Could not find the table with movies. The website structure might have changed.")
            return []
        
        # Extract rows (skip the header row)
        rows = table.find_all('tr')[1:]
        
        movies_data = []
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
                
                movies_data.append({
                    'title': title,
                    'seeders': seeders,
                    'leechers': leechers,
                    'peers': seeders + leechers,
                    'category': 'movies',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
                })
            except (IndexError, ValueError, AttributeError) as e:
                print(f"Error parsing row: {e}")
                continue
        
        return movies_data
    
    def scrape(self):
        """
        Scrape archived content
        
        Returns:
            list: List of dictionaries containing scraped data
        """
        soup = self.get_archived_content()
        
        if not soup:
            print(f"Failed to retrieve {self.category} data from archives")
            return []
        
        if self.category == 'games':
            return self.parse_games_data(soup)
        elif self.category == 'movies':
            return self.parse_movies_data(soup)
        else:
            print(f"Unknown category: {self.category}")
            return []


class GamesArchiveScraper(ArchiveScraper):
    """Class for scraping archived top games"""
    
    def __init__(self):
        """Initialize the games archive scraper"""
        super().__init__("https://1337x.to/top-100-games", "games")


class MoviesArchiveScraper(ArchiveScraper):
    """Class for scraping archived top movies"""
    
    def __init__(self):
        """Initialize the movies archive scraper"""
        super().__init__("https://1337x.to/top-100-movies", "movies")
