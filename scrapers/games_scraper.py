#!/usr/bin/env python3
"""
Games Scraper Module

This module provides functionality for scraping top games from torrent websites.
"""

from scrapers.base_scraper import BaseScraper, clean_title

class GamesScraper(BaseScraper):
    """Class for scraping top games"""
    
    def __init__(self, base_url="https://1337x.to"):
        """Initialize the games scraper"""
        super().__init__(base_url, "games")
        self.top_url = f"{base_url}/top-100-games"
    
    def scrape(self):
        """
        Scrape the top games
        
        Returns:
            list: List of dictionaries containing game information
        """
        response = self.make_request(self.top_url)
        soup = self.parse_response(response)
        
        if not soup:
            print("Failed to parse the games page")
            return []
        
        # Find the table containing the game list
        table = soup.find('table', class_='table-list') or soup.find('table', class_='table-list table table-responsive table-striped')
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
                    'total_peers': total_peers,
                    'category': 'games',
                    'clean_title': clean_title(title, for_display=True)
                })
            except (IndexError, AttributeError) as e:
                print(f"Error processing a row: {e}")
                continue
        
        return games_data
