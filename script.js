// Initialize Leaflet map
function initMap() {
    const map = L.map('map').setView([31.0461, 34.8516], 10); // Center map to Israel

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Load CSV data and add markers
    Papa.parse('football_matches.csv', {
        download: true,
        header: true,
        complete: (results) => {
            const matches = results.data;
            matches.forEach(match => {
                L.Control.Geocoder.nominatim().geocode(match.stadium, function(results) {
                    if (results && results.length > 0) {
                        const latLng = results[0].center;
                        L.marker(latLng)
                            .addTo(map)
                            .bindPopup(`<div><strong>${match.teams}</strong><br>Stadium: ${match.stadium}<br>Date: ${match.date}</div>`);
                    }
                });
            });
        }
    });
}    

// Search function
function searchMatches() {
    const query = document.getElementById('search').value.toLowerCase();
    // Implement search functionality here
    // You would filter the markers based on the query and update the map
}

// Login function
function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    // Implement login functionality here
    // For example, authenticate the user or show a message
}

// Initialize map on window load
window.onload = initMap;
