#!/usr/bin/env python3
"""
Base Scraper Module

This module provides the base functionality for scraping torrent websites.
It contains common utility functions and the BaseScraper class that other scrapers inherit from.
"""

import cloudscraper
from bs4 import BeautifulSoup
import time
import random
import re
import brotli
from difflib import SequenceMatcher

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
        for_display (bool): If True, clean the title for display purposes (less aggressive).
                           If False, clean for matching purposes (more aggressive).
        
    Returns:
        str: Cleaned title
    """
    cleaned = title
    
    # --- Initial Universal Cleaning --- 
    # Replace dots with spaces early on
    cleaned = cleaned.replace('.', ' ')
    
    # --- Patterns to remove for BOTH matching and display --- 
    # These are generally noise regardless of context
    patterns_all = [
        # Brackets/Parentheses content
        r'\[.*?\]',              # Content in square brackets: [Multi] etc.
        r'\(.*?\)',              # Content in parentheses: (Extended Cut) etc. 
                                   # (Might remove intended parts like "(I)" for movies)
        
        # Technical details (Quality, Codecs, Source, Resolution)
        r'\b(CAM|TS|TELESYNC|TC|HC)\b', # Early release types (CAM, Telesync, Hardcoded Subs)
        r'\b(BRRip|BDRip|BluRay|DVDRip|HDRip|WEBRip|WEB-DL|HDTV)\b', # Rip/Source types
        r'\b(REMUX)\b',             # Remux 
        r'\b(x264|x265|HEVC|XviD)\b', # Video Codecs
        r'\b(AAC|AC3|DTS|FLAC)\b',   # Audio Codecs
        r'\b(\d{3,4}p)\b',          # Resolution (720p, 1080p, 2160p)
        r'\b(\d\.\d)\b',          # Audio channels (5.1, 7.1)
        r'\b(4K)\b',                # 4K indicator

        # Versioning/Type indicators (Common in games, sometimes movies)
        r'\(v[\d\.]+.*?\)',     # Version numbers like (v1.2.3)
        r'\b(v[\d\.]+)',         # Version numbers like v1.2.3
        r'\b(Update.*$)',        # Updates (often game-related)
        r'\b(Repack)\b',          # Repacks (often game-related)
        r'\b(MULTi\d*)\b',       # Multi-language indicators (MULTi, MULTi12)
        r'\b(DLC)\b',             # DLC mentions (often game-related)
        r'\b(REMASTERED)\b',      # Remastered versions
        r'\b(EXTENDED)\b',        # Extended versions
        r'\b(DIRECTORS? CUT)\b', # Director's cut
        r'\b(UNRATED)\b',         # Unrated versions
        r'\b(COMPLETE.*?EDITION)\b', # Complete/Special Editions

        # Years (Standalone 4 digits: 19xx or 20xx)
        r'\b(19\d{2}|20\d{2})\b',  

        # Other common noise
        r'\+.*$',                 # Everything after a plus sign (often DLCs)
        r'\b(RUS|ENG|ITA|SPA|GER|FRE)\b', # Simple language tags (use MULTi for broader cases)
        r'\b(LiMiTED)\b',          # Limited tag
    ]
    
    # --- Patterns ONLY removed for matching (more aggressive) ---
    # These might remove parts of a desired display title but help grouping
    patterns_matching_only = [
        # Common Release Groups (Focus on movie groups here, game groups below)
        r'\b(YIFY|YTS|RARBG|ETRG|EtHD|EVO|PSA|NTb|MT|TGx|GalaxyRG)\b', 
        # Game-specific groups/repackers (also removed for matching games)
        r'\b(FitGirl|DODI|CODEX|PLAZA|SKIDROW|RELOADED|TENOKE|RUNE|CPY|EMPRESS|GOG|FLT)\b',
        # Generic pattern for ending group names (Use cautiously)
        # r'-[a-z0-9]+$', # Example: Movie-Title-GROUP -> Movie-Title
        # r'\b[a-z0-9]+$', # Example? Movie Title GROUP -> Movie Title (Risky! Might remove year/part of title)
        # Sticking to specific group names is safer
        r'\b(COLLECTiVE)\b', # Added from user example
        r'\b(BONE)\b',       # Added from user example
        
        # --- Added for better game key generation ---
        # Remove hyphen followed by potential group name (ONLY at the end)
        r'\s*-\s*[a-z\d]+$', 
        # Remove parenthesized content ONLY at the end (often build numbers, etc.)
        r'\s*\(.*\)$', 
        # Remove bracketed content ONLY at the end (like [F])
        r'\s*\[.*\]$',
        # DO NOT remove everything after colon, as it breaks titles like 'Game: Subtitle'
        # Instead, rely on removing specific tags/editions/versions after the colon if needed
        # Remove common game editions/tags aggressively for matching (might appear after colon)
        r'\b(?:deluxe|ultimate|gold|complete|collectors?|definitive|remastered|enhanced|goty|game of the year|premium|supporter|standard|bundle|pack|edition)\b',
        r'\b(?:repack|rip|preinstalled|portable)\b',
        r'\b(?:v\d+(?:[.]\d+)*|build[-.\s]?\d+|update[-.\s]?\d+)\b', # Versions, builds, updates
        r'\b(?:multi\d*|eng|rus|ita|esp|jpn|kor|fre|ger|\d{1,2} languages?)\b', # Languages
        # Also remove specific group names here for consistency (already listed above, but ensure RUNE etc. are covered)
        r'\b(RUNE|FitGirl|DODI|CODEX|PLAZA|SKIDROW|RELOADED|TENOKE|CPY|EMPRESS|GOG|FLT|BONE)\b',
    ]

    # --- Patterns ONLY removed for display --- 
    # Less aggressive, keeps more detail for the user to see
    patterns_display_only = [
        r'\b(Selective Download)\b', # Less relevant info for display
        # Consider removing very specific technical details ONLY for display if needed?
        # e.g., r'H264' if 'x264' wasn't caught
    ]

    # Apply the patterns
    for pattern in patterns_all:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    if not for_display: 
        # Aggressive cleaning for matching
        for pattern in patterns_matching_only:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        # Remove common punctuation for matching key consistency
        cleaned = re.sub(r'[:;,.\-\'"`~!@#$%^&*()_+={}\[\]|\\<>?]+', '', cleaned)
    else: 
        # Less aggressive cleaning for display
        for pattern in patterns_display_only:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Final whitespace cleanup
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Remove trailing characters like hyphens or colons that might be left after removals
    cleaned = re.sub(r'[\s:-]+$', '', cleaned).strip()
    
    # Return lowercase for matching, attempt to preserve original case for display
    return cleaned.lower() if not for_display else cleaned

def get_movie_grouping_key(title):
    """
    Generates a normalized key for grouping movie titles and a clean display prefix.
    It bases the prefix on the content before the first 4-digit year found.
    Falls back to aggressive cleaning if no year or prefix is suitable.

    Args:
        title (str): The original movie torrent title.

    Returns:
        tuple(str, str): (normalized_key, display_prefix)
                       normalized_key: Lowercase, no spaces key for grouping.
                       display_prefix: Cleaned prefix suitable for display.
    """
    cleaned_for_year_find = title.replace('.', ' ') # Replace dots before year finding
    
    # Find the first 4-digit year (19xx or 20xx)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', cleaned_for_year_find)
    
    display_prefix = "" # Initialize display prefix
    base_for_key = "" # Initialize the string that will become the normalized key

    if year_match:
        potential_prefix = cleaned_for_year_find[:year_match.start()].strip()
        # Use prefix if it seems reasonable (not empty, not just digits/symbols maybe?)
        # For now, just check if it's not empty
        if potential_prefix and len(potential_prefix.split()) >= 1:
             display_prefix = potential_prefix
             base_for_key = potential_prefix
        else:
            # Year found but prefix is bad/empty, fall back to aggressive clean for both
             aggressive_cleaned = clean_title(title, for_display=False)
             display_prefix = aggressive_cleaned # Use aggressive clean for display too
             base_for_key = aggressive_cleaned
    else:
        # No year found, use aggressively cleaned title as basis for key and display
        aggressive_cleaned = clean_title(title, for_display=False)
        display_prefix = aggressive_cleaned # Use aggressive clean for display
        base_for_key = aggressive_cleaned

    # Normalize the key: lowercase and remove all whitespace from the base
    normalized_key = re.sub(r'\s+', '', base_for_key).lower()
    
    # Final safety checks
    if not normalized_key:
        # If key is somehow empty, use a hash or placeholder
        normalized_key = "unknown_movie_group"
        # Ensure display_prefix isn't empty either
        if not display_prefix:
            display_prefix = clean_title(title, for_display=True) # Fallback display
            if not display_prefix: # Absolute last resort
                display_prefix = title 
                
    # Ensure display_prefix is not empty if key is valid
    if not display_prefix and normalized_key != "unknown_movie_group":
        display_prefix = clean_title(title, for_display=True) # Fallback display
        if not display_prefix:
             display_prefix = title

    # Clean trailing brackets/parentheses from display prefix
    final_display_prefix = display_prefix.strip()
    if final_display_prefix.endswith(('(', '[')):
        final_display_prefix = final_display_prefix[:-1].strip()

    # Return the normalized key for grouping and the cleaned prefix for display
    return normalized_key, final_display_prefix

def get_game_grouping_key(title):
    """
    Generates a normalized key and display title for grouping game titles.
    Uses aggressive cleaning for the key and less aggressive for the display title,
    followed by specific game-related suffix removal for display.

    Args:
        title (str): The original game torrent title.

    Returns:
        tuple(str, str): (normalized_key, display_title)
                       normalized_key: Lowercase, no spaces key for grouping.
                       display_title: Cleaned title suitable for display, preserving case.
    """
    # 1. Get base for display title (less aggressive, preserves case)
    display_title = clean_title(title, for_display=True)
    if not display_title: # Fallback if cleaning removed everything
        display_title = title # Use original title

    # 2. Get base for grouping key (aggressive, lowercase)
    key_base = clean_title(title, for_display=False)
    normalized_key = re.sub(r'\s+', '', key_base).lower()
    
    # Handle potential empty key
    if not normalized_key:
        normalized_key = "unknown_game_group"
        # If key is unknown, use less aggressive cleaning for display title too
        if display_title == title: # Check if fallback was already used
             display_title = clean_title(title, for_display=True) or title 

    # 3. Perform additional display_title specific cleaning (preserve case)
    # Remove common game suffixes/patterns left after general cleaning
    # Examples: '[ , sel', '( 0', ': premium edition [fi', ' - digital deluxe edition' etc.
    # Using broad patterns to catch variations
    # Define patterns to remove specifically from the *end* of the display title
    # These operate *after* the initial clean_title(for_display=True)
    suffixes_to_remove = [
        # Hyphen/colon/paren/bracket followed by common tags/groups/versions
        # Need to be careful not to remove intended parts like ': Subtitle'
        r'\s*[-\(:]\s*(?:\d+\s*[/.]?\s*\d+|v\d+|build|update|dlc|ost|soundtrack|multi\d*|eng|rus|ita|jpn|kor)\b.*', # Build nums, versions, lang etc after separator
        r'\s*[-\(:]\s*(?:premium|deluxe|supporter|ultimate|standard|collector.?s|goty|digital|definitive|complete|remastered|gold|enhanced|bundle|pack|edition|repack|rip|fitgirl|dodi|codex|rune|p2p|gog|flt)\b.*', # Editions, groups etc. after separator
        # Standalone bracketed/parenthesized content at the very end
        r'\s*\(.*\)$', # Parenthesized content at end
        r'\s*\[[^\]]*\]$', # Bracketed content at end (less greedy)
        # Specific leftovers seen in examples
        r'\s*-\s*RUNE$', # Explicitly match -RUNE at the end
        r'\s*: Khaos Reigns Kollection.*', # Specific MK1 edition noise
        r'\s*with early p.*', # Early purchase bonus
        r'\s*3 3f\d+$', # Schedule I noise
        r'\s*-\s*\(\s*\d+\s+\d+\s+\d+\s*\)$' # Specific TLOU build number format
    ]
    temp_title = display_title
    for suffix_pattern in suffixes_to_remove:
        # Match suffix at the end of the string, case-insensitive for the pattern
        match = re.search(suffix_pattern + '$', temp_title, re.IGNORECASE)
        if match:
            # Remove the matched part from the original cased string
            temp_title = temp_title[:match.start()].strip()
            
    # Remove trailing special characters again after suffix removal
    display_title = re.sub(r'[\s:;,.\(\[\-]+$', '', temp_title).strip()

    # Ensure display title isn't empty after all cleaning
    if not display_title:
        display_title = clean_title(title, for_display=True) # Try again with less aggressive
        if not display_title:
            display_title = title # Absolute fallback

    return normalized_key, display_title


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
    
    def create_scraper(self):
        """
        Create a cloudscraper session that can bypass Cloudflare protection
        
        Returns:
            cloudscraper.CloudScraper: Scraper session
        """
        # Create a cloudscraper session with browser-like headers
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',  # Try Firefox instead of Chrome
                'platform': 'windows',
                'mobile': False
            },
            delay=5,  # Shorter delay between requests
            debug=True,  # Enable debug mode to see what's happening
            allow_brotli=True,  # Allow brotli compression
            cipherSuite='ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256',  # Modern cipher suite
            captcha={'provider': 'return_response'}  # Return the response even if there's a captcha
        )
        
        # Set additional browser-like attributes
        scraper.headers.update({
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',  # Pretend we came from Google
            'DNT': '1'
        })
        
        return scraper

    def make_request(self, url):
        """
        Make a request to the specified URL using cloudscraper to bypass protection
        
        Args:
            url (str): URL to request
            
        Returns:
            cloudscraper.Response: Response object or None if all retries failed
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Add a delay to be respectful to the server (increase with each retry)
                time.sleep(retry_delay * (attempt + 1))
                
                # Create a cloudscraper session
                scraper = self.create_scraper()
                
                # Add additional headers
                for key, value in self.get_headers().items():
                    scraper.headers[key] = value
                
                # Make the request
                print(f"Attempting to access {url} with cloudscraper (Attempt {attempt+1}/{max_retries})")
                response = scraper.get(url, timeout=30)  # Longer timeout for challenge solving
                
                # Check for common error codes
                if response.status_code == 403:
                    print(f"Access forbidden (403). Retrying... (Attempt {attempt+1}/{max_retries})")
                    continue
                elif response.status_code == 429:
                    print(f"Rate limited (429). Waiting longer before retry... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(10)  # Wait longer for rate limit
                    continue
                
                # Check if we got a successful response
                if response.status_code == 200:
                    print(f"Successfully accessed {url} with cloudscraper")
                    return response
                else:
                    # Raise an exception for other HTTP errors
                    response.raise_for_status()
                
            except Exception as e:
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
            response (cloudscraper.Response): Response to parse
            
        Returns:
            BeautifulSoup: Parsed HTML or None if response is None
        """
        if response is None:
            return None
            
        try:
            # Print response info for debugging
            print(f"Response status: {response.status_code}, Content length: {len(response.content)} bytes")
            print(f"Content encoding: {response.headers.get('Content-Encoding', 'none')}")
            
            # Get the content, handling any encoding
            content = response.content
            
            # Manually decode if needed
            if 'br' in response.headers.get('Content-Encoding', '').lower():
                try:
                    content = brotli.decompress(content)
                    print("Successfully decompressed brotli content")
                except Exception as e:
                    print(f"Failed to decompress brotli content: {e}")
                    # If brotli decompression fails, use the response.text which might already be decoded
                    if hasattr(response, 'text') and response.text:
                        print("Using response.text as fallback")
                        content = response.text.encode('utf-8')
            
            # Use html5lib parser for better handling of malformed HTML
            soup = BeautifulSoup(content, 'html5lib')
            
            # Check if we got a CloudFlare or similar challenge page
            challenge_indicators = [
                "cloudflare", "challenge", "captcha", "blocked", "access denied",
                "ddos", "protection", "javascript", "browser check", "security check"
            ]
            
            page_text = soup.get_text().lower()
            for indicator in challenge_indicators:
                if indicator in page_text:
                    print(f"Detected anti-bot indicator: '{indicator}'")
                    # Don't return None immediately, try to proceed anyway
            
            # Check for the presence of the table we need
            table = soup.find('table', class_='table-list') or soup.find('table', class_='table-list table table-responsive table-striped')
            if table:
                print("Found the expected table structure!")
                return soup
            else:
                print("Could not find the expected table structure in the response.")
                
                # Try a more generic approach to find any table
                tables = soup.find_all('table')
                if tables:
                    print(f"Found {len(tables)} tables with different classes:")
                    for i, t in enumerate(tables):
                        print(f"Table {i+1} class: {t.get('class', 'None')}")
                    
                    # Try the first table that might contain our data
                    for t in tables:
                        rows = t.find_all('tr')
                        if len(rows) > 10:  # Assuming top-100 will have many rows
                            print(f"Using table with {len(rows)} rows")
                            return soup
                
                # Save a sample of the HTML for debugging
                print("Sample of HTML content:")
                print(str(soup)[:500])
                
                return soup  # Return the soup anyway, let the scraper handle it
                
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
