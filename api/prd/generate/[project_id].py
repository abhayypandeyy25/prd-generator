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


PRD_TEMPLATE = """# Product Requirements Document

## Executive Summary
[Brief overview of the product and its purpose]

## Problem Statement
[Detailed description of the problem being solved]

## Target Users
[Description of primary and secondary users]

## Proposed Solution
[High-level description of the solution]

## Key Features
[List of main features]

## Success Metrics
[How success will be measured]

## Technical Requirements
[Technical considerations and requirements]

## Timeline and Milestones
[Key milestones and timeline]

## Risks and Mitigations
[Potential risks and how to address them]
"""


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


def get_question_map(questions_data):
    """Create a map of question IDs to question details"""
    question_map = {}
    for section in questions_data.get('sections', []):
        for subsection in section.get('subsections', []):
            for q in subsection.get('questions', []):
                question_map[q['id']] = {
                    'question': q.get('question', ''),
                    'section': section['title'],
                    'subsection': subsection['title']
                }
    return question_map


def generate_prd_with_claude(organized_responses, template):
    """Use Claude to generate PRD content"""
    if anthropic is None:
        raise Exception("Anthropic library not available")

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("Anthropic API key not configured")

    client = anthropic.Anthropic(api_key=api_key)

    # Format responses for the prompt
    responses_text = ""
    for section_name, responses in organized_responses.items():
        responses_text += f"\n## {section_name}\n"
        for resp in responses:
            if resp.get('response') and resp.get('response').strip():
                responses_text += f"Q: {resp['question']}\nA: {resp['response']}\n\n"

    prompt = f"""You are a professional product manager. Based on the following Q&A responses, generate a comprehensive Product Requirements Document (PRD).

RESPONSES:
{responses_text}

TEMPLATE STRUCTURE:
{template}

Generate a well-structured PRD that:
1. Synthesizes all the provided answers into coherent sections
2. Follows the template structure
3. Uses professional language appropriate for stakeholders
4. Includes specific details from the responses
5. Adds appropriate formatting (headers, bullet points, etc.)

Output the PRD in Markdown format."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text
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
        """Generate PRD from confirmed responses"""
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

            # Get all responses
            responses_result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
            responses = responses_result.data if responses_result.data else []

            if not responses:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No responses found. Please answer questions first.',
                    'hint': 'Go to the Questions tab and answer at least some questions before generating a PRD.'
                }).encode())
                return

            # Check for confirmed responses
            confirmed_responses = [r for r in responses if r.get('confirmed')]
            if not confirmed_responses:
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No confirmed responses found.',
                    'hint': 'Please confirm at least some answers in the Questions tab before generating a PRD.',
                    'total_responses': len(responses)
                }).encode())
                return

            # Load questions and organize responses by section
            questions_data = load_questions()
            question_map = get_question_map(questions_data)
            organized_responses = {}

            for resp in responses:
                q_id = resp.get('question_id')
                if q_id in question_map:
                    section_key = question_map[q_id]['section']
                    if section_key not in organized_responses:
                        organized_responses[section_key] = []
                    organized_responses[section_key].append({
                        'question_id': q_id,
                        'question': question_map[q_id]['question'],
                        'response': resp.get('response', ''),
                        'confirmed': resp.get('confirmed', False)
                    })

            # Generate PRD using Claude
            try:
                prd_content = generate_prd_with_claude(organized_responses, PRD_TEMPLATE)
            except Exception as e:
                print(f"Claude API error generating PRD: {e}")
                self.send_response(503)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'AI service temporarily unavailable',
                    'details': str(e)
                }).encode())
                return

            if not prd_content or prd_content.startswith('# Error'):
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Failed to generate PRD content',
                    'details': prd_content if prd_content else 'No content returned'
                }).encode())
                return

            # Save generated PRD
            prd_id = str(uuid.uuid4())
            try:
                prd_result = supabase.table('prds').insert({
                    'id': prd_id,
                    'project_id': project_id,
                    'content_md': prd_content
                }).execute()

                saved_prd = prd_result.data[0] if prd_result.data else None
            except Exception as e:
                print(f"Error saving PRD: {e}")
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'PRD generated but failed to save',
                    'content': prd_content,
                    'details': str(e)
                }).encode())
                return

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'message': 'PRD generated successfully',
                'prd_id': saved_prd['id'] if saved_prd else prd_id,
                'content': prd_content,
                'stats': {
                    'total_responses': len(responses),
                    'confirmed_responses': len(confirmed_responses),
                    'sections_covered': len(organized_responses)
                }
            }).encode())

        except Exception as e:
            print(f"Error in generate_prd: {e}")
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'PRD generation failed: {str(e)}'}).encode())
        return
