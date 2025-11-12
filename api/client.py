import os
import requests
import json


def get_recommendations(server_url, songs):
    payload = {"songs": songs}

    try:
        # Send the POST request
        response = requests.post(server_url, json=payload)
        response.raise_for_status()

        # Parse the response JSON
        recommendations = response.json()
        return recommendations

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    host = os.environ.get('FLASK_RUN_HOST')
    port = os.environ.get('FLASK_RUN_PORT')

    # Server URL (adjust port if necessary)
    server_url = f"http://localhost:{port}/api/recommend"

    # Example user input
    songs = input("Enter a comma-separated list of songs: ").split(",")

    # Trim whitespace from each song
    songs = [song.strip() for song in songs if song.strip()]

    if not songs:
        print("Error: You must provide at least one song.")
    else:
        # Get recommendations
        result = get_recommendations(server_url, songs)
        # Display the response
        print(json.dumps(result, indent=2))
