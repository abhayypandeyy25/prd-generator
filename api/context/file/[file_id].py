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
        'Access-Control-Allow-Methods': 'GET, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


def get_file_id(path):
    """Extract file_id from path like /api/context/file/[file_id]"""
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

    def do_DELETE(self):
        """Delete a specific context file"""
        try:
            file_id = get_file_id(self.path)

            # Validate file_id
            if not file_id or not validate_uuid(file_id):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid file ID format'}).encode())
                return

            supabase = get_supabase()

            # Get file info first to delete from storage
            file_result = supabase.table('context_files').select('*').eq('id', file_id).execute()

            if not file_result.data:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())
                return

            file_info = file_result.data[0]

            # Try to delete from storage if URL exists
            if file_info.get('file_url'):
                try:
                    # Extract path from URL for deletion
                    file_url = file_info['file_url']
                    # URL format: .../storage/v1/object/public/context-files/[path]
                    if 'context-files/' in file_url:
                        storage_path = file_url.split('context-files/')[-1]
                        supabase.storage.from_('context-files').remove([storage_path])
                except Exception as storage_error:
                    print(f"Storage deletion error (non-critical): {storage_error}")
                    # Continue even if storage deletion fails

            # Delete from database
            delete_result = supabase.table('context_files').delete().eq('id', file_id).execute()

            if delete_result.data is not None:
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'File deleted successfully'}).encode())
            else:
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to delete file'}).encode())

        except Exception as e:
            print(f"Error deleting context file: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Delete failed: {str(e)}'}).encode())
        return

    def do_GET(self):
        """Get a specific context file by ID"""
        try:
            file_id = get_file_id(self.path)

            # Validate file_id
            if not file_id or not validate_uuid(file_id):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid file ID format'}).encode())
                return

            supabase = get_supabase()
            result = supabase.table('context_files').select('*').eq('id', file_id).execute()

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
                self.wfile.write(json.dumps({'error': 'File not found'}).encode())

        except Exception as e:
            print(f"Error getting context file: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Failed to get file: {str(e)}'}).encode())
        return
