from flask import Flask, jsonify, render_template_string, request
import math

app = Flask(__name__)

# --- 1. DATA CONFIGURATION ---

# Default coordinates (Kochi/Ernakulam area)
START_POINT = {"lat": 9.9816, "lng": 76.2999, "label": "Start: General Hospital"}
END_POINT = {"lat": 10.0261, "lng": 76.3125, "label": "Destination: Medical Center"}

# Dynamic Traffic Signal Intersections along the corridor
SIGNALS = [
    {"id": "SIG_1", "name": "MG Road Junction", "lat": 9.9920, "lng": 76.3020, "status": "RED"},
    {"id": "SIG_2", "name": "Palarivattom Bypass", "lat": 10.0050, "lng": 76.3060, "status": "RED"},
    {"id": "SIG_3", "name": "Edappally Intersection", "lat": 10.0180, "lng": 76.3100, "status": "RED"}
]

# --- 2. CORE UTILITY FUNCTIONS ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates approximate distance in kilometers between two GPS points using Haversine formula."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- 3. API ENDPOINTS ---

@app.route("/")
def home():
    """Serves the interactive frontend web dashboard."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/traffic-update", methods=["POST"])
def traffic_update():
    """Receives ambulance GPS position and dynamically toggles traffic signal status."""
    data = request.get_json()
    ambulance_lat = data.get("lat")
    ambulance_lng = data.get("lng")
    
    # Preemption threshold: 0.5 km (500 meters)
    THRESHOLD_KM = 0.5 
    
    updated_signals = []
    for sig in SIGNALS:
        dist = calculate_distance(ambulance_lat, ambulance_lng, sig["lat"], sig["lng"])
        
        # Override to GREEN if ambulance is within 500m radius
        if dist <= THRESHOLD_KM:
            status = "GREEN (Corridor Override)"
            color = "green"
        else:
            status = "RED (Normal Flow)"
            color = "red"
            
        updated_signals.append({
            "id": sig["id"],
            "name": sig["name"],
            "lat": sig["lat"],
            "lng": sig["lng"],
            "distance_km": round(dist, 2),
            "status": status,
            "color": color
        })
        
    return jsonify({
        "ambulance_position": {"lat": ambulance_lat, "lng": ambulance_lng},
        "signals": updated_signals
    })


# --- 4. EMBEDDED FRONTEND DASHBOARD (HTML + JS + LEAFLET.JS) ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GreenCorridor AI - Urban Intelligence Dashboard</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; height: 100vh; }
        #sidebar { width: 350px; background: #1f2937; color: white; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; }
        #map { flex: 1; height: 100%; }
        h2 { margin-top: 0; color: #38bdf8; font-size: 1.2rem; }
        .btn { background: #0284c7; color: white; border: none; padding: 12px; width: 100%; font-size: 1rem; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #0369a1; }
        .card { background: #374151; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
        .green { color: #4ade80; font-weight: bold; }
        .red { color: #f87171; font-weight: bold; }
    </style>
</head>
<body>

<div id="sidebar">
    <div>
        <h2>🚨 GreenCorridor AI</h2>
        <p><small>Urban Intelligence Emergency Traffic Clearing System</small></p>
        <button class="btn" onclick="startSimulation()">🚀 Start Ambulance Dispatch</button>
        <hr style="border-color: #4b5563; margin: 20px 0;">
        <h3>🚦 Intersection Status</h3>
        <div id="signals-container">Click start to initiate simulation...</div>
    </div>
    <div>
        <p style="font-size: 0.8rem; color: #9ca3af;">Domain 01: Urban Intelligence Project</p>
    </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // Initialize Map
    const map = L.map('map').setView([10.0050, 76.3060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Route coordinates
    const startPoint = [9.9816, 76.2999];
    const endPoint = [10.0261, 76.3125];

    // Draw route polyline
    const route = L.polyline([startPoint, [9.9920, 76.3020], [10.0050, 76.3060], [10.0180, 76.3100], endPoint], {color: '#0284c7', weight: 5}).addTo(map);

    // Ambulance Marker
    let ambulanceIcon = L.divIcon({html: '🚑', className: 'ambulance-icon', iconSize: [30, 30]});
    let ambulanceMarker = L.marker(startPoint, {icon: ambulanceIcon}).addTo(map).bindPopup("Emergency Dispatcher #108");

    // Markers storage
    let signalMarkers = {};

    function startSimulation() {
        let steps = 20;
        let step = 0;

        let interval = setInterval(() => {
            if (step > steps) {
                clearInterval(interval);
                alert("Destination Reached! Corridor Closed.");
                return;
            }

            // Interpolate position along path
            let currentLat = startPoint[0] + (endPoint[0] - startPoint[0]) * (step / steps);
            let currentLng = startPoint[1] + (endPoint[1] - startPoint[1]) * (step / steps);

            ambulanceMarker.setLatLng([currentLat, currentLng]);

            // Send GPS position update to Flask API
            fetch('/api/traffic-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: currentLat, lng: currentLng })
            })
            .then(res => res.json())
            .then(data => {
                updateDashboard(data.signals);
            });

            step++;
        }, 1000);
    }

    function updateDashboard(signals) {
        let container = document.getElementById('signals-container');
        container.innerHTML = '';

        signals.forEach(sig => {
            // Render UI Card
            let card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <strong>${sig.name}</strong><br>
                Dist: ${sig.distance_km} km<br>
                Status: <span class="${sig.color}">${sig.status}</span>
            `;
            container.appendChild(card);

            // Update Map Marker
            if (!signalMarkers[sig.id]) {
                signalMarkers[sig.id] = L.circleMarker([sig.lat, sig.lng], { radius: 10 }).addTo(map);
            }
            signalMarkers[sig.id].setStyle({ color: sig.color, fillColor: sig.color, fillOpacity: 0.8 });
        });
    }
</script>

</body>
</html>
"""

# --- 5. APP EXECUTION ENTRYPOINT ---

if __name__ == "__main__":
    print("\nStarting GreenCorridor AI Server...")
    print("Open your browser and navigate to: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
    