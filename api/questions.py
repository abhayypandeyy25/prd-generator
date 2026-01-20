from http.server import BaseHTTPRequestHandler
import json
import os


def load_questions():
    """Load questions from JSON file"""
    # Try to load from file first
    questions_file = os.path.join(os.path.dirname(__file__), 'data', 'questions.json')
    try:
        with open(questions_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading questions: {e}")
        # Fallback to minimal embedded data
        return {"sections": []}


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        for key, value in cors_headers().items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        return

    def do_GET(self):
        try:
            questions_data = load_questions()

            if not questions_data.get('sections'):
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No questions available',
                    'sections': []
                }).encode())
                return

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(questions_data).encode())
        except Exception as e:
            print(f"Error getting questions: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Failed to load questions: {str(e)}'}).encode())
        return
