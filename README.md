# Torrent Monitoring Dashboard

A web-based dashboard that displays rankings for top games and movies from torrent sources. This project scrapes data from 1337x.to, processes it, and displays real-time rankings and trends on a website hosted on GitHub Pages.

## Features

- **Automated Data Collection**: Scrapes top games and movies from 1337x.to every 3 hours using GitHub Actions
- **Intelligent Title Grouping**: Groups similar titles using text similarity algorithms
- **Ranking Visualization**: 
  - Daily (24h) and weekly (7d) ranking changes
  - Interactive charts showing trends over time
- **GitHub Pages Integration**: Automatically updates the website with the latest data

## Project Structure

```bash
torrent-monitoring/
├── scrapers/
│   ├── base_scraper.py     # Base scraper functionality
│   ├── games_scraper.py    # Games-specific scraper
│   ├── movies_scraper.py   # Movies-specific scraper
├── website/
│   ├── index.html          # Main website
│   ├── css/
│   │   └── styles.css      # Website styling
│   ├── js/
│   │   └── app.js          # Website functionality
│   └── data/               # Generated data files for website
├── data-raw/               # Raw scraped data
├── data-summary/           # Processed summary data
├── .github/
│   └── workflows/          # GitHub Actions configuration
├── main.py                 # Main script to run scrapers and update data
├── data_manager.py         # Handles data saving and processing
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Git (for GitHub integration)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/torrent-monitoring.git
   cd torrent-monitoring
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Running the Scraper

#### Manual Execution

To run the scraper manually:

```bash
python main.py
```

Add the `--push` flag to push changes to GitHub (only needed for local runs):

```bash
python main.py --push
```

#### Automated Execution with GitHub Actions

The scraper is configured to run automatically every 3 hours using GitHub Actions. The workflow configuration is in `.github/workflows/scraper.yml`.

You can also manually trigger the workflow from the Actions tab in your GitHub repository.

## Data Structure

### Raw Data

Raw data is stored in CSV files with the following columns:

- `title`: Original title from the torrent site
- `clean_title`: Cleaned and normalized title
- `seeders`: Number of seeders
- `leechers`: Number of leechers
- `total_peers`: Total number of peers (seeders + leechers)
- `category`: Category (games or movies)

### Grouped Data

Grouped data combines similar titles and includes:

- `main_title`: Representative title for the group
- `total_seeders`: Sum of seeders for all items in the group
- `total_leechers`: Sum of leechers for all items in the group
- `total_peers`: Sum of peers for all items in the group

### Summary Data

Summary data is used to generate rankings and charts, including:

- Daily rankings (24-hour changes)
- Weekly rankings (7-day changes)
- Chart data for visualizing trends

## Website

The website is designed to be hosted on GitHub Pages and includes:

- **Top Rankings Tab**: Shows the top 20 games and movies with ranking changes
- **Movies Chart Tab**: Interactive chart showing trends for top movies
- **Games Chart Tab**: Interactive chart showing trends for top games
- **GitHub Link**: Direct link to the project repository

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational purposes only. Please use responsibly and in accordance with the terms of service of any websites you interact with.

## Acknowledgements

- Data sourced from [1337x.to](https://1337x.to)
- Built with [Chart.js](https://www.chartjs.org/) for visualizations
