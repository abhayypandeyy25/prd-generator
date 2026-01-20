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
    if len(parts) >= 5:
        return parts[4]
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
        """Export PRD as Markdown file"""
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

            # Get PRD
            prd_result = supabase.table('prds').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(1).execute()

            if not prd_result.data:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No PRD found. Please generate one first.'}).encode())
                return

            prd = prd_result.data[0]
            content = prd.get('content_md', '')

            if not content:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'PRD content is empty'}).encode())
                return

            # Get project name for filename
            project_result = supabase.table('projects').select('name').eq('id', project_id).execute()
            project_name = project_result.data[0].get('name', 'PRD') if project_result.data else 'PRD'
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()

            md_bytes = content.encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'text/markdown')
            self.send_header('Content-Disposition', f'attachment; filename=PRD_{safe_name}.md')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(md_bytes)))
            self.end_headers()
            self.wfile.write(md_bytes)

        except Exception as e:
            print(f"Error exporting markdown: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Export failed: {str(e)}'}).encode())
        return
