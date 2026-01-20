from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
import re
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
    if len(parts) >= 4:
        return parts[3]
    return None


def validate_uuid(uuid_str):
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def markdown_to_html(markdown_text):
    """Simple markdown to HTML conversion"""
    if not markdown_text:
        return ''

    html = markdown_text

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.MULTILINE)

    # Code blocks
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Paragraphs
    html = re.sub(r'\n\n', '</p><p>', html)
    html = f'<p>{html}</p>'

    # Clean up
    html = html.replace('<p></p>', '')
    html = html.replace('<p><h', '<h').replace('</h1></p>', '</h1>').replace('</h2></p>', '</h2>').replace('</h3></p>', '</h3>')

    return html


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
        """Get PRD as HTML for preview"""
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

            if not result.data:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No PRD found. Please generate one first.',
                    'markdown': '',
                    'html': ''
                }).encode())
                return

            prd = result.data[0]
            content = prd.get('content_md', '')

            try:
                html = markdown_to_html(content) if content else ''
            except Exception as e:
                print(f"Error converting to HTML: {e}")
                html = f'<p>Error converting to HTML: {str(e)}</p>'

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'markdown': content,
                'html': html,
                'created_at': prd.get('created_at'),
                'prd_id': prd.get('id')
            }).encode())

        except Exception as e:
            print(f"Error previewing PRD: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Preview failed: {str(e)}'}).encode())
        return
