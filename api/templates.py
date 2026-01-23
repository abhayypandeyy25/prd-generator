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
    """Parse path to determine operation and extract IDs
    /api/templates -> ('list', None)
    /api/templates/{template_id} -> ('get', template_id)
    /api/templates/{template_id}/clone -> ('clone', template_id)
    /api/templates/{template_id}/sections -> ('sections', template_id)
    """
    parts = path.strip('/').split('/')

    if len(parts) == 2:  # /api/templates
        return ('list', None)
    elif len(parts) == 3:  # /api/templates/{id}
        return ('get', parts[2])
    elif len(parts) == 4:  # /api/templates/{id}/clone or /api/templates/{id}/sections
        if parts[3] == 'clone':
            return ('clone', parts[2])
        elif parts[3] == 'sections':
            return ('sections', parts[2])

    return (None, None)


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
            op, template_id = parse_path(self.path)
            supabase = get_supabase()

            if op == 'list':
                # List all templates with section counts
                result = supabase.table('prd_templates').select(
                    'id, name, description, is_default, is_public, created_at'
                ).eq('is_public', True).order('is_default', desc=True).order('name').execute()

                templates = result.data if result.data else []

                # Get section counts for each template
                for template in templates:
                    sections_result = supabase.table('template_sections').select(
                        'id', count='exact'
                    ).eq('template_id', template['id']).execute()
                    template['section_count'] = sections_result.count if sections_result.count else 0

                self.send_json(200, templates)
                return

            elif op == 'get':
                if not template_id or not validate_uuid(template_id):
                    self.send_json(400, {'error': 'Invalid template ID'})
                    return

                # Get template details
                result = supabase.table('prd_templates').select('*').eq('id', template_id).execute()

                if not result.data:
                    self.send_json(404, {'error': 'Template not found'})
                    return

                template = result.data[0]

                # Get sections
                sections_result = supabase.table('template_sections').select('*').eq(
                    'template_id', template_id
                ).order('section_order').execute()
                template['sections'] = sections_result.data if sections_result.data else []

                # Get custom questions
                questions_result = supabase.table('custom_questions').select('*').eq(
                    'template_id', template_id
                ).order('display_order').execute()
                template['custom_questions'] = questions_result.data if questions_result.data else []

                self.send_json(200, template)
                return

            elif op == 'sections':
                if not template_id or not validate_uuid(template_id):
                    self.send_json(400, {'error': 'Invalid template ID'})
                    return

                # Get just the sections for a template
                sections_result = supabase.table('template_sections').select('*').eq(
                    'template_id', template_id
                ).order('section_order').execute()

                self.send_json(200, sections_result.data if sections_result.data else [])
                return

            else:
                self.send_json(400, {'error': 'Invalid request path'})
                return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, template_id = parse_path(self.path)
            supabase = get_supabase()

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

            if op == 'list':
                # Create new template
                name = body.get('name', '').strip()
                description = body.get('description', '').strip()
                sections = body.get('sections', [])

                if not name:
                    self.send_json(400, {'error': 'Template name is required'})
                    return

                # Create template
                new_id = str(uuid.uuid4())
                template_result = supabase.table('prd_templates').insert({
                    'id': new_id,
                    'name': name,
                    'description': description,
                    'is_default': False,
                    'is_public': True  # User templates are public by default
                }).execute()

                if not template_result.data:
                    self.send_json(500, {'error': 'Failed to create template'})
                    return

                # Add sections if provided
                if sections:
                    sections_to_insert = []
                    for i, section in enumerate(sections):
                        sections_to_insert.append({
                            'id': str(uuid.uuid4()),
                            'template_id': new_id,
                            'section_name': section.get('name', f'Section {i+1}'),
                            'section_order': section.get('order', i + 1),
                            'is_required': section.get('required', False),
                            'prompt_template': section.get('prompt_template', '')
                        })

                    supabase.table('template_sections').insert(sections_to_insert).execute()

                self.send_json(201, {
                    'success': True,
                    'template_id': new_id,
                    'message': 'Template created successfully'
                })
                return

            elif op == 'clone':
                if not template_id or not validate_uuid(template_id):
                    self.send_json(400, {'error': 'Invalid template ID'})
                    return

                new_name = body.get('name', '').strip()

                # Get original template
                result = supabase.table('prd_templates').select('*').eq('id', template_id).execute()
                if not result.data:
                    self.send_json(404, {'error': 'Template not found'})
                    return

                original = result.data[0]

                # Create new template
                new_id = str(uuid.uuid4())
                clone_name = new_name if new_name else f"Copy of {original['name']}"

                supabase.table('prd_templates').insert({
                    'id': new_id,
                    'name': clone_name,
                    'description': original.get('description', ''),
                    'is_default': False,
                    'is_public': True
                }).execute()

                # Clone sections
                sections_result = supabase.table('template_sections').select('*').eq(
                    'template_id', template_id
                ).execute()

                if sections_result.data:
                    sections_to_insert = []
                    for section in sections_result.data:
                        sections_to_insert.append({
                            'id': str(uuid.uuid4()),
                            'template_id': new_id,
                            'section_name': section['section_name'],
                            'section_order': section['section_order'],
                            'is_required': section['is_required'],
                            'prompt_template': section.get('prompt_template', '')
                        })
                    supabase.table('template_sections').insert(sections_to_insert).execute()

                # Clone custom questions
                questions_result = supabase.table('custom_questions').select('*').eq(
                    'template_id', template_id
                ).execute()

                if questions_result.data:
                    questions_to_insert = []
                    for q in questions_result.data:
                        questions_to_insert.append({
                            'id': str(uuid.uuid4()),
                            'template_id': new_id,
                            'section_id': q.get('section_id'),
                            'question_id': q.get('question_id'),
                            'question_text': q['question_text'],
                            'hint': q.get('hint'),
                            'question_type': q.get('question_type', 'text'),
                            'is_required': q.get('is_required', False),
                            'display_order': q.get('display_order')
                        })
                    supabase.table('custom_questions').insert(questions_to_insert).execute()

                self.send_json(201, {
                    'success': True,
                    'template_id': new_id,
                    'message': f'Template cloned as "{clone_name}"'
                })
                return

            else:
                self.send_json(400, {'error': 'Invalid request path'})
                return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_PUT(self):
        try:
            op, template_id = parse_path(self.path)

            if op != 'get' or not template_id:
                self.send_json(400, {'error': 'Invalid request path'})
                return

            if not validate_uuid(template_id):
                self.send_json(400, {'error': 'Invalid template ID'})
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

            supabase = get_supabase()

            # Check if template exists
            result = supabase.table('prd_templates').select('id, is_default').eq('id', template_id).execute()
            if not result.data:
                self.send_json(404, {'error': 'Template not found'})
                return

            # Don't allow editing default templates
            if result.data[0].get('is_default'):
                self.send_json(403, {'error': 'Cannot edit default templates. Clone it first.'})
                return

            # Update template
            update_data = {}
            if 'name' in body:
                update_data['name'] = body['name'].strip()
            if 'description' in body:
                update_data['description'] = body['description'].strip()

            if update_data:
                supabase.table('prd_templates').update(update_data).eq('id', template_id).execute()

            # Update sections if provided
            if 'sections' in body:
                # Delete existing sections
                supabase.table('template_sections').delete().eq('template_id', template_id).execute()

                # Insert new sections
                sections_to_insert = []
                for i, section in enumerate(body['sections']):
                    sections_to_insert.append({
                        'id': str(uuid.uuid4()),
                        'template_id': template_id,
                        'section_name': section.get('name', f'Section {i+1}'),
                        'section_order': section.get('order', i + 1),
                        'is_required': section.get('required', False),
                        'prompt_template': section.get('prompt_template', '')
                    })

                if sections_to_insert:
                    supabase.table('template_sections').insert(sections_to_insert).execute()

            self.send_json(200, {
                'success': True,
                'message': 'Template updated successfully'
            })
            return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_DELETE(self):
        try:
            op, template_id = parse_path(self.path)

            if op != 'get' or not template_id:
                self.send_json(400, {'error': 'Invalid request path'})
                return

            if not validate_uuid(template_id):
                self.send_json(400, {'error': 'Invalid template ID'})
                return

            supabase = get_supabase()

            # Check if template exists and is not default
            result = supabase.table('prd_templates').select('id, is_default').eq('id', template_id).execute()
            if not result.data:
                self.send_json(404, {'error': 'Template not found'})
                return

            if result.data[0].get('is_default'):
                self.send_json(403, {'error': 'Cannot delete default templates'})
                return

            # Delete template (cascades to sections and questions)
            supabase.table('prd_templates').delete().eq('id', template_id).execute()

            self.send_json(200, {
                'success': True,
                'message': 'Template deleted successfully'
            })
            return

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
