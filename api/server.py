"""
Flask REST API Server for Spotify Playlist Recommendations
Exposes endpoint at /api/recommend that accepts song lists and returns recommendations

Note: The model uses normalized track names (lowercase, no punctuation).
Input songs should be provided as normalized track names, not Spotify URIs.
"""

from flask import Flask, request, jsonify
import pickle
import os
from datetime import datetime
from pathlib import Path
import sys
import unicodedata
import string

# Add parent directory to path to import RulesGenerator
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)

# Configuration
MODEL_PATH = os.environ.get('MODEL_PATH', '/home/giovanamachado/TP2/rules_ds1.pkl')
VERSION = os.environ.get('API_VERSION', '1.0.0')
PORT = int(os.environ.get('API_PORT', '50013'))

# Global variables to store model and metadata
app.model_data = None
app.model_date = None


def normalize_track_name(track_name):
    """
    Normalize track name to match the format used in the model.
    Converts to lowercase, removes punctuation, normalizes unicode.
    
    Args:
        track_name (str): Original track name
        
    Returns:
        str: Normalized track name
    """
    track_name = track_name.lower()
    track_name = unicodedata.normalize('NFC', track_name)
    track_name = track_name.strip()
    track_name = track_name.translate(str.maketrans('', '', string.punctuation))
    return track_name


def load_model(model_path):
    """
    Load the association rules model from pickle file.
    
    Args:
        model_path (str): Path to the pickle file containing rules DataFrame
        
    Returns:
        tuple: (rules_dataframe, model_date_string)
    """
    try:
        with open(model_path, 'rb') as f:
            rules_df = pickle.load(f)
        
        # Get file modification time as model date
        mod_time = os.path.getmtime(model_path)
        model_date = datetime.fromtimestamp(mod_time).isoformat()
        
        print(f"✓ Model loaded from: {model_path}")
        print(f"  - Rules count: {len(rules_df)}")
        print(f"  - Model date: {model_date}")
        
        if len(rules_df) > 0:
            print(f"  - Avg confidence: {rules_df['confidence'].mean():.4f}")
            print(f"  - Avg lift: {rules_df['lift'].mean():.4f}")
        
        return rules_df, model_date
    except FileNotFoundError:
        print(f"ERROR: Model file not found at {model_path}")
        raise
    except Exception as e:
        print(f"ERROR loading model: {e}")
        raise


def get_recommendations(input_songs, rules_df, top_n=10, min_confidence=0.3, min_lift=1.0):
    """
    Generate song recommendations based on input songs using association rules.
    
    Args:
        input_songs (list): List of song identifiers (normalized track names)
        rules_df (DataFrame): DataFrame containing association rules
        top_n (int): Maximum number of recommendations to return
        min_confidence (float): Minimum confidence threshold for rules
        min_lift (float): Minimum lift threshold for rules
        
    Returns:
        list: List of recommended song identifiers
    """
    if not input_songs:
        return []
    
    if len(rules_df) == 0:
        return []
    
    # Normalize input songs to match model format
    normalized_input = {normalize_track_name(song) for song in input_songs}
    input_set = normalized_input
    
    # Find rules where antecedents are in the input songs
    # Score recommendations by confidence * lift (can be adjusted)
    recommendations = {}
    
    for idx, rule in rules_df.iterrows():
        antecedents = set(rule['antecedents'])
        consequents = set(rule['consequents'])
        
        # Check if any antecedent is in the input songs
        # and consequents are not already in input
        if antecedents.intersection(input_set) and not consequents.intersection(input_set):
            # Filter by thresholds
            if rule['confidence'] >= min_confidence and rule['lift'] >= min_lift:
                # Add consequents to recommendations
                for song in consequents:
                    if song not in input_set:
                        # Score = confidence * lift (higher is better)
                        score = rule['confidence'] * rule['lift']
                        
                        # Keep the best score for each song
                        if song not in recommendations or score > recommendations[song]:
                            recommendations[song] = score
    
    # Sort by score and return top N
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    recommended_songs = [song for song, score in sorted_recommendations[:top_n]]
    
    return recommended_songs


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """
    REST endpoint for song recommendations.
    
    Request JSON format:
        {
            "songs": ["song_id_1", "song_id_2", ...],
            "top_n": 10 (optional),
            "min_confidence": 0.3 (optional),
            "min_lift": 1.0 (optional)
        }
    
    Response JSON format:
        {
            "songs": ["recommended_song_1", "recommended_song_2", ...],
            "version": "1.0.0",
            "model_date": "2025-11-05T12:34:56"
        }
    """
    try:
        # Parse JSON from request
        data = request.get_json(force=True)
        
        if not data or 'songs' not in data:
            return jsonify({
                'error': 'Invalid request format. Expected JSON with "songs" field.'
            }), 400
        
        input_songs = data['songs']
        
        if not isinstance(input_songs, list):
            return jsonify({
                'error': '"songs" field must be a list.'
            }), 400
        
        # Optional parameters
        top_n = data.get('top_n', 10)
        min_confidence = data.get('min_confidence', 0.3)
        min_lift = data.get('min_lift', 1.0)
        
        # Check if model is loaded
        if app.model_data is None:
            return jsonify({
                'error': 'Model not loaded. Server initialization failed.'
            }), 503
        
        # Generate recommendations (app.model_data is now the rules DataFrame)
        recommended_songs = get_recommendations(
            input_songs, 
            app.model_data,
            top_n=top_n,
            min_confidence=min_confidence,
            min_lift=min_lift
        )
        
        # Build response
        response = {
            'songs': recommended_songs,
            'version': VERSION,
            'model_date': app.model_date
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint for Kubernetes probes.
    Returns 200 if the service is healthy and model is loaded.
    """
    if app.model_data is None:
        return jsonify({
            'status': 'unhealthy',
            'reason': 'Model not loaded'
        }), 503
    
    return jsonify({
        'status': 'healthy',
        'version': VERSION,
        'model_date': app.model_date,
        'model_rules': len(app.model_data) if app.model_data is not None else 0
    }), 200


@app.route('/api/stats', methods=['GET'])
def stats():
    """
    Statistics endpoint showing model information.
    """
    if app.model_data is None:
        return jsonify({
            'error': 'Model not loaded'
        }), 503
    
    return jsonify({
        'version': VERSION,
        'model_date': app.model_date,
        'total_rules': len(app.model_data),
        'avg_confidence': float(app.model_data['confidence'].mean()) if len(app.model_data) > 0 else 0,
        'avg_lift': float(app.model_data['lift'].mean()) if len(app.model_data) > 0 else 0,
        'port': PORT
    }), 200


# Initialize the application
def init_app():
    """Initialize the Flask application by loading the model."""
    try:
        print("=" * 80)
        print("INITIALIZING SPOTIFY RECOMMENDATION API SERVER")
        print("=" * 80)
        print(f"Version: {VERSION}")
        print(f"Model path: {MODEL_PATH}")
        print(f"Port: {PORT}")
        print("=" * 80)
        
        # Load the model
        app.model_data, app.model_date = load_model(MODEL_PATH)
        
        print("=" * 80)
        print("✓ SERVER READY")
        print(f"  Endpoints available:")
        print(f"    POST /api/recommend - Get song recommendations")
        print(f"    GET  /api/health    - Health check")
        print(f"    GET  /api/stats     - Model statistics")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        print("Server will start but /api/recommend will return 503 errors")
        app.model_data = None
        app.model_date = None


# Initialize on startup
init_app()


if __name__ == '__main__':
    # Run the Flask development server
    # In production, use a WSGI server like gunicorn
    app.run(host='0.0.0.0', port=PORT, debug=False)
