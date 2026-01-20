from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
import io
import re
from supabase import create_client

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    Document = None


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


def markdown_to_docx(markdown_text, title="Product Requirements Document"):
    """Convert markdown to Word document"""
    if Document is None:
        raise Exception("python-docx library not available")

    doc = Document()

    # Add title
    title_para = doc.add_heading(title, 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Process markdown content
    lines = markdown_text.split('\n')
    current_list = None

    for line in lines:
        line = line.rstrip()

        # Skip empty lines but add paragraph break
        if not line:
            if current_list:
                current_list = None
            continue

        # Headers
        if line.startswith('### '):
            doc.add_heading(line[4:], level=3)
            current_list = None
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
            current_list = None
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
            current_list = None
        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            # Remove markdown formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            doc.add_paragraph(text, style='List Bullet')
        # Numbered lists
        elif re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line)
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            doc.add_paragraph(text, style='List Number')
        # Regular paragraph
        else:
            # Remove markdown formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'`(.+?)`', r'\1', text)

            if text.strip():
                doc.add_paragraph(text)

    # Save to bytes
    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)
    return docx_buffer.getvalue()


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
        """Export PRD as Word document"""
        try:
            project_id = get_project_id(self.path)

            if not project_id or not validate_uuid(project_id):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid project ID format'}).encode())
                return

            if Document is None:
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Word document export not available'}).encode())
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

            # Get project name for title and filename
            project_result = supabase.table('projects').select('name').eq('id', project_id).execute()
            project_name = project_result.data[0].get('name', 'Product') if project_result.data else 'Product'
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
            title = f"PRD - {project_name}"

            try:
                docx_bytes = markdown_to_docx(content, title)
            except Exception as e:
                print(f"Error generating DOCX: {e}")
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Failed to generate Word document: {str(e)}'}).encode())
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            self.send_header('Content-Disposition', f'attachment; filename=PRD_{safe_name}.docx')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(docx_bytes)))
            self.end_headers()
            self.wfile.write(docx_bytes)

        except Exception as e:
            print(f"Error exporting DOCX: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Export failed: {str(e)}'}).encode())
        return
