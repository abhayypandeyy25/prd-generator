from http.server import BaseHTTPRequestHandler
import json
import os
from supabase import create_client

# Import authentication middleware
from auth_middleware import require_auth, get_user_from_request, is_auth_enabled


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
        """List all projects or get single project (requires auth)"""
        # Check authentication
        user_id = get_user_from_request(self)
        if is_auth_enabled() and not user_id:
            self.send_json(401, {'error': 'Unauthorized', 'message': 'Please sign in to continue'})
            return

        try:
            project_id = get_project_id(self.path)
            supabase = get_supabase()

            if project_id:
                # Get single project - filter by user_id for security
                query = supabase.table('projects').select('*').eq('id', project_id)
                if user_id:
                    query = query.eq('user_id', user_id)
                result = query.execute()

                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Project not found'})
            else:
                # List all projects for this user
                query = supabase.table('projects').select('*')
                if user_id:
                    query = query.eq('user_id', user_id)
                result = query.order('created_at', desc=True).execute()
                self.send_json(200, result.data if result.data else [])
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        """Create a new project (requires auth)"""
        # Check authentication
        user_id = get_user_from_request(self)
        if is_auth_enabled() and not user_id:
            self.send_json(401, {'error': 'Unauthorized', 'message': 'Please sign in to continue'})
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            name = data.get('name', '').strip()
            if not name:
                self.send_json(400, {'error': 'Project name is required'})
                return

            supabase = get_supabase()

            # Include user_id when creating project
            insert_data = {'name': name}
            if user_id:
                insert_data['user_id'] = user_id

            result = supabase.table('projects').insert(insert_data).execute()

            if result.data:
                self.send_json(201, result.data[0])
            else:
                self.send_json(500, {'error': 'Failed to create project'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_DELETE(self):
        """Delete a project (requires auth)"""
        # Check authentication
        user_id = get_user_from_request(self)
        if is_auth_enabled() and not user_id:
            self.send_json(401, {'error': 'Unauthorized', 'message': 'Please sign in to continue'})
            return

        try:
            project_id = get_project_id(self.path)
            if not project_id:
                self.send_json(400, {'error': 'Project ID required'})
                return

            supabase = get_supabase()

            # Only delete if project belongs to user
            query = supabase.table('projects').delete().eq('id', project_id)
            if user_id:
                query = query.eq('user_id', user_id)
            query.execute()

            self.send_json(200, {'message': 'Project deleted'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
