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
        'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


def get_project_id(path):
    parts = path.strip('/').split('/')
    if len(parts) >= 4:
        return parts[3]
    return None


def validate_uuid(uuid_str):
    """Validate UUID format"""
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
        """Get all saved responses for a project"""
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

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result.data if result.data else []).encode())
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
        return

    def do_PUT(self):
        """Save/update multiple question responses"""
        try:
            project_id = get_project_id(self.path)
            if not project_id or not validate_uuid(project_id):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid project ID format'}).encode())
                return

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            responses = data.get('responses', [])
            if not responses:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No responses provided'}).encode())
                return

            supabase = get_supabase()

            # Check if project exists
            project_result = supabase.table('projects').select('*').eq('id', project_id).execute()
            if not project_result.data:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                return

            saved = []
            for resp in responses:
                question_id = resp.get('question_id')
                if not question_id:
                    continue

                # Check if response exists
                existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', question_id).execute()

                response_data = {
                    'project_id': project_id,
                    'question_id': question_id,
                    'response': resp.get('response', ''),
                    'ai_suggested': resp.get('ai_suggested', False),
                    'confirmed': resp.get('confirmed', False)
                }

                if existing.data:
                    # Update existing
                    result = supabase.table('question_responses').update(response_data).eq('id', existing.data[0]['id']).execute()
                else:
                    # Insert new
                    response_data['id'] = str(uuid.uuid4())
                    result = supabase.table('question_responses').insert(response_data).execute()

                if result.data:
                    saved.append(result.data[0])

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'message': f'Saved {len(saved)} responses',
                'responses': saved
            }).encode())

        except Exception as e:
            print(f"Error saving responses: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Failed to save responses: {str(e)}'}).encode())
        return
