// Function to initialize coordinate dictionaries
function initializeCoordDict(callback) {
    const primaryDict = {};
    const cityDict = {};

    Papa.parse('Scrapper/stadium_coordinates.csv', {
        download: true,
        header: true,
        complete: (results) => {
            console.log('Coordinates CSV loaded:', results.data);

            results.data.forEach(row => {
                const stadiumName = row.Stadium ? row.Stadium.toLowerCase() : '';
                const cityName = row.City ? row.City.toLowerCase() : '';
                const lat = parseFloat(row.Latitude);
                const lng = parseFloat(row.Longitude);

                if (stadiumName && !isNaN(lat) && !isNaN(lng)) {
                    primaryDict[stadiumName] = [lat, lng];
                }

                if (cityName && !isNaN(lat) && !isNaN(lng)) {
                    cityDict[cityName] = [lat, lng];  // Store coordinates based on city
                }
            });

            window.coordDict = { primary: primaryDict, city: cityDict };

            // Call the callback function to initialize the map after loading coordinates
            if (callback) callback();
        },
        error: (error) => console.error('Error loading coordinates CSV:', error)
    });
}

// Initialize Leaflet map
function initMap() {
    const map = L.map('map').setView([31.0461, 34.8516], 10); // Center map to Israel
    window.map = map; // Make map available globally

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Load CSV data and add markers
    Papa.parse('Scrapper/Ligat_HaAl_Fixtures.csv', {
        download: true,
        header: true,
        complete: (results) => {
            console.log('Matches CSV loaded:', results.data);

            const matches = results.data;

            // Ensure coordDict is defined
            if (!window.coordDict) {
                console.error('Coordinates dictionary is not initialized.');
                return;
            }

            // Filter matches based on user input date range
            document.getElementById('filterBtn').addEventListener('click', () => {
                filterMatchesAndDisplay(map, matches);
            });
        },
        error: (error) => console.error('Error loading matches CSV:', error)
    });
}

// Function to filter matches and display them on the map
function filterMatchesAndDisplay(map, matches) {
    const startDateInput = document.getElementById('startDate').value;
    const endDateInput = document.getElementById('endDate').value;

    if (!startDateInput || !endDateInput) {
        alert('Please select both a start and end date.');
        return;
    }

    const startDate = new Date(startDateInput);
    const endDate = new Date(endDateInput);

    const filteredMatches = matches.filter(match => {
        const matchDate = new Date(match.Date);
        return matchDate >= startDate && matchDate <= endDate;
    });

    if (filteredMatches.length === 0) {
        console.log('No matches found in the given date range.');
    }

    // Group matches by stadium and display them
    const groupedMatches = groupMatchesByStadium(filteredMatches);
    displayGroupedMatchesOnMap(map, groupedMatches);
}

// Function to group matches by stadium
function groupMatchesByStadium(matches) {
    const grouped = {};

    matches.forEach(match => {
        const stadiumName = match.Stadium ? match.Stadium.trim().toLowerCase() : '';

        if (!grouped[stadiumName]) {
            grouped[stadiumName] = [];
        }
        grouped[stadiumName].push(match);
    });

    return grouped;
}

// Function to display grouped matches on the map
function displayGroupedMatchesOnMap(map, groupedMatches) {
    if (!window.coordDict) {
        console.error('Coordinates dictionary is not initialized.');
        return;
    }

    const coordDict = window.coordDict;
    const primaryDict = coordDict.primary || {};
    const cityDict = coordDict.city || {};

    // Clear existing markers
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    const bounds = L.latLngBounds(); // Initialize bounds for map

    Object.keys(groupedMatches).forEach(stadiumName => {
        const matches = groupedMatches[stadiumName];
        let coords = primaryDict[stadiumName];

        // If no coordinates for stadium, try city
        if (!coords && matches.length > 0) {
            const cityName = matches[0].City ? matches[0].City.trim().toLowerCase() : '';
            coords = cityDict[cityName];
        }

        if (coords) {
            const [lat, lng] = coords;
            if (isFinite(lat) && isFinite(lng)) {
                // Create popup content with all matches for this stadium
                const popupContent = createPopupContent(matches);

                L.marker([lat, lng])
                    .addTo(map)
                    .bindPopup(popupContent);

                bounds.extend([lat, lng]); // Extend bounds with valid coordinates
            }
        } else {
            console.log(`Coordinates not found for stadium: ${stadiumName}`);
        }
    });

    if (bounds.isValid()) {
        // Optional: Fit map bounds to show all markers
        map.fitBounds(bounds);
    } else {
        console.log('Bounds are not valid.');
    }
}

// Function to create popup content for all matches at a stadium
function createPopupContent(matches) {
    let popupContent = `<div><strong>Matches at ${matches[0].Stadium}:</strong><br><ul>`;
    matches.forEach(match => {
        popupContent += `<li>${match.Match}<br>Date: ${match.Date}<br>Time: ${match.Time}</li>`;
    });
    popupContent += '</ul></div>';
    return popupContent;
}

// Initialize map and coordinate dictionary on window load
window.onload = () => {
    initializeCoordDict(initMap);
};
