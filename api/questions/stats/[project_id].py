from http.server import BaseHTTPRequestHandler
import json
import os
from supabase import create_client


def load_questions():
    """Load questions from JSON file"""
    questions_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'questions.json')
    try:
        with open(questions_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading questions: {e}")
        return {"sections": []}


def get_supabase():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured")
    return create_client(url, key)


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


def get_project_id(path):
    parts = path.strip('/').split('/')
    if len(parts) >= 4:
        return parts[3]
    return None


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
            project_id = get_project_id(self.path)
            if not project_id:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Project ID required'}).encode())
                return

            supabase = get_supabase()
            result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
            responses = result.data if result.data else []

            # Load questions and count total
            questions_data = load_questions()
            total_questions = 0
            for section in questions_data.get('sections', []):
                for subsection in section.get('subsections', []):
                    total_questions += len(subsection.get('questions', []))

            confirmed_count = sum(1 for r in responses if r.get('confirmed'))
            ai_suggested_count = sum(1 for r in responses if r.get('ai_suggested'))
            answered_count = sum(1 for r in responses if r.get('response') and r.get('response').strip())

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'total_questions': total_questions,
                'answered': answered_count,
                'confirmed': confirmed_count,
                'ai_suggested': ai_suggested_count,
                'completion_percentage': round((confirmed_count / total_questions) * 100, 1) if total_questions > 0 else 0
            }).encode())
        except Exception as e:
            print(f"Error getting stats: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
        return
