/**



 * Torrent Monitoring Dashboard


 * Main JavaScript file for handling the dashboard functionality


 */





// Global variables for charts


let moviesChart = null;


let gamesChart = null;





// Colors for chart lines


const chartColors = [


    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',


    '#1abc9c', '#d35400', '#34495e', '#16a085', '#c0392b',


    '#27ae60', '#f1c40f', '#8e44ad', '#2980b9', '#7f8c8d',


    '#2c3e50', '#e67e22', '#95a5a6', '#d35400', '#bdc3c7'


];





// DOM elements


const tabs = document.querySelectorAll('.tab');


const tabContents = document.querySelectorAll('.tab-content');


const periodButtons = document.querySelectorAll('.period-btn');


const moviesTable = document.getElementById('movies-table').querySelector('tbody');


const gamesTable = document.getElementById('games-table').querySelector('tbody');


const lastUpdatedTime = document.getElementById('last-updated-time');





/**


 * Initialize the application


 */


function init() {


    // Set up tab switching


    setupTabs();


    


    // Set up period buttons


    setupPeriodButtons();


    


    // Load initial data


    loadRankingsData('movies', 'daily');


    loadRankingsData('games', 'daily');


    


    // Initialize charts


    initCharts();


    


    // Update last updated time


    updateLastUpdatedTime();


}





/**


 * Set up tab switching functionality


 */


function setupTabs() {


    tabs.forEach(tab => {


        tab.addEventListener('click', (e) => {


            // Skip for GitHub tab which is an external link


            if (tab.getAttribute('target') === '_blank') {


                return;


            }


            


            e.preventDefault();


            


            // Remove active class from all tabs and tab contents


            tabs.forEach(t => t.classList.remove('active'));


            tabContents.forEach(content => content.classList.remove('active'));


            


            // Add active class to clicked tab


            tab.classList.add('active');


            


            // Show corresponding tab content


            const tabId = tab.getAttribute('data-tab');


            document.getElementById(tabId).classList.add('active');


            


            // If switching to a chart tab, resize the chart


            if (tabId === 'movies-chart' && moviesChart) {


                moviesChart.resize();


            } else if (tabId === 'games-chart' && gamesChart) {


                gamesChart.resize();


            }


        });


    });


}





/**


 * Set up period buttons functionality


 */


function setupPeriodButtons() {


    periodButtons.forEach(button => {


        button.addEventListener('click', () => {


            // Get the category and period from the button


            const category = button.getAttribute('data-category');


            const period = button.getAttribute('data-period');


            


            // Remove active class from all buttons in this category


            document.querySelectorAll(`.period-btn[data-category="${category}"]`)


                .forEach(btn => btn.classList.remove('active'));


            


            // Add active class to clicked button


            button.classList.add('active');


            


            // Load data for the selected period


            loadRankingsData(category, period);


        });


    });


}





/**


 * Load rankings data for the specified category and period


 * @param {string} category - 'movies' or 'games'


 * @param {string} period - 'daily' or 'weekly'


 */


function loadRankingsData(category, period) { // Note: 'period' argument is no longer used for URL
    const tableBody = category === 'movies' ? moviesTable : gamesTable;

    // Show loading indicator
    tableBody.innerHTML = '<tr><td colspan="5" class="loading">Loading latest data...</td></tr>';

    // Fetch the chart data (contains latest info)
    const url = `data-summary/${category}_chart_data.json`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                // Handle network errors (including 404 for chart data, which shouldn't happen normally)
                throw new Error(`Failed to fetch chart data (${url}): ${response.status} ${response.statusText}`);
            }
            return response.json(); // Proceed to parse JSON
        })
        .then(data => {
            if (data && data.titles && data.data && data.data.length > 0) {
                // Extract the latest data point (last row in the data array)
                const latestDataRow = data.data[data.data.length - 1];

                // Construct rankings array from titles and latest data row
                const rankings = data.titles.map((title, index) => ({
                    title: title,
                    peers: latestDataRow[index] !== null && latestDataRow[index] !== undefined ? latestDataRow[index] : 0, // Get peers from the last row, default to 0 if null/undefined
                    seeders: 'N/A', // Chart data doesn't store separate seeders/leechers
                    leechers: 'N/A',
                    change: 'N/A'   // Chart data doesn't store change info
                }));

                // Sort by peers descending
                rankings.sort((a, b) => b.peers - a.peers);

                displayRankings(tableBody, rankings);
                updateLastUpdatedTime(data.updated_at); // Update time using chart data timestamp

            } else {
                // Handle cases where chart data is empty or malformed
                console.warn(`No valid chart data found in ${url}`);
                tableBody.innerHTML = '<tr><td colspan="5" class="loading">Latest data not available or file is empty.</td></tr>';
                // Attempt to update timestamp even if data is bad, might still be in file
                if (data && data.updated_at) {
                    updateLastUpdatedTime(data.updated_at);
                } else {
                     // If absolutely no data, try fetching the other category's chart data just for the timestamp
                    const otherCategory = category === 'movies' ? 'games' : 'movies';
                    fetch(`data-summary/${otherCategory}_chart_data.json`)
                        .then(res => res.ok ? res.json() : null)
                        .then(otherData => {
                            if (otherData && otherData.updated_at) updateLastUpdatedTime(otherData.updated_at);
                        })
                        .catch(() => { /* Ignore errors fetching secondary timestamp */ });
                }
            }
        })
        .catch(error => {
            console.error(`Error fetching or processing ${category} chart data from ${url}:`, error);
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">Error loading latest data. Check console.</td></tr>';
        });
}





/**


 * Display rankings in the specified table


 * @param {HTMLElement} tableBody - Table body element


 * @param {Array} rankings - Rankings data


 */


function displayRankings(tableBody, rankings) {


    // Clear the table


    tableBody.innerHTML = '';


    


    // Add rows for each ranking


    rankings.forEach((item, index) => {


        const row = document.createElement('tr');


        


        // Rank column


        const rankCell = document.createElement('td');


        rankCell.textContent = index + 1; // Use loop index for rank


        row.appendChild(rankCell);


        


        // Title column


        const titleCell = document.createElement('td');


        titleCell.textContent = item.title;


        row.appendChild(titleCell);


        


        // Change column


        const changeCell = document.createElement('td');


        const changeSpan = document.createElement('span');


        changeSpan.className = 'rank-change';


        


        if (item.rank_change === 'N/A') {
            // Handle the N/A case from chart data
            changeSpan.textContent = 'N/A';
        } else if (item.rank_change === 'new') {
            changeSpan.classList.add('new');
            changeSpan.innerHTML = '<i class="fas fa-star"></i> New';
        } else if (item.rank_change > 0) {
            changeSpan.classList.add('up');
            changeSpan.innerHTML = `<i class="fas fa-arrow-up"></i> ${item.rank_change}`;
        } else if (item.rank_change < 0) {
            changeSpan.classList.add('down');
            changeSpan.innerHTML = `<i class="fas fa-arrow-down"></i> ${Math.abs(item.rank_change)}`;
        } else { // rank_change is likely 0 or undefined/null
            changeSpan.innerHTML = '<i class="fas fa-minus"></i> 0';
        }


        


        changeCell.appendChild(changeSpan);


        row.appendChild(changeCell);


        


        // Seeders column


        const seedersCell = document.createElement('td');


        seedersCell.textContent = item.seeders.toLocaleString();


        row.appendChild(seedersCell);


        


        // Peers column


        const peersCell = document.createElement('td');


        peersCell.textContent = item.peers.toLocaleString();


        row.appendChild(peersCell);


        


        tableBody.appendChild(row);


    });


}





/**


 * Initialize the charts


 */


function initCharts() {


    // Load chart data for movies


    fetch('data-summary/movies_chart_data.json')


        .then(response => {


            if (!response.ok) {


                throw new Error('Network response was not ok');


            }


            return response.json();


        })


        .then(data => {


            createChart('moviesChart', data, 'movies-legend');


        })


        .catch(error => {


            console.error('Error fetching movies chart data:', error);


            document.getElementById('moviesChart').parentNode.innerHTML = 


                '<div class="loading">Failed to load chart data. Please try again later.</div>';


        });


    


    // Load chart data for games


    fetch('data-summary/games_chart_data.json')


        .then(response => {


            if (!response.ok) {


                throw new Error('Network response was not ok');


            }


            return response.json();


        })


        .then(data => {


            createChart('gamesChart', data, 'games-legend');


        })


        .catch(error => {


            console.error('Error fetching games chart data:', error);


            document.getElementById('gamesChart').parentNode.innerHTML = 


                '<div class="loading">Failed to load chart data. Please try again later.</div>';


        });


}





/**


 * Create a chart with the provided data


 * @param {string} chartId - ID of the canvas element


 * @param {Object} data - Chart data


 * @param {string} legendId - ID of the legend container


 */


function createChart(chartId, data, legendId) {


    const ctx = document.getElementById(chartId).getContext('2d');


    const legendContainer = document.getElementById(legendId);


    


    // Parse dates and prepare datasets
    const parsedDates = data.dates.map(dateStr => new Date(dateStr));

    // Determine the time range for the x-axis
    let minDate = null;
    let maxDate = null;
    if (parsedDates.length > 0) {
        parsedDates.sort((a, b) => a - b); // Sort dates chronologically
        maxDate = parsedDates[parsedDates.length - 1];
        minDate = parsedDates[0];
        
        // Calculate the date 7 days before the max date
        const sevenDaysAgo = new Date(maxDate);
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

        // Ensure the min date is not earlier than 7 days ago
        if (minDate < sevenDaysAgo) {
            minDate = sevenDaysAgo;
        }
    } 

    // Prepare datasets


    const datasets = data.titles.map((title, index) => {


        const color = chartColors[index % chartColors.length];


        return {


            label: title,


            data: data.data.map(row => row[index] || 0),


            borderColor: color,


            backgroundColor: color + '20',  // Add transparency


            borderWidth: 2,


            pointRadius: 3,


            pointHoverRadius: 5,


            tension: 0.1


        };


    });


    


    // Create the chart


    const chart = new Chart(ctx, {


        type: 'line',


        data: {


            labels: parsedDates, // Use parsed dates for labels


            datasets: datasets


        },


        options: {


            responsive: true,


            maintainAspectRatio: false,


            plugins: {


                legend: {


                    display: false  // Hide default legend


                },


                tooltip: {


                    mode: 'index',


                    intersect: false


                }


            },


            scales: {


                x: {
                    type: 'time',
                    time: {
                        unit: 'hour', // Adjust based on data density if needed
                        tooltipFormat: 'PPp', // Format for tooltips (e.g., Apr 9, 2025, 6:14:04 PM)
                        displayFormats: {
                            hour: 'MMM d, HH:mm', // Format for labels on the axis
                            day: 'MMM d'
                        }
                    },
                    min: minDate ? minDate.toISOString() : undefined,
                    max: maxDate ? maxDate.toISOString() : undefined,
                    grid: {
                        display: false
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10 // Adjust for desired density
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },


                y: {
                    type: 'logarithmic',
                    // beginAtZero is ignored/invalid for logarithmic scale
                    grid: {


                        color: '#ecf0f1'


                    },


                    ticks: {


                        callback: function(value) {


                            return value.toLocaleString();


                        }
                    },
                    title: {
                        display: true,
                        text: 'Peers'
                    }
                }
            }
        }
    });


    


    // Save chart reference


    if (chartId === 'moviesChart') {


        moviesChart = chart;


    } else {


        gamesChart = chart;


    }


    


    // Create custom legend


    createCustomLegend(chart, legendContainer);


}





/**


 * Create a custom legend for the chart


 * @param {Chart} chart - Chart.js instance


 * @param {HTMLElement} container - Legend container element


 */


function createCustomLegend(chart, container) {


    // Clear the container


    container.innerHTML = '';


    


    // Create legend items


    chart.data.datasets.forEach((dataset, index) => {


        const item = document.createElement('div');


        item.className = 'legend-item';


        item.dataset.index = index;


        


        const colorBox = document.createElement('span');


        colorBox.className = 'legend-color';


        colorBox.style.backgroundColor = dataset.borderColor;


        


        const text = document.createElement('span');


        text.textContent = dataset.label;


        


        item.appendChild(colorBox);


        item.appendChild(text);


        container.appendChild(item);


        


        // Add click event to toggle visibility


        item.addEventListener('click', () => {


            const index = parseInt(item.dataset.index);


            const isDatasetVisible = chart.isDatasetVisible(index);


            


            if (isDatasetVisible) {


                chart.hide(index);


                item.classList.add('hidden');


            } else {


                chart.show(index);


                item.classList.remove('hidden');


            }


        });


    });


}





/**


 * Update the last updated time display


 * @param {string} [timestamp] - Timestamp string


 */


function updateLastUpdatedTime(timestamp) {


    if (timestamp) {


        try {
            const date = new Date(timestamp);
            lastUpdatedTime.textContent = date.toLocaleString();
        } catch (e) {
            lastUpdatedTime.textContent = 'Invalid Date';
            console.error('Error parsing provided timestamp:', timestamp, e);
        }


    } else {


        // Try to get the timestamp from one of the data files


        fetch('data-summary/movies_chart_data.json') // Use chart data as a reliable source for update time


            .then(response => response.json())


            .then(data => {


                if (data.updated_at) {
                    try {
                        const date = new Date(data.updated_at);
                        lastUpdatedTime.textContent = date.toLocaleString();
                    } catch (e) {
                        lastUpdatedTime.textContent = 'Invalid Date';
                        console.error('Error parsing fetched updated_at:', data.updated_at, e);
                    }
                } else {
                    lastUpdatedTime.textContent = 'Unknown';
                }


            })


            .catch(() => {


                lastUpdatedTime.textContent = 'Unknown';


            });


    }


}





// Initialize the application when the DOM is loaded


document.addEventListener('DOMContentLoaded', init);