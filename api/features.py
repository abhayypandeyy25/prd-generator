from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from supabase import create_client

try:
    import anthropic
except ImportError:
    anthropic = None


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
    """Parse path to determine operation and extract IDs"""
    parts = path.strip('/').split('/')
    if len(parts) >= 3:
        if parts[2] == 'extract' and len(parts) >= 4:
            return ('extract', parts[3], None)
        elif parts[2] == 'item' and len(parts) >= 4:
            return ('item', None, parts[3])
        elif parts[2] == 'select' and len(parts) >= 4:
            return ('select', None, parts[3])
        else:
            return ('list', parts[2], None)
    return (None, None, None)


def extract_features_with_claude(context_text):
    """Use Claude to extract features from context"""
    if anthropic is None:
        raise Exception("Anthropic library not available")

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("Anthropic API key not configured")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Analyze the following product context and extract a list of potential features for the product.

CONTEXT:
{context_text[:30000]}

For each feature, provide:
1. A concise name (3-7 words)
2. A brief description (1-2 sentences explaining the feature's purpose and value)

Focus on:
- Core functionality mentioned in the context
- User needs implied by the documents
- Technical capabilities discussed
- Integration requirements
- User experience improvements

Extract 5-15 features based on the richness of the context.

Respond in JSON format with an array of objects:
[
  {{"name": "Feature Name", "description": "Brief description of what this feature does and why it matters"}},
  ...
]

Respond ONLY with the JSON array, no additional text."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    try:
        if response_text.startswith('['):
            return json.loads(response_text)
        elif '[' in response_text:
            start = response_text.index('[')
            end = response_text.rindex(']') + 1
            return json.loads(response_text[start:end])
    except json.JSONDecodeError:
        pass

    return []


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
            op, project_id, feature_id = parse_path(self.path)
            supabase = get_supabase()

            if op == 'list' and project_id:
                if not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID format'})
                    return
                result = supabase.table('features').select('*').eq('project_id', project_id).order('display_order').order('created_at').execute()
                self.send_json(200, result.data if result.data else [])

            elif op == 'item' and feature_id:
                if not validate_uuid(feature_id):
                    self.send_json(400, {'error': 'Invalid feature ID format'})
                    return
                result = supabase.table('features').select('*').eq('id', feature_id).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Feature not found'})

            else:
                self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, project_id, feature_id = parse_path(self.path)
            supabase = get_supabase()

            if op == 'extract' and project_id:
                if not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID format'})
                    return

                # Get aggregated context
                context_result = supabase.table('context_files').select('extracted_text').eq('project_id', project_id).execute()
                context_texts = [f.get('extracted_text', '') for f in (context_result.data or []) if f.get('extracted_text')]
                context = '\n\n---\n\n'.join(context_texts)

                if not context.strip():
                    self.send_json(400, {'error': 'No context available. Please upload context files first.'})
                    return

                # Extract features with AI
                try:
                    extracted_features = extract_features_with_claude(context)
                except Exception as e:
                    self.send_json(503, {'error': 'AI service temporarily unavailable', 'details': str(e)})
                    return

                if not extracted_features:
                    self.send_json(422, {'error': 'AI could not extract features from the context'})
                    return

                # Save features to database
                saved_features = []
                for i, feature in enumerate(extracted_features):
                    feature_id = str(uuid.uuid4())
                    feature_data = {
                        'id': feature_id,
                        'project_id': project_id,
                        'name': feature.get('name', 'Unnamed Feature'),
                        'description': feature.get('description', ''),
                        'is_selected': True,
                        'is_ai_generated': True,
                        'display_order': i
                    }
                    result = supabase.table('features').insert(feature_data).execute()
                    if result.data:
                        saved_features.append(result.data[0])

                self.send_json(200, {
                    'message': f'Extracted {len(saved_features)} features',
                    'features': saved_features,
                    'count': len(saved_features)
                })

            elif op == 'list' and project_id:
                # Create a new feature manually
                if not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID format'})
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body) if body else {}

                name = data.get('name', '').strip()
                if not name:
                    self.send_json(400, {'error': 'Feature name is required'})
                    return

                feature_id = str(uuid.uuid4())
                feature_data = {
                    'id': feature_id,
                    'project_id': project_id,
                    'name': name,
                    'description': data.get('description', ''),
                    'is_selected': True,
                    'is_ai_generated': False,
                    'display_order': data.get('display_order', 999)
                }

                result = supabase.table('features').insert(feature_data).execute()
                if result.data:
                    self.send_json(201, result.data[0])
                else:
                    self.send_json(500, {'error': 'Failed to create feature'})

            else:
                self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_PUT(self):
        try:
            op, project_id, feature_id = parse_path(self.path)
            supabase = get_supabase()

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            if op == 'item' and feature_id:
                if not validate_uuid(feature_id):
                    self.send_json(400, {'error': 'Invalid feature ID format'})
                    return

                # Update feature (name, description)
                update_data = {}
                if 'name' in data:
                    update_data['name'] = data['name']
                if 'description' in data:
                    update_data['description'] = data['description']
                if 'display_order' in data:
                    update_data['display_order'] = data['display_order']

                if not update_data:
                    self.send_json(400, {'error': 'No update data provided'})
                    return

                result = supabase.table('features').update(update_data).eq('id', feature_id).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Feature not found'})

            elif op == 'select' and feature_id:
                if not validate_uuid(feature_id):
                    self.send_json(400, {'error': 'Invalid feature ID format'})
                    return

                # Toggle or set selection status
                is_selected = data.get('is_selected')
                if is_selected is None:
                    # Toggle current value
                    existing = supabase.table('features').select('is_selected').eq('id', feature_id).execute()
                    if not existing.data:
                        self.send_json(404, {'error': 'Feature not found'})
                        return
                    is_selected = not existing.data[0]['is_selected']

                result = supabase.table('features').update({'is_selected': is_selected}).eq('id', feature_id).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Feature not found'})

            else:
                self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_DELETE(self):
        try:
            op, project_id, feature_id = parse_path(self.path)
            supabase = get_supabase()

            if op == 'item' and feature_id:
                if not validate_uuid(feature_id):
                    self.send_json(400, {'error': 'Invalid feature ID format'})
                    return

                result = supabase.table('features').delete().eq('id', feature_id).execute()
                self.send_json(200, {'message': 'Feature deleted'})

            else:
                self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
