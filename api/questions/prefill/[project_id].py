from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from supabase import create_client

try:
    import anthropic
except ImportError:
    anthropic = None


def load_questions():
    """Load questions from JSON file"""
    questions_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'questions.json')
    try:
        with open(questions_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading questions: {e}")
        return {"sections": []}


def get_supabase():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured")
    return create_client(url, key)


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
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


def get_flat_questions(questions_data):
    """Flatten questions for AI processing"""
    flat_questions = []
    for section in questions_data.get('sections', []):
        for subsection in section.get('subsections', []):
            for q in subsection.get('questions', []):
                flat_questions.append({
                    'id': q['id'],
                    'question': q.get('question', ''),
                    'type': q.get('type', 'text'),
                    'hint': q.get('hint', '')
                })
    return flat_questions


def analyze_context_for_questions(context, questions):
    """Use Claude to analyze context and suggest answers"""
    if anthropic is None:
        raise Exception("Anthropic library not available")

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("Anthropic API key not configured")

    client = anthropic.Anthropic(api_key=api_key)

    # Limit questions text to avoid exceeding context limits
    questions_text = "\n".join([f"{q['id']}: {q['question']}" for q in questions[:50]])

    prompt = f"""You are a product management assistant. Based on the following context, suggest answers to these product questions.

CONTEXT:
{context[:30000]}

QUESTIONS:
{questions_text}

For each question, provide a suggested answer based ONLY on information found in the context. If the context doesn't contain relevant information for a question, provide an empty string.

Respond in JSON format with an array of objects, each containing:
- question_id: the question ID
- suggested_answer: your suggested answer (empty string if no relevant info)
- confidence: "high", "medium", or "low"
- source_hint: brief note about where in the context you found the information

Example response:
[
  {{"question_id": "1.1.1", "suggested_answer": "The core problem is...", "confidence": "high", "source_hint": "Found in meeting notes section"}},
  {{"question_id": "1.1.2", "suggested_answer": "", "confidence": "low", "source_hint": ""}}
]

Respond ONLY with the JSON array, no additional text."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Try to parse JSON with proper error handling
        try:
            if response_text.startswith('['):
                return json.loads(response_text)
            elif '[' in response_text:
                start = response_text.index('[')
                end = response_text.rindex(']') + 1
                return json.loads(response_text[start:end])
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {json_err}")
            print(f"Response text: {response_text[:500]}")
            return []

        return []
    except Exception as e:
        print(f"Claude API error: {e}")
        raise


class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        for key, value in cors_headers().items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        return

    def do_POST(self):
        """Use AI to prefill question answers based on context"""
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

            # Check if project exists
            project_result = supabase.table('projects').select('*').eq('id', project_id).execute()
            if not project_result.data:
                self.send_response(404)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                return

            # Get aggregated context
            context_result = supabase.table('context_files').select('extracted_text').eq('project_id', project_id).execute()

            context_texts = [f.get('extracted_text', '') for f in (context_result.data or []) if f.get('extracted_text')]
            context = '\n\n---\n\n'.join(context_texts)

            if not context or len(context.strip()) == 0:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No context available. Please upload context files first.',
                    'hint': 'Upload documents, emails, or notes in the Context tab before using AI prefill.'
                }).encode())
                return

            # Load and flatten questions
            questions_data = load_questions()
            flat_questions = get_flat_questions(questions_data)
            if not flat_questions:
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No questions found to process'}).encode())
                return

            # Call Claude to analyze context
            try:
                ai_responses = analyze_context_for_questions(context, flat_questions)
            except Exception as e:
                print(f"Claude API error: {e}")
                self.send_response(503)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'AI service temporarily unavailable',
                    'details': str(e)
                }).encode())
                return

            if not ai_responses:
                self.send_response(422)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'AI could not generate responses',
                    'hint': 'The context might not contain enough relevant information.'
                }).encode())
                return

            # Save AI-suggested responses to database
            saved_responses = []
            save_errors = []

            for ai_resp in ai_responses:
                try:
                    question_id = ai_resp.get('question_id')
                    suggested_answer = ai_resp.get('suggested_answer', '')

                    if not question_id or not suggested_answer:
                        continue

                    # Check if response exists
                    existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', question_id).execute()

                    response_data = {
                        'project_id': project_id,
                        'question_id': question_id,
                        'response': suggested_answer,
                        'ai_suggested': True,
                        'confirmed': False
                    }

                    if existing.data:
                        result = supabase.table('question_responses').update(response_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        response_data['id'] = str(uuid.uuid4())
                        result = supabase.table('question_responses').insert(response_data).execute()

                    if result.data:
                        saved_responses.append({
                            'question_id': question_id,
                            'response': suggested_answer,
                            'confidence': ai_resp.get('confidence', 'low'),
                            'source_hint': ai_resp.get('source_hint', '')
                        })

                except Exception as e:
                    save_errors.append({
                        'question_id': ai_resp.get('question_id'),
                        'error': str(e)
                    })

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'message': f'AI prefilled {len(saved_responses)} questions',
                'responses': saved_responses,
                'total_processed': len(ai_responses),
                'save_errors': save_errors if save_errors else None
            }).encode())

        except Exception as e:
            print(f"Error in prefill_questions: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Prefill failed: {str(e)}'}).encode())
        return
