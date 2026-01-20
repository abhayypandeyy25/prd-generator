from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from supabase import create_client


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
    if len(parts) >= 3:
        return parts[2]
    return None


def validate_uuid(uuid_str):
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


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
        """Get the generated PRD for a project"""
        try:
            project_id = get_project_id(self.path)

            if not project_id or not validate_uuid(project_id):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid project ID format'}).encode())
                return

            supabase = get_supabase()
            result = supabase.table('prds').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(1).execute()

            if result.data:
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result.data[0]).encode())
            else:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No PRD found. Please generate one first.',
                    'hint': 'Go to the PRD tab and click Generate PRD.'
                }).encode())

        except Exception as e:
            print(f"Error getting PRD: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Failed to get PRD: {str(e)}'}).encode())
        return
