// Function to initialize coordinate dictionaries
function initializeCoordDict(callback) {
    const primaryDict = {};
    const cityDict = {};

    fetch('/api/stadium-coordinates')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            data.forEach(row => {
                const stadiumName = row.stadium ? row.stadium.toLowerCase().trim() : '';
                const cityName = row.city ? row.city.toLowerCase().trim() : '';
                const lat = parseFloat(row.latitude);
                const lng = parseFloat(row.longitude);

                if (stadiumName && !isNaN(lat) && !isNaN(lng)) {
                    primaryDict[stadiumName] = [lat, lng];
                }
                if (cityName && !isNaN(lat) && !isNaN(lng)) {
                    cityDict[cityName] = [lat, lng];
                }
            });

            window.coordDict = { primary: primaryDict, city: cityDict };
            if (callback) callback();
        })
        .catch(error => console.error('Error fetching coordinates:', error));
}

// Initialize Leaflet map
function initMap() {
    const map = L.map('map').setView([32.0853, 34.7818], 8);
    window.map = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {}).addTo(map);

    fetch('/api/matches')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(matches => {
            if (!window.coordDict) {
                console.error('Coordinates dictionary is not initialized.');
                return;
            }

            const filterBtn = document.getElementById('filterBtn');
            if (!filterBtn) {
                console.error('Filter button not found.');
                return;
            }

            filterBtn.addEventListener('click', () => {
                filterMatchesAndDisplay(map, matches);
            });
        })
        .catch(error => console.error('Error fetching matches:', error));
}

// Function to filter matches by date, city, or team
function filterMatchesAndDisplay(map, matches) {
    const startDate = new Date(document.getElementById('startDate').value);
    const endDate = new Date(document.getElementById('endDate').value);
    const city = document.getElementById('city').value.toLowerCase().trim();
    const team = document.getElementById('team').value.toLowerCase().trim();

    const filteredMatches = matches.filter(match => {
        const matchDate = new Date(match.date);
        const matchCity = match.city ? match.city.toLowerCase().trim() : '';
        const homeTeam = match.home_team ? match.home_team.toLowerCase().trim() : '';
        const awayTeam = match.away_team ? match.away_team.toLowerCase().trim() : '';

        return (isNaN(startDate) || matchDate >= startDate) &&
               (isNaN(endDate) || matchDate <= endDate) &&
               (city === '' || matchCity.includes(city)) &&
               (team === '' || homeTeam.includes(team) || awayTeam.includes(team));
    });

    const groupedMatches = groupMatchesByStadium(filteredMatches);
    displayGroupedMatchesOnMap(map, groupedMatches);
}

function groupMatchesByStadium(matches) {
    const grouped = {};
    matches.forEach(match => {
        const stadiumName = match.stadium ? match.stadium.trim().toLowerCase() : '';
        if (!grouped[stadiumName]) {
            grouped[stadiumName] = [];
        }
        grouped[stadiumName].push(match);
    });
    return grouped;
}

function displayGroupedMatchesOnMap(map, groupedMatches) {
    if (!window.coordDict) {
        console.error('Coordinates dictionary is not initialized.');
        return;
    }

    const primaryDict = window.coordDict.primary || {};
    const cityDict = window.coordDict.city || {};

    // Remove existing markers
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    const bounds = L.latLngBounds();

    Object.keys(groupedMatches).forEach(stadiumName => {
        const matches = groupedMatches[stadiumName];
        let coords = primaryDict[stadiumName] || cityDict[matches[0].city.toLowerCase().trim()];

        if (coords) {
            const [lat, lng] = coords;
            const popupContent = createPopupContent(matches);
            const marker = L.marker([lat, lng]).addTo(map).bindPopup(popupContent);
            bounds.extend([lat, lng]);  // Extend map bounds to include the marker's location
        } else {
            console.log(`Coordinates not found for stadium: ${stadiumName}`);
        }
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds);  // Adjust map view to fit all markers within bounds
    }
}



function createPopupContent(matches) {
    let content = `<div class="popup-content"><strong>Matches at ${matches[0].stadium || matches[0].city}:</strong><ul>`;
    if (matches.length > 0) {
        content += `<li>Capacity: ${matches[0].capacity || 'N/A'}</li>`;
        content += `<li>Field Size: ${matches[0].field_size || 'N/A'}</li>`;
        content += `<li>Opened: ${matches[0].opened_date || 'N/A'}</li>`;
        content += `<li><img src="${matches[0].image_url || '#'}" alt="Stadium Image" style="width: 100px; height: auto;"></li>`;
    }
    content += `<table class="match-table">`;
    matches.forEach(match => {
        content += `
            <tr>
                <td><strong>${match.home_team} vs ${match.away_team}</strong></td>
            </tr>
            <tr>
                <td>Date: ${match.date}</td>
            </tr>
            <tr>
                <td>Day: ${match.day}</td>
            </tr>
            <tr>
                <td>Time: ${match.time != null ? match.time : 'N/A'}</td>
            </tr>`;
    });
    content += '</table></div>';
    return content;
}


window.onload = () => {
    initializeCoordDict(initMap);
};
