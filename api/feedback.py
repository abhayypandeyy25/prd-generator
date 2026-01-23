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
        'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
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
    /api/feedback/rate/{project_id} -> ('rate', project_id, None)
    /api/feedback/question/{project_id}/{question_id} -> ('question', project_id, question_id)
    /api/feedback/improve/{project_id} -> ('improve', project_id, None)
    /api/feedback/stats/{project_id} -> ('stats', project_id, None)
    /api/feedback/suggestions/{project_id} -> ('suggestions', project_id, None)
    """
    parts = path.strip('/').split('/')

    if len(parts) >= 4:
        op = parts[2]
        project_id = parts[3]
        extra_id = parts[4] if len(parts) >= 5 else None
        return (op, project_id, extra_id)

    return (None, None, None)


def analyze_feedback_patterns(feedback_data):
    """Analyze feedback to identify patterns and improvement areas"""
    patterns = {
        'low_rated_sections': [],
        'common_issues': {},
        'improvement_areas': []
    }

    for feedback in feedback_data:
        # Track low-rated items
        if feedback.get('rating', 5) <= 2:
            section = feedback.get('section_name')
            if section and section not in patterns['low_rated_sections']:
                patterns['low_rated_sections'].append(section)

        # Track common issues from feedback text
        feedback_text = (feedback.get('feedback_text') or '').lower()
        issue_keywords = {
            'unclear': 'Clarity issues',
            'vague': 'Vague content',
            'missing': 'Missing information',
            'wrong': 'Incorrect information',
            'incomplete': 'Incomplete coverage',
            'too long': 'Too verbose',
            'too short': 'Needs more detail',
            'generic': 'Too generic'
        }

        for keyword, issue_type in issue_keywords.items():
            if keyword in feedback_text:
                patterns['common_issues'][issue_type] = patterns['common_issues'].get(issue_type, 0) + 1

    # Sort common issues by frequency
    patterns['common_issues'] = dict(
        sorted(patterns['common_issues'].items(), key=lambda x: x[1], reverse=True)
    )

    # Generate improvement areas
    if patterns['low_rated_sections']:
        patterns['improvement_areas'].append(f"Review and improve: {', '.join(patterns['low_rated_sections'][:3])}")
    if 'Clarity issues' in patterns['common_issues']:
        patterns['improvement_areas'].append("Focus on clearer, more specific language")
    if 'Missing information' in patterns['common_issues']:
        patterns['improvement_areas'].append("Ensure comprehensive coverage of all topics")
    if 'Too generic' in patterns['common_issues']:
        patterns['improvement_areas'].append("Add more specific, actionable details")

    return patterns


def generate_improvement_suggestions(prd_content, feedback_data, context=''):
    """Use AI to generate specific improvement suggestions"""
    if anthropic is None:
        return None

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    # Compile feedback summary
    feedback_summary = []
    for fb in feedback_data[:10]:  # Limit to recent 10
        if fb.get('feedback_text'):
            feedback_summary.append(f"- {fb.get('section_name', 'General')}: {fb['feedback_text']} (Rating: {fb.get('rating', 'N/A')}/5)")

    feedback_text = '\n'.join(feedback_summary) if feedback_summary else 'No specific feedback provided'

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Analyze this PRD and the user feedback to provide specific improvement suggestions.

PRD Content (first 8000 chars):
{prd_content[:8000]}

User Feedback:
{feedback_text}

Based on the feedback, provide a JSON response with:
1. "priority_improvements": List of 3-5 specific, actionable improvements ranked by priority
2. "section_recommendations": Object with section names as keys and specific recommendations as values
3. "rewrite_suggestions": List of 2-3 specific sentences/paragraphs that should be rewritten, with suggested rewrites
4. "missing_elements": List of any important elements missing from the PRD

Respond ONLY with valid JSON, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith('{'):
            return json.loads(response_text)
        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
    except (json.JSONDecodeError, Exception) as e:
        print(f"Improvement suggestion error: {e}")

    return None


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
            op, project_id, _ = parse_path(self.path)

            if not project_id or not validate_uuid(project_id):
                self.send_json(400, {'error': 'Invalid project ID'})
                return

            supabase = get_supabase()

            if op == 'stats':
                # Get feedback statistics for the project
                feedback_result = supabase.table('prd_feedback').select('*').eq('project_id', project_id).execute()
                feedback_data = feedback_result.data or []

                if not feedback_data:
                    self.send_json(200, {
                        'total_feedback': 0,
                        'average_rating': None,
                        'rating_distribution': {},
                        'patterns': {}
                    })
                    return

                # Calculate stats
                ratings = [f['rating'] for f in feedback_data if f.get('rating')]
                avg_rating = sum(ratings) / len(ratings) if ratings else None

                distribution = {}
                for r in ratings:
                    distribution[str(r)] = distribution.get(str(r), 0) + 1

                # Analyze patterns
                patterns = analyze_feedback_patterns(feedback_data)

                self.send_json(200, {
                    'total_feedback': len(feedback_data),
                    'average_rating': round(avg_rating, 2) if avg_rating else None,
                    'rating_distribution': distribution,
                    'patterns': patterns
                })
                return

            elif op == 'suggestions':
                # Get AI improvement suggestions
                prd_result = supabase.table('generated_prds').select('content_md').eq('project_id', project_id).execute()
                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                prd_content = prd_result.data[0].get('content_md', '')

                feedback_result = supabase.table('prd_feedback').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(10).execute()
                feedback_data = feedback_result.data or []

                suggestions = generate_improvement_suggestions(prd_content, feedback_data)

                if suggestions:
                    self.send_json(200, suggestions)
                else:
                    self.send_json(500, {'error': 'Failed to generate suggestions'})
                return

            self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, project_id, extra_id = parse_path(self.path)

            if not project_id or not validate_uuid(project_id):
                self.send_json(400, {'error': 'Invalid project ID'})
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

            supabase = get_supabase()

            if op == 'rate':
                # Submit overall PRD rating
                rating = body.get('rating')
                feedback_text = body.get('feedback_text', '').strip()
                section_name = body.get('section_name')

                if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
                    self.send_json(400, {'error': 'Rating must be an integer between 1 and 5'})
                    return

                feedback_id = str(uuid.uuid4())
                feedback_data = {
                    'id': feedback_id,
                    'project_id': project_id,
                    'feedback_type': 'prd_rating',
                    'rating': rating,
                    'feedback_text': feedback_text or None,
                    'section_name': section_name
                }

                result = supabase.table('prd_feedback').insert(feedback_data).execute()

                if result.data:
                    self.send_json(201, {
                        'success': True,
                        'feedback_id': feedback_id,
                        'message': 'Thank you for your feedback!'
                    })
                else:
                    self.send_json(500, {'error': 'Failed to save feedback'})
                return

            elif op == 'question':
                # Submit feedback on a specific question response
                question_id = extra_id
                if not question_id:
                    self.send_json(400, {'error': 'Question ID required'})
                    return

                rating = body.get('rating')
                feedback_text = body.get('feedback_text', '').strip()
                was_helpful = body.get('was_helpful')
                suggested_improvement = body.get('suggested_improvement', '').strip()

                feedback_id = str(uuid.uuid4())
                feedback_data = {
                    'id': feedback_id,
                    'project_id': project_id,
                    'feedback_type': 'question_response',
                    'question_id': question_id,
                    'rating': rating,
                    'feedback_text': feedback_text or None,
                    'metadata': json.dumps({
                        'was_helpful': was_helpful,
                        'suggested_improvement': suggested_improvement
                    }) if was_helpful is not None or suggested_improvement else None
                }

                result = supabase.table('prd_feedback').insert(feedback_data).execute()

                if result.data:
                    self.send_json(201, {
                        'success': True,
                        'feedback_id': feedback_id
                    })
                else:
                    self.send_json(500, {'error': 'Failed to save feedback'})
                return

            elif op == 'improve':
                # Apply AI improvements to PRD based on feedback
                prd_result = supabase.table('generated_prds').select('*').eq('project_id', project_id).execute()
                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                prd_content = prd_result.data[0].get('content_md', '')
                prd_id = prd_result.data[0].get('id')

                feedback_result = supabase.table('prd_feedback').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(10).execute()
                feedback_data = feedback_result.data or []

                if not feedback_data:
                    self.send_json(400, {'error': 'No feedback available to improve from'})
                    return

                # Use AI to improve the PRD
                if anthropic is None:
                    self.send_json(503, {'error': 'AI service not available'})
                    return

                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not api_key:
                    self.send_json(503, {'error': 'AI service not configured'})
                    return

                # Compile feedback
                feedback_summary = []
                for fb in feedback_data:
                    if fb.get('feedback_text'):
                        feedback_summary.append(f"- {fb.get('section_name', 'General')}: {fb['feedback_text']}")

                if not feedback_summary:
                    self.send_json(400, {'error': 'No actionable feedback text provided'})
                    return

                try:
                    client = anthropic.Anthropic(api_key=api_key)

                    prompt = f"""Improve this PRD based on the user feedback provided.

Current PRD:
{prd_content}

User Feedback:
{chr(10).join(feedback_summary)}

Instructions:
1. Address each piece of feedback
2. Maintain the overall structure and formatting
3. Make the content clearer and more actionable
4. Keep the improved PRD comprehensive but concise

Return the improved PRD in markdown format. Return ONLY the improved PRD content, no explanations."""

                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=8000,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    improved_content = message.content[0].text.strip()

                    # Save as new version
                    supabase.table('generated_prds').update({
                        'content_md': improved_content,
                        'version': prd_result.data[0].get('version', 1) + 1
                    }).eq('id', prd_id).execute()

                    # Create snapshot of previous version
                    snapshot_id = str(uuid.uuid4())
                    supabase.table('prd_edit_snapshots').insert({
                        'id': snapshot_id,
                        'prd_id': prd_id,
                        'content_md': prd_content,
                        'version_name': f"Before AI improvement v{prd_result.data[0].get('version', 1)}",
                        'change_summary': 'Auto-saved before AI improvement'
                    }).execute()

                    self.send_json(200, {
                        'success': True,
                        'message': 'PRD improved based on feedback',
                        'previous_version_id': snapshot_id
                    })

                except Exception as e:
                    self.send_json(500, {'error': f'Failed to improve PRD: {str(e)}'})
                return

            self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
