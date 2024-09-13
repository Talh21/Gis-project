// Function to initialize coordinate dictionaries
function initializeCoordDict(callback) {
    const primaryDict = {};
    const cityDict = {};

    Papa.parse('/static/data/stadium_coordinates.csv', {
        download: true,
        header: true,
        complete: (results) => {
            results.data.forEach(row => {
                const stadiumName = row.Stadium ? row.Stadium.toLowerCase() : '';
                const cityName = row.City ? row.City.toLowerCase() : '';
                const lat = parseFloat(row.Latitude);
                const lng = parseFloat(row.Longitude);

                if (stadiumName && !isNaN(lat) && !isNaN(lng)) {
                    primaryDict[stadiumName] = [lat, lng];
                }
                if (cityName && !isNaN(lat) && !isNaN(lng)) {
                    cityDict[cityName] = [lat, lng];
                }
            });

            window.coordDict = { primary: primaryDict, city: cityDict };
            if (callback) callback();
        },
        error: (error) => console.error('Error loading coordinates CSV:', error)
    });
}

// Initialize Leaflet map
function initMap() {
    const map = L.map('map').setView([32.0853, 34.7818], 8); 
    window.map = map;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        
    }).addTo(map);


    Papa.parse('/static/data/Ligat_HaAl_Fixtures.csv', {
        download: true,
        header: true,
        complete: (results) => {
            const matches = results.data;

            if (!window.coordDict) {
                console.error('Coordinates dictionary is not initialized.');
                return;
            }

            document.getElementById('filterBtn').addEventListener('click', () => {
                filterMatchesAndDisplay(map, matches);
            });
        },
        error: (error) => console.error('Error loading matches CSV:', error)
    });
}

// Function to filter matches by date, city, or team
function filterMatchesAndDisplay(map, matches) {
    const startDate = new Date(document.getElementById('startDate').value);
    const endDate = new Date(document.getElementById('endDate').value);
    const city = document.getElementById('city').value.toLowerCase();
    const team = document.getElementById('team').value.toLowerCase();

    const filteredMatches = matches.filter(match => {
        const matchDate = new Date(match.Date);
        const matchCity = match.City ? match.City.toLowerCase() : '';
        const matchTeam = match.Match ? match.Match.toLowerCase() : '';

        return (isNaN(startDate) || matchDate >= startDate) &&
               (isNaN(endDate) || matchDate <= endDate) &&
               (city === '' || matchCity.includes(city)) &&
               (team === '' || matchTeam.includes(team));
    });

    const groupedMatches = groupMatchesByStadium(filteredMatches);
    displayGroupedMatchesOnMap(map, groupedMatches);
}

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

function displayGroupedMatchesOnMap(map, groupedMatches) {
    if (!window.coordDict) {
        console.error('Coordinates dictionary is not initialized.');
        return;
    }

    const primaryDict = window.coordDict.primary || {};
    const cityDict = window.coordDict.city || {};

    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    const bounds = L.latLngBounds();
    Object.keys(groupedMatches).forEach(stadiumName => {
        const matches = groupedMatches[stadiumName];
        let coords = primaryDict[stadiumName] || cityDict[matches[0].City.trim().toLowerCase()];

        if (coords) {
            const [lat, lng] = coords;
            const popupContent = createPopupContent(matches);
            L.marker([lat, lng]).addTo(map).bindPopup(popupContent);
            bounds.extend([lat, lng]);
        } else {
            console.log(`Coordinates not found for stadium: ${stadiumName}`);
        }
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds);
    }
}

function createPopupContent(matches) {
    let content = `<div><strong>Matches at ${matches[0].Stadium}:</strong><ul>`;
    matches.forEach(match => {
        content += `<li>${match.Match}<br>Date: ${match.Date}<br>Time: ${match.Time}</li>`;
    });
    content += '</ul></div>';
    return content;
}

window.onload = () => {
    initializeCoordDict(initMap);
};
