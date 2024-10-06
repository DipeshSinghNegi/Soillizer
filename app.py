from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# API Keys
WEATHER_API_KEY = 'aba1797aeeb5b408ca62ef1a67fa8997'  # OpenWeather API Key
NASA_API_KEY = 'Z1C2eZiWPP868Ihx7WnKhAJJgRqMXuFVxBmPkfEN'  # NASA API Key for SMAP data

# Hardcoded fallback coordinates
FALLBACK_COORDINATES = {'lat': 38.0, 'lon': -97.0}

@app.route('/')
def index():
    return render_template('index.html')

# Fetch weather data from OpenWeather API
@app.route('/weather', methods=['POST', 'GET'])
def fetch_weather_data():
    if request.content_type != 'application/json':
        return {'error': 'Content-Type must be application/json'}, 415  # Unsupported Media Type

    location = request.json.get('location')
    if not location:
        return {'error': 'Location is required'}, 400

    weather_api_url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric'

    try:
        response = requests.get(weather_api_url)
        if response.status_code != 200:
            return {'error': 'Weather data not found'}, 404

        return response.json()
    except Exception as e:
        return {'error': str(e)}, 500

# Fetch soil data from NASA's SMAP API
@app.route('/soil', methods=['POST'])
def fetch_soil_data():
    # Use coordinates from the weather request
    location = request.json.get('location')
    if not location:
        return jsonify({'error': 'Location is required'}), 400

    weather_response = fetch_weather_data()
    lat, lon = weather_response['coord']['lat'], weather_response['coord']['lon']

    soil_api_url = f'https://api-test.openepi.io/soil/type?lat={lat}&lon={lon}'

    try:
        response = requests.get(soil_api_url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch soil data'}), 404

        soil_data = response.json()
        return jsonify(soil_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/soil_properties', methods=['POST'])
def fetch_soil_properties():
    print("Request received for soil properties.")
    location = request.json.get('location')
    if not location:
        return jsonify({'error': 'Location is required'}), 400

    weather_response = fetch_weather_data()
    lat, lon = weather_response['coord']['lat'], weather_response['coord']['lon']

    print(f"Fetching soil properties for lat: {lat}, lon: {lon}")

    try:
        response = requests.get(
            url="https://api-test.openepi.io/soil/property",
            params={
                "lat": lat,
                "lon": lon,
                "depths": "0-5cm",
                "properties": ["bdod", "phh2o"],  # Only these two properties
                "values": ["mean"],
            },
        )

        if response.status_code != 200:
            print("Soil API response not OK:", response.status_code)
            return jsonify({'error': 'Failed to fetch soil data'}), 404

        soil_data = response.json()
        print("Soil data received:", soil_data)

        # Check if properties are available
        properties = soil_data.get('properties')
        bdod_value = None
        phh2o_value = None

        # Extract values
        if properties:
            for layer in properties.get('layers', []):
                if layer['code'] == 'bdod':
                    bdod_value = layer['depths'][0]['values']['mean']
                elif layer['code'] == 'phh2o':
                    phh2o_value = layer['depths'][0]['values']['mean']

        # If both values are None, fetch fallback data
        if bdod_value is None and phh2o_value is None:
            print("No valid data found, attempting fallback with default coordinates.")
            lat, lon = FALLBACK_COORDINATES['lat'], FALLBACK_COORDINATES['lon']
            response = requests.get(
                url="https://api-test.openepi.io/soil/property",
                params={
                    "lat": lat,
                    "lon": lon,
                    "depths": "0-5cm",
                    "properties": ["
