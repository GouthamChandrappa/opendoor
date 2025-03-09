"""
Flask server for serving the Door Installation Assistant web UI
"""

import os
import argparse
from flask import Flask, render_template, send_from_directory, request, jsonify

app = Flask(__name__)

# Configuration
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 5000))
API_URL = os.environ.get("API_URL", "http://localhost:8000")

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('templates', 'index.html')

@app.route('/<path:path>')
def serve_page(path):
    """Serve HTML pages"""
    if path.endswith('.html'):
        return send_from_directory('templates', path)
    return send_from_directory('static', path)

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/config')
def get_config():
    """Get UI configuration"""
    return jsonify({
        "apiUrl": API_URL,
        "version": "1.0.0"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "door-installation-ui"
    })

@app.route('/components/<path:path>')
def serve_component(path):
    """Serve component templates"""
    return send_from_directory('templates/components', path)

def load_with_component(template_path, component_data=None):
    """Load a template with component data"""
    # This helper function could be expanded to handle component inclusion
    # For now, we'll just return the template
    return send_from_directory('templates', template_path)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Door Installation Assistant UI Server')
    parser.add_argument('--host', type=str, default=SERVER_HOST, help='Server host')
    parser.add_argument('--port', type=int, default=SERVER_PORT, help='Server port')
    parser.add_argument('--api-url', type=str, default=API_URL, help='API URL')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Update configuration
    SERVER_HOST = args.host
    SERVER_PORT = args.port
    API_URL = args.api_url
    
    # Print startup message
    print(f"Starting Door Installation Assistant UI Server")
    print(f"Server: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"API URL: {API_URL}")
    
    # Start the server
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)