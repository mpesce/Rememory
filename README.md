# Rememory - Personal Memory Capture System

Rememory is an assistive technology system that turns a smartphone into a full-featured capture device for individuals with memory disorders. It continuously captures GPS location, audio, and photos, then uses Google Gemini AI to provide real-time situational awareness.

## Features

- **Continuous GPS Tracking**: Monitors location in real-time
- **Audio Streaming**: Captures ambient audio for conversation transcription
- **Photo Capture**: Takes photos at configurable intervals (default: every 60 seconds)
- **AI-Powered State Generation**: Uses Google Gemini to synthesize location, audio, and visual data into a coherent summary
- **Real-Time Updates**: State refreshes every 3 minutes with current context
- **Simple Web Interface**: No app installation required - works in any mobile browser

## System Architecture

```
┌─────────────────┐
│  Smartphone     │
│  Web Browser    │
│  - GPS          │
│  - Camera       │
│  - Microphone   │
└────────┬────────┘
         │ WebSocket
         │
┌────────▼────────┐
│  Flask Server   │
│  - Data Storage │
│  - Gemini API   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Google Gemini  │
│  - Location     │
│  - Transcription│
│  - Vision       │
│  - Summary      │
└─────────────────┘
```

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Modern web browser (Chrome, Safari, Firefox, Edge)
- HTTPS connection or localhost (required for camera/microphone access)

## Installation

### 1. Clone or Download the Repository

```bash
cd Rememory
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

Create a configuration file from the template:

```bash
cp server/config.json.template server/config.json
```

Edit `server/config.json` and add your Gemini API key:

```json
{
  "GEMINI_API_KEY": "your-actual-api-key-here"
}
```

## Usage

### Starting the Server

```bash
python server/app.py
```

The server will start on `http://0.0.0.0:5000`

You should see output like:

```
============================================================
REMEMORY SERVER STARTING
============================================================
Data directory: /path/to/Rememory/data
Audio directory: /path/to/Rememory/data/audio
Photo directory: /path/to/Rememory/data/photos
Log directory: /path/to/Rememory/data/logs
============================================================
[Background Task] State updater started (3-minute interval)
[Gemini] Initialized with model: gemini-2.0-flash-exp
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

### Accessing the Client

#### On the Same Device (Testing)

Open your web browser and navigate to:
```
http://localhost:5000
```

#### On a Smartphone (Production Use)

1. Find your computer's local IP address:
   - **macOS/Linux**: Run `ifconfig` or `ip addr`
   - **Windows**: Run `ipconfig`

2. On your smartphone, navigate to:
   ```
   http://YOUR_COMPUTER_IP:5000
   ```
   Example: `http://192.168.1.100:5000`

3. Grant permissions when prompted:
   - Camera access
   - Microphone access
   - Location access

4. Click "Start Rememory"

### Using Rememory

Once started, the app will:

1. **Track your location** continuously via GPS
2. **Capture photos** at your configured interval (default: every 60 seconds)
3. **Record audio** in 5-second chunks for continuous monitoring
4. **Update your current state** every 3 minutes using Gemini AI

The main screen displays:
- **Current Situation**: AI-generated summary of where you are and what's happening
- **Statistics**: Photos captured, GPS updates, audio chunks, session time
- **Controls**: Adjust photo capture interval

## Configuration

### Photo Capture Interval

Adjust the slider in the web interface (10-300 seconds). Default is 60 seconds.

### State Update Frequency

Currently set to 3 minutes. To change this, edit `server/config.py`:

```python
STATE_UPDATE_INTERVAL = 180  # seconds (3 minutes)
```

### Data Storage

All captured data is stored in the `data/` directory:

```
data/
├── audio/          # Audio chunks (.webm files)
├── photos/         # Captured photos (.jpg files)
└── logs/           # State update logs (.jsonl files)
```

## HTTPS / SSL Setup (Recommended for Production)

For production use, especially over the internet, you should use HTTPS. Modern browsers require HTTPS for camera and microphone access (except on localhost).

### Option 1: Using ngrok (Quick & Easy)

```bash
# Install ngrok from https://ngrok.com
ngrok http 5000
```

This will give you an HTTPS URL like `https://abc123.ngrok.io`

### Option 2: Self-Signed Certificate (Local Network)

```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Modify app.py to use SSL
# Add to the bottom of server/app.py:
# socketio.run(app, host='0.0.0.0', port=5000,
#              certfile='cert.pem', keyfile='key.pem')
```

### Option 3: Let's Encrypt (Public Server)

For a public-facing server, use [Certbot](https://certbot.eff.org/) with a reverse proxy like nginx.

## Troubleshooting

### "GEMINI_API_KEY not found" Error

Make sure you created `server/config.json` with your API key:
```json
{
  "GEMINI_API_KEY": "your-key-here"
}
```

### Camera/Microphone Not Working

- Ensure you're using HTTPS or localhost
- Check browser permissions in Settings
- Try a different browser (Chrome recommended)
- On iOS, use Safari (Chrome iOS doesn't support getUserMedia well)

### Connection Issues

- Check firewall settings
- Ensure server and client are on the same network
- Try disabling VPN temporarily
- Check the browser console (F12) for errors

### High Data Usage

Audio and photos consume bandwidth. On cellular:
- Increase photo capture interval
- Consider audio chunk size reduction
- Use WiFi when possible

## Privacy & Security Notes

This system captures sensitive personal data:

- Audio recordings of conversations
- Photos of your surroundings
- GPS location history

**Important:**
- All data is stored locally on the server machine
- No data is sent to third parties except Google Gemini API for processing
- Secure your server and API keys
- Consider encrypting the `data/` directory
- Review Google's data usage policy for Gemini API

## Future Enhancements

Potential improvements for future versions:

- [ ] Photo analysis using Gemini Vision
- [ ] Audio transcription with speaker identification
- [ ] Voice commands for hands-free operation
- [ ] Cloud storage integration
- [ ] Multi-user support
- [ ] Emergency contact alerts
- [ ] Geofencing and location alerts
- [ ] Daily activity summaries
- [ ] Export to PDF or email

## Technical Details

### Backend Stack
- **Python 3.8+**
- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support for real-time communication
- **Google Generative AI**: Gemini API integration

### Frontend Stack
- **Vanilla HTML/CSS/JavaScript**: No frameworks
- **Socket.IO**: Real-time bidirectional communication
- **Web APIs**: getUserMedia, Geolocation, MediaRecorder

### Data Flow

1. Client captures GPS, audio, and photos
2. Data streamed via WebSocket to Flask server
3. Server stores data in local filesystem
4. Every 3 minutes, background task:
   - Collects recent data
   - Sends to Gemini API for analysis
   - Receives contextual state summary
   - Broadcasts to connected clients
   - Logs to file

## License

This project is provided as-is for assistive technology purposes.

## Support

For issues or questions, please open an issue on the project repository.

---

Built with care for those who need help remembering.
