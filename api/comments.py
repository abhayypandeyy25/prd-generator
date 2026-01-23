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


def parse_path(path):
    """Parse path to determine operation
    /api/comments/{prd_id} -> ('list', prd_id, None)
    /api/comments/{prd_id}/add -> ('add', prd_id, None)
    /api/comments/resolve/{comment_id} -> ('resolve', comment_id, None)
    /api/comments/delete/{comment_id} -> ('delete', comment_id, None)
    /api/comments/reply/{comment_id} -> ('reply', comment_id, None)
    """
    parts = path.strip('/').split('/')

    if len(parts) >= 3:
        if parts[2] == 'resolve' and len(parts) >= 4:
            return ('resolve', parts[3], None)
        elif parts[2] == 'delete' and len(parts) >= 4:
            return ('delete', parts[3], None)
        elif parts[2] == 'reply' and len(parts) >= 4:
            return ('reply', parts[3], None)
        elif len(parts) >= 4 and parts[3] == 'add':
            return ('add', parts[2], None)
        else:
            return ('list', parts[2], None)

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

            if op == 'list':
                prd_id = identifier

                if not validate_uuid(prd_id):
                    self.send_json(400, {'error': 'Invalid PRD ID'})
                    return

                # Get all comments for PRD
                result = supabase.table('prd_comments').select('*').eq(
                    'prd_id', prd_id
                ).order('created_at').execute()

                comments = result.data if result.data else []

                # Organize into threads (top-level and replies)
                top_level = []
                replies = {}

                for comment in comments:
                    if comment.get('parent_comment_id'):
                        parent_id = comment['parent_comment_id']
                        if parent_id not in replies:
                            replies[parent_id] = []
                        replies[parent_id].append(comment)
                    else:
                        top_level.append(comment)

                # Attach replies to parent comments
                for comment in top_level:
                    comment['replies'] = replies.get(comment['id'], [])

                self.send_json(200, {
                    'comments': top_level,
                    'total_count': len(comments)
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

            if op == 'add':
                prd_id = identifier

                if not validate_uuid(prd_id):
                    self.send_json(400, {'error': 'Invalid PRD ID'})
                    return

                # Verify PRD exists
                prd_result = supabase.table('generated_prds').select('id').eq('id', prd_id).execute()
                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                author_name = body.get('author_name', '').strip()
                comment_text = body.get('comment_text', '').strip()

                if not author_name:
                    self.send_json(400, {'error': 'Author name is required'})
                    return

                if not comment_text:
                    self.send_json(400, {'error': 'Comment text is required'})
                    return

                comment_id = str(uuid.uuid4())

                comment_data = {
                    'id': comment_id,
                    'prd_id': prd_id,
                    'author_name': author_name,
                    'author_email': body.get('author_email', '').strip() or None,
                    'section_id': body.get('section_id'),
                    'text_selection': body.get('text_selection'),
                    'comment_text': comment_text,
                    'parent_comment_id': body.get('parent_comment_id')
                }

                result = supabase.table('prd_comments').insert(comment_data).execute()

                # Log activity
                log_activity(supabase, prd_id, 'commented',
                           actor_name=author_name,
                           actor_email=body.get('author_email'),
                           metadata={'comment_id': comment_id, 'section_id': body.get('section_id')})

                self.send_json(201, {
                    'success': True,
                    'comment': result.data[0] if result.data else comment_data
                })
                return

            elif op == 'resolve':
                comment_id = identifier

                if not validate_uuid(comment_id):
                    self.send_json(400, {'error': 'Invalid comment ID'})
                    return

                # Update comment as resolved
                result = supabase.table('prd_comments').update({
                    'is_resolved': True
                }).eq('id', comment_id).execute()

                if not result.data:
                    self.send_json(404, {'error': 'Comment not found'})
                    return

                self.send_json(200, {
                    'success': True,
                    'comment': result.data[0]
                })
                return

            elif op == 'reply':
                parent_comment_id = identifier

                if not validate_uuid(parent_comment_id):
                    self.send_json(400, {'error': 'Invalid comment ID'})
                    return

                # Get parent comment
                parent_result = supabase.table('prd_comments').select('*').eq(
                    'id', parent_comment_id
                ).execute()

                if not parent_result.data:
                    self.send_json(404, {'error': 'Parent comment not found'})
                    return

                parent = parent_result.data[0]

                author_name = body.get('author_name', '').strip()
                comment_text = body.get('comment_text', '').strip()

                if not author_name or not comment_text:
                    self.send_json(400, {'error': 'Author name and comment text are required'})
                    return

                reply_id = str(uuid.uuid4())

                reply_data = {
                    'id': reply_id,
                    'prd_id': parent['prd_id'],
                    'author_name': author_name,
                    'author_email': body.get('author_email', '').strip() or None,
                    'section_id': parent.get('section_id'),
                    'comment_text': comment_text,
                    'parent_comment_id': parent_comment_id
                }

                result = supabase.table('prd_comments').insert(reply_data).execute()

                # Log activity
                log_activity(supabase, parent['prd_id'], 'commented',
                           actor_name=author_name,
                           metadata={'comment_id': reply_id, 'is_reply': True})

                self.send_json(201, {
                    'success': True,
                    'comment': result.data[0] if result.data else reply_data
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

            if op != 'delete':
                self.send_json(400, {'error': 'Invalid request path'})
                return

            comment_id = identifier
            if not validate_uuid(comment_id):
                self.send_json(400, {'error': 'Invalid comment ID'})
                return

            supabase = get_supabase()

            # Delete the comment (will cascade to replies)
            supabase.table('prd_comments').delete().eq('id', comment_id).execute()

            self.send_json(200, {
                'success': True,
                'message': 'Comment deleted'
            })
            return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
