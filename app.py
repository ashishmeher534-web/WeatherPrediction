from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/weather")
def get_weather():
    city = request.args.get("city", "").strip()

    if len(city) < 2:
        return jsonify({"error": "Please enter a city name."}), 400

    try:
        # Find the city's coordinates
        geo_response = requests.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=15
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        locations = geo_data.get("results", [])

        if not locations:
            return jsonify({
                "error": "City not found. Try another city name."
            }), 404

        place = locations[0]

        # Fetch current weather and today's hourly forecast
        weather_response = requests.get(
            WEATHER_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,is_day,precipitation,"
                    "rain,showers,snowfall,weather_code,"
                    "cloud_cover,wind_speed_10m,wind_direction_10m"
                ),
                "hourly": (
                    "temperature_2m,precipitation_probability,"
                    "precipitation,weather_code"
                ),
                "forecast_days": 1,
                "timezone": "auto"
            },
            timeout=20
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        current = weather_data.get("current", {})
        hourly = weather_data.get("hourly", {})

        if not current:
            return jsonify({
                "error": "Current weather data is unavailable."
            }), 502

        code = current.get("weather_code", 0)

        # Translate weather codes into readable descriptions
        if code == 0:
            description = "Clear sky"
        elif code in (1, 2, 3):
            description = "Mainly clear / Cloudy"
        elif code in (45, 48):
            description = "Foggy"
        elif code in (51, 53, 55, 56, 57):
            description = "Drizzle"
        elif code in (61, 63, 65, 66, 67):
            description = "Rain"
        elif code in (71, 73, 75, 77):
            description = "Snow"
        elif code in (80, 81, 82):
            description = "Rain showers"
        elif code in (85, 86):
            description = "Snow showers"
        elif code in (95, 96, 99):
            description = "Thunderstorm"
        else:
            description = "Weather conditions unavailable"

        return jsonify({
            "city": place["name"],
            "country": place.get("country", ""),
            "region": place.get("admin1", ""),
            "timezone": weather_data.get("timezone", ""),
            "current": current,
            "description": description,
            "hourly": hourly,
            "source": "Open-Meteo"
        })

    except requests.RequestException:
        return jsonify({
            "error": (
                "Could not connect to the weather service. "
                "Check your internet connection and try again."
            )
        }), 502


if __name__ == "__main__":
    app.run(debug=True)