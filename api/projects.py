from http.server import BaseHTTPRequestHandler
import json
import os
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
        'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }


def get_project_id(path):
    """Extract project ID from path like /api/projects/[id]"""
    parts = path.strip('/').split('/')
    if len(parts) >= 3 and parts[2]:
        return parts[2]
    return None


class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        for key, value in cors_headers().items():
            self.send_header(key, value)

    def send_json(self, status, data):
        """Helper to send JSON response"""
        self.send_response(status)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        return

    def do_GET(self):
        """List all projects or get single project"""
        try:
            project_id = get_project_id(self.path)
            supabase = get_supabase()

            if project_id:
                # Get single project
                result = supabase.table('projects').select('*').eq('id', project_id).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Project not found'})
            else:
                # List all projects
                result = supabase.table('projects').select('*').order('created_at', desc=True).execute()
                self.send_json(200, result.data if result.data else [])
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        """Create a new project"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            name = data.get('name', '').strip()
            if not name:
                self.send_json(400, {'error': 'Project name is required'})
                return

            supabase = get_supabase()
            result = supabase.table('projects').insert({'name': name}).execute()

            if result.data:
                self.send_json(201, result.data[0])
            else:
                self.send_json(500, {'error': 'Failed to create project'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_DELETE(self):
        """Delete a project"""
        try:
            project_id = get_project_id(self.path)
            if not project_id:
                self.send_json(400, {'error': 'Project ID required'})
                return

            supabase = get_supabase()
            supabase.table('projects').delete().eq('id', project_id).execute()
            self.send_json(200, {'message': 'Project deleted'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
