from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
import secrets
import hashlib
from urllib.parse import parse_qs, urlparse
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
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }


def validate_uuid(uuid_str):
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def generate_share_token():
    """Generate a secure, URL-safe share token"""
    return secrets.token_urlsafe(32)


def hash_password(password):
    """Hash password for storage"""
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verify password against hash"""
    if not password_hash:
        return True
    if not password:
        return False
    return hash_password(password) == password_hash


def parse_path(path):
    """Parse path to determine operation and extract IDs
    /api/share/create/{project_id} -> ('create', project_id, None)
    /api/share/{share_token} -> ('get', share_token, None)
    /api/share/revoke/{share_id} -> ('revoke', share_id, None)
    /api/share/list/{project_id} -> ('list', project_id, None)
    """
    parts = path.strip('/').split('/')

    if len(parts) >= 3:
        if parts[2] == 'create' and len(parts) >= 4:
            return ('create', parts[3], None)
        elif parts[2] == 'revoke' and len(parts) >= 4:
            return ('revoke', parts[3], None)
        elif parts[2] == 'list' and len(parts) >= 4:
            return ('list', parts[3], None)
        else:
            return ('get', parts[2], None)

    return (None, None, None)


def log_activity(supabase, prd_id, activity_type, actor_name=None, actor_email=None, metadata=None):
    """Log activity for a PRD"""
    try:
        supabase.table('prd_activity').insert({
            'id': str(uuid.uuid4()),
            'prd_id': prd_id,
            'activity_type': activity_type,
            'actor_name': actor_name,
            'actor_email': actor_email,
            'metadata': metadata or {}
        }).execute()
    except Exception as e:
        print(f"Failed to log activity: {e}")


class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        for key, value in cors_headers().items():
            self.send_header(key, value)

    def send_json(self, status, data):
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
        try:
            op, identifier, _ = parse_path(self.path)
            supabase = get_supabase()

            if op == 'get':
                # Access shared PRD
                share_token = identifier

                # Get share info
                result = supabase.table('prd_shares').select('*').eq('share_token', share_token).execute()

                if not result.data:
                    self.send_json(404, {'error': 'Share link not found or expired'})
                    return

                share = result.data[0]

                # Check expiration
                if share.get('expires_at'):
                    from datetime import datetime
                    expires = datetime.fromisoformat(share['expires_at'].replace('Z', '+00:00'))
                    if datetime.now(expires.tzinfo) > expires:
                        self.send_json(410, {'error': 'This share link has expired'})
                        return

                # Check password
                if share.get('password_hash'):
                    # Parse query params for password
                    parsed = urlparse(self.path)
                    query_params = parse_qs(parsed.query)
                    password = query_params.get('password', [None])[0]

                    if not verify_password(password, share['password_hash']):
                        self.send_json(401, {
                            'error': 'Password required',
                            'password_protected': True
                        })
                        return

                # Get PRD content
                prd_result = supabase.table('generated_prds').select('*').eq('id', share['prd_id']).execute()

                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                prd = prd_result.data[0]

                # Get project name
                project_result = supabase.table('projects').select('name').eq('id', prd['project_id']).execute()
                project_name = project_result.data[0]['name'] if project_result.data else 'Untitled Project'

                # Increment view count
                supabase.table('prd_shares').update({
                    'view_count': share['view_count'] + 1
                }).eq('id', share['id']).execute()

                # Log activity
                log_activity(supabase, share['prd_id'], 'viewed', metadata={'via': 'share_link'})

                # Get comments if access allows
                comments = []
                if share['access_type'] in ['comment', 'edit']:
                    comments_result = supabase.table('prd_comments').select('*').eq(
                        'prd_id', share['prd_id']
                    ).order('created_at').execute()
                    comments = comments_result.data if comments_result.data else []

                self.send_json(200, {
                    'prd': {
                        'id': prd['id'],
                        'project_id': prd['project_id'],
                        'project_name': project_name,
                        'content_md': prd.get('content_md', ''),
                        'status': prd.get('status', 'draft'),
                        'created_at': prd.get('created_at')
                    },
                    'access_type': share['access_type'],
                    'comments': comments
                })
                return

            elif op == 'list':
                # List all shares for a project
                project_id = identifier

                if not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                # Get PRD for project
                prd_result = supabase.table('generated_prds').select('id').eq(
                    'project_id', project_id
                ).order('created_at', desc=True).limit(1).execute()

                if not prd_result.data:
                    self.send_json(200, {'shares': []})
                    return

                prd_id = prd_result.data[0]['id']

                # Get all shares
                shares_result = supabase.table('prd_shares').select(
                    'id, share_token, access_type, expires_at, view_count, created_at'
                ).eq('prd_id', prd_id).order('created_at', desc=True).execute()

                self.send_json(200, {
                    'shares': shares_result.data if shares_result.data else []
                })
                return

            else:
                self.send_json(400, {'error': 'Invalid request path'})
                return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, identifier, _ = parse_path(self.path)
            supabase = get_supabase()

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

            if op == 'create':
                project_id = identifier

                if not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                # Get PRD for project
                prd_result = supabase.table('generated_prds').select('id').eq(
                    'project_id', project_id
                ).order('created_at', desc=True).limit(1).execute()

                if not prd_result.data:
                    self.send_json(404, {'error': 'No PRD found for this project'})
                    return

                prd_id = prd_result.data[0]['id']

                # Create share
                access_type = body.get('access_type', 'view')
                if access_type not in ['view', 'comment', 'edit']:
                    access_type = 'view'

                password = body.get('password')
                password_hash = hash_password(password) if password else None

                expires_in = body.get('expires_in')  # days
                expires_at = None
                if expires_in:
                    from datetime import datetime, timedelta
                    expires_at = (datetime.utcnow() + timedelta(days=int(expires_in))).isoformat()

                share_token = generate_share_token()
                share_id = str(uuid.uuid4())

                supabase.table('prd_shares').insert({
                    'id': share_id,
                    'prd_id': prd_id,
                    'share_token': share_token,
                    'access_type': access_type,
                    'password_hash': password_hash,
                    'expires_at': expires_at
                }).execute()

                # Log activity
                log_activity(supabase, prd_id, 'shared', metadata={
                    'access_type': access_type,
                    'expires_in_days': expires_in
                })

                self.send_json(201, {
                    'success': True,
                    'share_id': share_id,
                    'share_token': share_token,
                    'access_type': access_type,
                    'expires_at': expires_at,
                    'password_protected': password_hash is not None
                })
                return

            else:
                self.send_json(400, {'error': 'Invalid request path'})
                return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_DELETE(self):
        try:
            op, identifier, _ = parse_path(self.path)

            if op != 'revoke':
                self.send_json(400, {'error': 'Invalid request path'})
                return

            share_id = identifier
            if not validate_uuid(share_id):
                self.send_json(400, {'error': 'Invalid share ID'})
                return

            supabase = get_supabase()

            # Delete the share
            supabase.table('prd_shares').delete().eq('id', share_id).execute()

            self.send_json(200, {
                'success': True,
                'message': 'Share link revoked'
            })
            return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
