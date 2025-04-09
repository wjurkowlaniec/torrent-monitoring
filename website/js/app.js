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


function loadRankingsData(category, period) {


    const tableBody = category === 'movies' ? moviesTable : gamesTable;


    


    // Show loading indicator


    tableBody.innerHTML = '<tr><td colspan="5" class="loading">Loading data...</td></tr>';


    


    // Fetch the data


    fetch(`data/${category}_${period}_rankings.json`)


        .then(response => {


            if (!response.ok) {


                throw new Error('Network response was not ok');


            }


            return response.json();


        })


        .then(data => {


            displayRankings(tableBody, data.rankings);


            updateLastUpdatedTime(data.updated_at);


        })


        .catch(error => {


            console.error('Error fetching rankings data:', error);


            tableBody.innerHTML = '<tr><td colspan="5" class="loading">Failed to load data. Please try again later.</td></tr>';


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


    rankings.forEach(item => {


        const row = document.createElement('tr');


        


        // Rank column


        const rankCell = document.createElement('td');


        rankCell.textContent = item.current_rank;


        row.appendChild(rankCell);


        


        // Title column


        const titleCell = document.createElement('td');


        titleCell.textContent = item.title;


        row.appendChild(titleCell);


        


        // Change column


        const changeCell = document.createElement('td');


        const changeSpan = document.createElement('span');


        changeSpan.className = 'rank-change';


        


        if (item.rank_change === 'new') {


            changeSpan.classList.add('new');


            changeSpan.innerHTML = '<i class="fas fa-star"></i> New';


        } else if (item.rank_change > 0) {


            changeSpan.classList.add('up');


            changeSpan.innerHTML = `<i class="fas fa-arrow-up"></i> ${item.rank_change}`;


        } else if (item.rank_change < 0) {


            changeSpan.classList.add('down');


            changeSpan.innerHTML = `<i class="fas fa-arrow-down"></i> ${Math.abs(item.rank_change)}`;


        } else {


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


    fetch('data/movies_chart_data.json')


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


    fetch('data/games_chart_data.json')


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


            labels: data.dates,


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


                    grid: {


                        display: false


                    }


                },


                y: {


                    beginAtZero: true,


                    grid: {


                        color: '#ecf0f1'


                    },


                    ticks: {


                        callback: function(value) {


                            return value.toLocaleString();


                        }


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


        lastUpdatedTime.textContent = timestamp;


    } else {


        // Try to get the timestamp from one of the data files


        fetch('data/movies_daily_rankings.json')


            .then(response => response.json())


            .then(data => {


                lastUpdatedTime.textContent = data.updated_at || 'Unknown';


            })


            .catch(() => {


                lastUpdatedTime.textContent = 'Unknown';


            });


    }


}





// Initialize the application when the DOM is loaded


document.addEventListener('DOMContentLoaded', init);