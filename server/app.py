"""
Rememory Server - Main Flask Application
Captures GPS, audio, and photos from client and processes with Gemini
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import json
import base64
from datetime import datetime
from threading import Thread, Lock
import time
from gemini_processor import GeminiProcessor
from config import Config

app = Flask(__name__, static_folder='../client', template_folder='../client')
app.config['SECRET_KEY'] = 'rememory-secret-key-change-in-production'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10e6)

# Initialize Gemini processor
gemini_processor = GeminiProcessor(Config.GEMINI_API_KEY)

# Data directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
PHOTO_DIR = os.path.join(DATA_DIR, 'photos')
LOG_DIR = os.path.join(DATA_DIR, 'logs')

# Ensure directories exist
for directory in [AUDIO_DIR, PHOTO_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Session data storage
current_session = {
    'gps_data': [],
    'audio_chunks': [],
    'photos': [],
    'current_state': 'Initializing Rememory...',
    'last_update': datetime.now().isoformat()
}
session_lock = Lock()

# Background state update task
state_update_running = False

def background_state_updater():
    """Background task that updates state every 3 minutes"""
    global state_update_running
    state_update_running = True

    while state_update_running:
        time.sleep(180)  # 3 minutes

        with session_lock:
            # Prepare data for Gemini
            data_snapshot = {
                'gps_data': current_session['gps_data'].copy(),
                'photos': current_session['photos'].copy(),
                'audio_chunks': len(current_session['audio_chunks'])
            }

        # Process with Gemini
        try:
            new_state = gemini_processor.generate_state(data_snapshot)

            with session_lock:
                current_session['current_state'] = new_state
                current_session['last_update'] = datetime.now().isoformat()

            # Log the state update
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'state': new_state,
                'gps_count': len(data_snapshot['gps_data']),
                'photo_count': len(data_snapshot['photos']),
                'audio_chunks': data_snapshot['audio_chunks']
            }

            log_file = os.path.join(LOG_DIR, f'state_log_{datetime.now().strftime("%Y%m%d")}.jsonl')
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            # Broadcast updated state to connected clients
            socketio.emit('state_update', {
                'state': new_state,
                'timestamp': current_session['last_update']
            })

            print(f"[State Update] {datetime.now().isoformat()}: {new_state[:100]}...")

        except Exception as e:
            print(f"[Error] State update failed: {str(e)}")


@app.route('/')
def index():
    """Serve the main client page"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get current system status"""
    with session_lock:
        return jsonify({
            'status': 'running',
            'current_state': current_session['current_state'],
            'last_update': current_session['last_update'],
            'gps_points': len(current_session['gps_data']),
            'photos': len(current_session['photos']),
            'audio_chunks': len(current_session['audio_chunks'])
        })


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[Client Connected] {request.sid}")
    emit('connected', {
        'message': 'Connected to Rememory server',
        'state': current_session['current_state'],
        'timestamp': current_session['last_update']
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[Client Disconnected] {request.sid}")


@socketio.on('gps_update')
def handle_gps_update(data):
    """Receive GPS location updates"""
    try:
        gps_entry = {
            'timestamp': datetime.now().isoformat(),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'accuracy': data.get('accuracy'),
            'altitude': data.get('altitude'),
            'heading': data.get('heading'),
            'speed': data.get('speed')
        }

        with session_lock:
            current_session['gps_data'].append(gps_entry)
            # Keep only last 100 GPS points to prevent memory issues
            if len(current_session['gps_data']) > 100:
                current_session['gps_data'] = current_session['gps_data'][-100:]

        print(f"[GPS Update] {gps_entry['latitude']:.6f}, {gps_entry['longitude']:.6f}")

    except Exception as e:
        print(f"[Error] GPS update failed: {str(e)}")


@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Receive audio data chunks"""
    try:
        timestamp = datetime.now()
        audio_filename = f"audio_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.webm"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        # Decode base64 audio data
        audio_data = base64.b64decode(data['audio'])

        # Save audio chunk
        with open(audio_path, 'wb') as f:
            f.write(audio_data)

        with session_lock:
            current_session['audio_chunks'].append({
                'timestamp': timestamp.isoformat(),
                'filename': audio_filename,
                'size': len(audio_data)
            })

        print(f"[Audio Chunk] Saved {audio_filename} ({len(audio_data)} bytes)")

    except Exception as e:
        print(f"[Error] Audio chunk save failed: {str(e)}")


@socketio.on('photo_capture')
def handle_photo_capture(data):
    """Receive photo captures"""
    try:
        timestamp = datetime.now()
        photo_filename = f"photo_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        photo_path = os.path.join(PHOTO_DIR, photo_filename)

        # Decode base64 image data
        # Remove data URL prefix if present
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        photo_bytes = base64.b64decode(image_data)

        # Save photo
        with open(photo_path, 'wb') as f:
            f.write(photo_bytes)

        photo_entry = {
            'timestamp': timestamp.isoformat(),
            'filename': photo_filename,
            'path': photo_path,
            'size': len(photo_bytes)
        }

        with session_lock:
            current_session['photos'].append(photo_entry)

        print(f"[Photo Captured] {photo_filename} ({len(photo_bytes)} bytes)")

        emit('photo_saved', {'filename': photo_filename, 'timestamp': timestamp.isoformat()})

    except Exception as e:
        print(f"[Error] Photo save failed: {str(e)}")
        emit('photo_error', {'error': str(e)})


@socketio.on('request_state')
def handle_state_request():
    """Client requests current state"""
    with session_lock:
        emit('state_update', {
            'state': current_session['current_state'],
            'timestamp': current_session['last_update']
        })


if __name__ == '__main__':
    print("=" * 60)
    print("REMEMORY SERVER STARTING")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print(f"Audio directory: {AUDIO_DIR}")
    print(f"Photo directory: {PHOTO_DIR}")
    print(f"Log directory: {LOG_DIR}")
    print("=" * 60)

    # Start background state updater
    updater_thread = Thread(target=background_state_updater, daemon=True)
    updater_thread.start()
    print("[Background Task] State updater started (3-minute interval)")

    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
