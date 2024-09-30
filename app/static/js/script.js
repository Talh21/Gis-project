function changeMarker(){
    var footballIcon = L.icon({
        iconUrl: 'static/images/location.png',    
        iconSize:     [40, 40], // size of the icon
    });
    return footballIcon

}


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

    Promise.all([
        fetch('/api/matches').then(response => response.json()),
        fetch('/api/stadium-info').then(response => response.json())
    ])
    .then(([matches, stadiumInfo]) => {
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
            filterMatchesAndDisplay(map, matches, stadiumInfo);
        });
    })
    .catch(error => console.error('Error fetching data:', error));
}

// Function to filter matches by date, city, or team
function filterMatchesAndDisplay(map, matches, stadiumInfo) {
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
    displayGroupedMatchesOnMap(map, groupedMatches, stadiumInfo);
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

function displayGroupedMatchesOnMap(map, groupedMatches, stadiumInfo) {
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
            const popupContent = createPopupContent(matches, stadiumInfo);
            const marker = L.marker([lat, lng], {icon:changeMarker()}).addTo(map).bindPopup(popupContent);
            bounds.extend([lat, lng]);  // Extend map bounds to include the marker's location
        } else {
            console.log(`Coordinates not found for stadium: ${stadiumName}`);
        }
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds);  // Adjust map view to fit all markers within bounds
    }
}

function createPopupContent(matches, stadiumInfo) {
    const stadiumName = matches[0].stadium || matches[0].city;
    let stadium = stadiumInfo.find(info => info.stadium.toLowerCase().trim() === stadiumName.toLowerCase().trim());

    if (!stadium) {
        stadium = stadiumInfo.find(info => info.city.toLowerCase().trim() === matches[0].city.toLowerCase().trim());
    }

    // Safely stringify the stadium object
    const sanitizedStadium = JSON.stringify(stadium)
        .replace(/'/g, "&apos;")
        .replace(/"/g, '&quot;');

    let content = `<div class="popup-content">
                    <strong class="stadium-name">${stadiumName} - ${stadium.city}</strong>
                    <button class="info-btn" onclick='showDetailedInfo(${sanitizedStadium})'>
                        <i class="info-icon">i</i>
                    </button>
                    <ul class="match-list">`;

    matches.forEach((match, index) => {
        content += `
            <li class="match-item ${index % 2 === 0 ? 'even' : 'odd'}">
                <div class="match-title"><strong>${match.home_team} vs ${match.away_team}</strong></div>
                <div class="match-details">League: ${match.league}</div>
                <div class="match-details">Matchday: ${match.matchday}</div>
                <div class="match-details">Date: ${match.date}</div>
                <div class="match-details">Day: ${match.day}</div>
                <div class="match-details">Time: ${match.time ? match.time : 'N/A'}</div>
            </li>`;
    });

    content += '</ul></div>';

    return content;
}



function showDetailedInfo(stadium) {
    if (stadium) {
        // Construct the popup content
        let popupContent = `
            <div class="popup-content">
                <img src="${stadium.image_url ? stadium.image_url : '/static/images/home_screen.jpg'}" alt="Stadium Image" style="width:100%; height:auto;">
                <div>
                    <p><strong>Stadium Name:</strong> ${stadium.stadium}</p>
                    <p><strong>Capacity:</strong> ${stadium.capacity ? stadium.capacity : 'N/A'}</p>
                    <p><strong>Field Size:</strong> ${stadium.field_size ? stadium.field_size : 'N/A'}</p>
                    <p><strong>Opened:</strong> ${stadium.opened_date ? stadium.opened_date : 'N/A'}</p>
                    
                </div>
                <a href="${stadium.url}">More info</a>
            </div>
        `;
        

        
        // Find the stadium's coordinates in the map
        const stadiumName = stadium.stadium.toLowerCase().trim();
        const coords = window.coordDict.primary[stadiumName] || window.coordDict.city[stadium.city.toLowerCase().trim()];

        if (coords) {
            const [lat, lng] = coords;

            // Create a new popup on the map
            const popup = L.popup()
                .setLatLng([lat, lng])  // Set the popup location based on the stadium's coordinates
                .setContent(popupContent)  // Set the content to include the stadium image and details
                .openOn(window.map);  // Open the popup on the map

        } else {
            console.log(`Coordinates not found for stadium: ${stadium.stadium}`);
        }
    } else {
        console.log('Stadium information not available.');
    }
}


function setMinDate() {
    const today = new Date().toISOString().split('T')[0];  // Get the current date in YYYY-MM-DD format
    document.getElementById('startDate').setAttribute('min', today);
    document.getElementById('endDate').setAttribute('min', today);
}


window.onload = () => {
    setMinDate();  // Set the min date for date inputs when the page loads
    initializeCoordDict(initMap);
};
