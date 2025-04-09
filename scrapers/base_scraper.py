#!/usr/bin/env python3
"""
Base Scraper Module

This module provides the base functionality for scraping torrent websites.
It contains common utility functions and the BaseScraper class that other scrapers inherit from.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from difflib import SequenceMatcher
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Define user agents to rotate and avoid being blocked
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
]

def get_random_user_agent():
    """Return a random user agent from the list."""
    return random.choice(USER_AGENTS)

def clean_title(title, for_display=False):
    """
    Clean and normalize title for better matching or display
    
    Args:
        title (str): Original title
        for_display (bool): If True, clean the title for display purposes
                           If False, clean for matching purposes
        
    Returns:
        str: Cleaned title
    """
    # Remove common patterns in titles that indicate versions, repacks, etc.
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
        r'REMASTERED',  # Remastered versions
        r'EXTENDED',  # Extended versions
        r'DIRECTORS CUT',  # Director's cut
        r'UNRATED',  # Unrated versions
        r'BRRip',  # Blu-ray rips
        r'DVDRip',  # DVD rips
        r'HDRip',  # HD rips
        r'WEBRip',  # Web rips
        r'XviD',  # Video codec
        r'x264',  # Video codec
        r'x265',  # Video codec
        r'HEVC',  # Video codec
        r'AAC',  # Audio codec
        r'AC3',  # Audio codec
        r'FLAC',  # Audio codec
        r'\d{3,4}p',  # Resolution like 1080p, 720p
        r'HDTV',  # TV source
        r'WEB-DL',  # Web download
        r'BluRay',  # Blu-ray source
    ]
    
    # Additional patterns for display cleaning (more aggressive)
    display_patterns = [
        r'-[^-]*$',  # Everything after the last hyphen if it's not part of the name
        r'\s*:\s*$',  # Trailing colons with optional spaces
        r'\s*-\s*$',  # Trailing hyphens with optional spaces
        r'FitGirl',  # FitGirl repacks
        r'DODI',  # DODI repacks
        r'CODEX',  # CODEX releases
        r'PLAZA',  # PLAZA releases
        r'SKIDROW',  # SKIDROW releases
        r'RELOADED',  # RELOADED releases
        r'TENOKE',  # TENOKE releases
        r'RUNE',  # RUNE releases
        r'YIFY',  # YIFY releases
        r'YTS',  # YTS releases
        r'RARBG',  # RARBG releases
        r'ETRG',  # ETRG releases
        r'EtHD',  # EtHD releases
        r'Selective Download',  # Selective download option
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
    Calculate similarity between two titles
    
    Args:
        title1 (str): First title
        title2 (str): Second title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Clean titles first (for matching, not display)
    clean_title1 = clean_title(title1, for_display=False)
    clean_title2 = clean_title(title2, for_display=False)
    
    # Use SequenceMatcher for similarity calculation
    return SequenceMatcher(None, clean_title1, clean_title2).ratio()

class BaseScraper:
    """Base class for all scrapers"""
    
    def __init__(self, base_url, category):
        """
        Initialize the scraper
        
        Args:
            base_url (str): Base URL of the website to scrape
            category (str): Category to scrape (e.g., 'games', 'movies')
        """
        self.base_url = base_url
        self.category = category
        
    def get_headers(self):
        """
        Get random user agent headers with additional browser-like headers
        
        Returns:
            dict: Headers for HTTP request
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15"
        ]
        
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "TE": "Trailers",
            "DNT": "1"
        }
        
        return headers
    
    def create_session(self):
        """
        Create a requests session with retry logic
        
        Returns:
            requests.Session: Configured session object
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # Maximum number of retries
            backoff_factor=1,  # Time factor between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET", "HEAD"]  # Only retry for these methods
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def make_request(self, url):
        """
        Make a request to the specified URL with retry logic
        
        Args:
            url (str): URL to request
            
        Returns:
            requests.Response: Response object or None if all retries failed
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Add a delay to be respectful to the server (increase with each retry)
                time.sleep(retry_delay * (attempt + 1))
                
                # Create a session to maintain cookies
                session = requests.Session()
                
                # Make the request
                response = session.get(url, headers=self.get_headers(), timeout=15)
                
                # Check for common error codes
                if response.status_code == 403:
                    print(f"Access forbidden (403). Retrying with different headers... (Attempt {attempt+1}/{max_retries})")
                    continue
                elif response.status_code == 429:
                    print(f"Rate limited (429). Waiting longer before retry... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(10)  # Wait longer for rate limit
                    continue
                
                # Raise an exception for other HTTP errors
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay * (attempt + 2)} seconds...")
                else:
                    print("All retry attempts failed.")
                    return None
        
        return None
    
    def parse_response(self, response):
        """
        Parse the response into BeautifulSoup
        
        Args:
            response (requests.Response): Response to parse
            
        Returns:
            BeautifulSoup: Parsed HTML or None if response is None
        """
        if response is None:
            return None
            
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we got a CloudFlare or similar challenge page
            if soup.find(text=re.compile(r"(cloudflare|challenge|captcha|blocked|access denied)", re.I)):
                print("Detected anti-bot challenge or access denied page.")
                return None
                
            # Check if we got an empty or very small page (likely blocked)
            if len(response.text) < 1000:
                print(f"Response too small ({len(response.text)} bytes), might be blocked.")
                return None
                
            return soup
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    
    def group_similar_items(self, items_data, similarity_threshold=0.6):
        """
        Group similar items together based on title similarity
        
        Args:
            items_data (list): List of dictionaries containing item information
            similarity_threshold (float): Threshold for considering items similar
            
        Returns:
            list: List of dictionaries containing grouped item information
        """
        if not items_data:
            return []
        
        # Sort items by total peers (descending) to prioritize more popular versions
        sorted_items = sorted(items_data, key=lambda x: x['total_peers'], reverse=True)
        
        # Initialize groups with the first item
        groups = []
        processed_indices = set()
        
        # For each item, try to find a group or create a new one
        for i, item in enumerate(sorted_items):
            if i in processed_indices:
                continue
                
            # Create a new group with this item as the representative
            current_group = {
                'representative': item,
                'titles': [item['title']],
                'total_seeders': item['seeders'],
                'total_leechers': item['leechers'],
                'total_peers': item['total_peers'],
                'versions': [item]
            }
            processed_indices.add(i)
            
            # Find similar items
            for j, other_item in enumerate(sorted_items):
                if j in processed_indices or i == j:
                    continue
                    
                similarity = calculate_similarity(item['title'], other_item['title'])
                if similarity >= similarity_threshold:
                    current_group['titles'].append(other_item['title'])
                    current_group['total_seeders'] += other_item['seeders']
                    current_group['total_leechers'] += other_item['leechers']
                    current_group['total_peers'] += other_item['total_peers']
                    current_group['versions'].append(other_item)
                    processed_indices.add(j)
            
            groups.append(current_group)
        
        return groups
    
    def scrape(self):
        """
        Scrape the website
        
        This method should be implemented by subclasses
        
        Returns:
            list: List of dictionaries containing scraped data
        """
        raise NotImplementedError("Subclasses must implement this method")
