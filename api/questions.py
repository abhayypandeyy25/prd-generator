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
    questions_file = os.path.join(os.path.dirname(__file__), 'data', 'questions.json')
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
    """Parse path to determine operation and extract IDs"""
    parts = path.strip('/').split('/')
    if len(parts) == 2:
        return ('list', None, None)
    elif len(parts) >= 4:
        op = parts[2]
        project_id = parts[3]
        question_id = parts[4] if len(parts) >= 5 else None
        return (op, project_id, question_id)
    return (None, None, None)


# Adaptive questioning configuration
FOLLOW_UP_TRIGGERS = {
    'competitor': {
        'keywords': ['competitor', 'alternative', 'similar', 'market'],
        'follow_ups': [
            {'id': 'fu_competitor_1', 'question': 'How do you plan to differentiate from these competitors?', 'hint': 'Focus on unique value proposition'},
            {'id': 'fu_competitor_2', 'question': 'What specific features do competitors lack that you will provide?', 'hint': 'Identify gaps in the market'}
        ]
    },
    'timeline': {
        'keywords': ['deadline', 'launch', 'release', 'q1', 'q2', 'q3', 'q4', 'month', 'week'],
        'follow_ups': [
            {'id': 'fu_timeline_1', 'question': 'What are the key milestones before the launch date?', 'hint': 'Break down the timeline into phases'},
            {'id': 'fu_timeline_2', 'question': 'What dependencies might affect this timeline?', 'hint': 'Identify blockers and risks'}
        ]
    },
    'metric': {
        'keywords': ['metric', 'kpi', 'measure', 'success', 'goal', 'target', 'conversion', 'retention'],
        'follow_ups': [
            {'id': 'fu_metric_1', 'question': 'How will you measure progress towards these metrics?', 'hint': 'Define measurement methodology'},
            {'id': 'fu_metric_2', 'question': 'What is the current baseline for these metrics?', 'hint': 'Establish starting point for comparison'}
        ]
    },
    'user': {
        'keywords': ['user', 'customer', 'persona', 'audience', 'segment'],
        'follow_ups': [
            {'id': 'fu_user_1', 'question': 'What are the primary pain points for this user segment?', 'hint': 'Identify problems to solve'},
            {'id': 'fu_user_2', 'question': 'How do these users currently solve this problem?', 'hint': 'Understand existing behaviors'}
        ]
    },
    'integration': {
        'keywords': ['integrate', 'api', 'connect', 'third-party', 'external', 'system'],
        'follow_ups': [
            {'id': 'fu_integration_1', 'question': 'What authentication/authorization is needed for these integrations?', 'hint': 'Security requirements'},
            {'id': 'fu_integration_2', 'question': 'Are there rate limits or data volume considerations?', 'hint': 'Technical constraints'}
        ]
    }
}

# Skip logic rules
SKIP_LOGIC = {
    '2.1.1': {'skip_if_contains': ['n/a', 'none', 'no competitors'], 'skip_questions': ['2.1.2', '2.1.3']},
    '3.1.1': {'skip_if_contains': ['no integration', 'standalone', 'none required'], 'skip_questions': ['3.1.2', '3.1.3']},
    '4.1.1': {'skip_if_contains': ['no existing', 'greenfield', 'new system'], 'skip_questions': ['4.1.2']}
}


def get_follow_up_questions(question_id, response_text):
    """Generate follow-up questions based on the response content"""
    if not response_text:
        return []

    response_lower = response_text.lower()
    follow_ups = []

    for trigger_name, trigger_config in FOLLOW_UP_TRIGGERS.items():
        for keyword in trigger_config['keywords']:
            if keyword in response_lower:
                for fu in trigger_config['follow_ups']:
                    follow_up = {
                        **fu,
                        'parent_question_id': question_id,
                        'trigger': trigger_name,
                        'type': 'follow_up'
                    }
                    if follow_up not in follow_ups:
                        follow_ups.append(follow_up)
                break  # Only add once per trigger

    return follow_ups[:3]  # Limit to 3 follow-ups


def check_skip_logic(question_id, response_text):
    """Check if any questions should be skipped based on the response"""
    if not response_text or question_id not in SKIP_LOGIC:
        return []

    response_lower = response_text.lower()
    skip_config = SKIP_LOGIC[question_id]

    for skip_phrase in skip_config.get('skip_if_contains', []):
        if skip_phrase in response_lower:
            return skip_config.get('skip_questions', [])

    return []


def generate_ai_follow_ups(question_text, response_text, context=''):
    """Use AI to generate contextual follow-up questions"""
    if anthropic is None:
        return []

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return []

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Based on this product question and answer, suggest 2 follow-up questions that would help clarify or expand the response.

Original Question: {question_text}
Answer Given: {response_text}

Additional Context: {context[:2000] if context else 'None provided'}

Return a JSON array with follow-up questions:
[{{"id": "ai_fu_1", "question": "...", "hint": "...", "reasoning": "..."}}]

Only suggest questions if the answer is substantial and could benefit from clarification. If the answer is complete, return an empty array [].
Return ONLY the JSON array, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        if response_text.startswith('['):
            follow_ups = json.loads(response_text)
            for fu in follow_ups:
                fu['type'] = 'ai_generated'
            return follow_ups
    except (json.JSONDecodeError, Exception) as e:
        print(f"AI follow-up generation error: {e}")

    return []


def get_related_questions(question_id, questions_data, responses):
    """Find related questions based on section and topic"""
    related = []
    current_section = None
    current_subsection = None

    # Find current question's section
    for section in questions_data.get('sections', []):
        for subsection in section.get('subsections', []):
            for q in subsection.get('questions', []):
                if q['id'] == question_id:
                    current_section = section
                    current_subsection = subsection
                    break

    if not current_section:
        return []

    # Get unanswered questions from same subsection
    for q in current_subsection.get('questions', []):
        if q['id'] != question_id:
            # Check if not answered
            answered = any(r.get('question_id') == q['id'] and r.get('response') for r in responses)
            if not answered:
                related.append({
                    'id': q['id'],
                    'question': q.get('question', ''),
                    'hint': q.get('hint', ''),
                    'type': 'related',
                    'reason': f"Related question in {current_subsection.get('name', 'same section')}"
                })

    return related[:3]


def get_flat_questions(questions_data):
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


def analyze_context_for_questions_batch(context, questions, selected_features=None, client=None):
    """Process a single batch of questions."""
    questions_text = "\n".join([f"{q['id']}: {q['question']}" for q in questions])

    features_context = ""
    if selected_features and len(selected_features) > 0:
        features_list = []
        for f in selected_features[:15]:
            features_list.append(f"- {f.get('name', 'Unnamed')}: {f.get('description', '')[:100]}")
        features_context = "\n\nSELECTED FEATURES:\n" + "\n".join(features_list)

    max_context_length = 12000
    truncated_context = context[:max_context_length]

    prompt = f"""Based on the product context and features below, answer these product questions concisely.

CONTEXT:
{truncated_context}
{features_context}

QUESTIONS:
{questions_text}

For each question, provide a brief answer based on context and features. Use empty string if no relevant info.

Return JSON array only:
[{{"question_id": "1.1.1", "suggested_answer": "answer", "confidence": "high/medium/low", "source_hint": "brief source"}}]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
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


def analyze_context_for_questions(context, questions, selected_features=None):
    """Analyze context and features to generate answers for ALL questions."""
    if anthropic is None:
        raise Exception("Anthropic library not available")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise Exception("Anthropic API key not configured")

    client = anthropic.Anthropic(api_key=api_key)

    # Use smaller batches (30 instead of 50) to reduce per-request latency
    # This ensures faster completion of each batch and better progress updates
    batch_size = 30
    all_responses = []

    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        try:
            batch_responses = analyze_context_for_questions_batch(
                context, batch, selected_features, client
            )
            all_responses.extend(batch_responses)
        except Exception as e:
            print(f"Error processing batch {i//batch_size + 1}: {e}")
            continue

    return all_responses


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
            op, project_id, question_id = parse_path(self.path)

            if op == 'list':
                questions_data = load_questions()
                if not questions_data.get('sections'):
                    self.send_json(500, {'error': 'No questions available', 'sections': []})
                else:
                    self.send_json(200, questions_data)
                return

            supabase = get_supabase()

            if op == 'responses' and project_id:
                result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
                self.send_json(200, result.data if result.data else [])

            elif op == 'response' and project_id and question_id:
                result = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', question_id).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(404, {'error': 'Response not found'})

            elif op == 'stats' and project_id:
                result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
                responses = result.data if result.data else []
                questions_data = load_questions()
                total_questions = sum(len(sub.get('questions', [])) for sec in questions_data.get('sections', []) for sub in sec.get('subsections', []))
                confirmed_count = sum(1 for r in responses if r.get('confirmed'))
                ai_suggested_count = sum(1 for r in responses if r.get('ai_suggested'))
                answered_count = sum(1 for r in responses if r.get('response') and r.get('response').strip())
                self.send_json(200, {
                    'total_questions': total_questions, 'answered': answered_count,
                    'confirmed': confirmed_count, 'ai_suggested': ai_suggested_count,
                    'completion_percentage': round((confirmed_count / total_questions) * 100, 1) if total_questions > 0 else 0
                })
            else:
                self.send_json(400, {'error': 'Invalid request path'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_PUT(self):
        try:
            op, project_id, question_id = parse_path(self.path)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            if not project_id or not validate_uuid(project_id):
                self.send_json(400, {'error': 'Invalid project ID format'})
                return

            supabase = get_supabase()

            if op == 'responses':
                responses = data.get('responses', [])
                if not responses:
                    self.send_json(400, {'error': 'No responses provided'})
                    return
                saved = []
                for resp in responses:
                    q_id = resp.get('question_id')
                    if not q_id:
                        continue
                    existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', q_id).execute()
                    response_data = {'project_id': project_id, 'question_id': q_id, 'response': resp.get('response', ''), 'ai_suggested': resp.get('ai_suggested', False), 'confirmed': resp.get('confirmed', False)}
                    if existing.data:
                        result = supabase.table('question_responses').update(response_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        response_data['id'] = str(uuid.uuid4())
                        result = supabase.table('question_responses').insert(response_data).execute()
                    if result.data:
                        saved.append(result.data[0])
                self.send_json(200, {'message': f'Saved {len(saved)} responses', 'responses': saved})

            elif op == 'response' and question_id:
                existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', question_id).execute()
                response_data = {'project_id': project_id, 'question_id': question_id, 'response': data.get('response', ''), 'ai_suggested': data.get('ai_suggested', False), 'confirmed': data.get('confirmed', False)}
                if existing.data:
                    result = supabase.table('question_responses').update(response_data).eq('id', existing.data[0]['id']).execute()
                else:
                    response_data['id'] = str(uuid.uuid4())
                    result = supabase.table('question_responses').insert(response_data).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(500, {'error': 'Failed to save response'})
            else:
                self.send_json(400, {'error': 'Invalid request path'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, project_id, question_id = parse_path(self.path)

            if not project_id or not validate_uuid(project_id):
                self.send_json(400, {'error': 'Invalid project ID format'})
                return

            supabase = get_supabase()

            if op == 'prefill':
                context_result = supabase.table('context_files').select('extracted_text').eq('project_id', project_id).execute()
                context_texts = [f.get('extracted_text', '') for f in (context_result.data or []) if f.get('extracted_text')]
                context = '\n\n---\n\n'.join(context_texts)

                if not context.strip():
                    self.send_json(400, {'error': 'No context available. Please upload context files first.'})
                    return

                questions_data = load_questions()
                flat_questions = get_flat_questions(questions_data)
                if not flat_questions:
                    self.send_json(500, {'error': 'No questions found to process'})
                    return

                features_result = supabase.table('features').select('name, description').eq('project_id', project_id).eq('is_selected', True).execute()
                selected_features = features_result.data if features_result.data else []

                try:
                    ai_responses = analyze_context_for_questions(context, flat_questions, selected_features)
                except Exception as e:
                    self.send_json(503, {'error': 'AI service temporarily unavailable', 'details': str(e)})
                    return

                if not ai_responses:
                    self.send_json(422, {'error': 'AI could not generate responses'})
                    return

                saved_responses = []
                for ai_resp in ai_responses:
                    q_id = ai_resp.get('question_id')
                    suggested = ai_resp.get('suggested_answer', '')
                    if not q_id or not suggested:
                        continue
                    existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', q_id).execute()
                    response_data = {'project_id': project_id, 'question_id': q_id, 'response': suggested, 'ai_suggested': True, 'confirmed': False}
                    if existing.data:
                        result = supabase.table('question_responses').update(response_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        response_data['id'] = str(uuid.uuid4())
                        result = supabase.table('question_responses').insert(response_data).execute()
                    if result.data:
                        saved_responses.append({'question_id': q_id, 'response': suggested, 'confidence': ai_resp.get('confidence', 'low')})

                self.send_json(200, {'message': f'AI prefilled {len(saved_responses)} questions', 'responses': saved_responses})

            elif op == 'confirm' and question_id:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body) if body else {}
                confirmed = data.get('confirmed', True)

                existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', question_id).execute()
                if not existing.data:
                    self.send_json(404, {'error': 'Response not found'})
                    return

                result = supabase.table('question_responses').update({'confirmed': confirmed}).eq('id', existing.data[0]['id']).execute()
                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(500, {'error': 'Failed to confirm response'})

            elif op == 'follow-ups' and question_id:
                # Get follow-up questions for a specific response
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body) if body else {}

                response_text = data.get('response', '')
                question_text = data.get('question', '')
                include_ai = data.get('include_ai', False)

                # Get rule-based follow-ups
                follow_ups = get_follow_up_questions(question_id, response_text)

                # Check skip logic
                skipped_questions = check_skip_logic(question_id, response_text)

                # Get related questions
                questions_data = load_questions()
                responses_result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
                responses = responses_result.data or []
                related = get_related_questions(question_id, questions_data, responses)

                # Optionally generate AI follow-ups
                ai_follow_ups = []
                if include_ai and response_text and len(response_text) > 50:
                    context_result = supabase.table('context_files').select('extracted_text').eq('project_id', project_id).limit(3).execute()
                    context = '\n'.join([f.get('extracted_text', '')[:2000] for f in (context_result.data or [])])
                    ai_follow_ups = generate_ai_follow_ups(question_text, response_text, context)

                self.send_json(200, {
                    'follow_ups': follow_ups,
                    'ai_follow_ups': ai_follow_ups,
                    'related_questions': related,
                    'skip_questions': skipped_questions
                })

            elif op == 'save-follow-up':
                # Save a follow-up question response
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body) if body else {}

                follow_up_id = data.get('follow_up_id')
                parent_question_id = data.get('parent_question_id')
                question_text = data.get('question')
                response_text = data.get('response', '')

                if not follow_up_id or not question_text:
                    self.send_json(400, {'error': 'follow_up_id and question are required'})
                    return

                # Store as a custom response
                response_data = {
                    'id': str(uuid.uuid4()),
                    'project_id': project_id,
                    'question_id': follow_up_id,
                    'response': response_text,
                    'ai_suggested': False,
                    'confirmed': True,
                    'metadata': json.dumps({
                        'type': 'follow_up',
                        'parent_question_id': parent_question_id,
                        'question_text': question_text
                    })
                }

                # Check if exists
                existing = supabase.table('question_responses').select('*').eq('project_id', project_id).eq('question_id', follow_up_id).execute()

                if existing.data:
                    result = supabase.table('question_responses').update({
                        'response': response_text,
                        'confirmed': True
                    }).eq('id', existing.data[0]['id']).execute()
                else:
                    result = supabase.table('question_responses').insert(response_data).execute()

                if result.data:
                    self.send_json(200, result.data[0])
                else:
                    self.send_json(500, {'error': 'Failed to save follow-up response'})

            elif op == 'smart-suggest' and question_id:
                # Get smart suggestions for a specific question based on context and other responses
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body) if body else {}

                question_text = data.get('question', '')

                # Get context
                context_result = supabase.table('context_files').select('extracted_text').eq('project_id', project_id).execute()
                context = '\n'.join([f.get('extracted_text', '')[:3000] for f in (context_result.data or [])])

                # Get other responses for context
                responses_result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
                other_responses = responses_result.data or []

                # Build context from responses
                responses_context = '\n'.join([
                    f"Q: {r.get('question_id', 'Unknown')}: {r.get('response', '')[:200]}"
                    for r in other_responses if r.get('response')
                ][:10])

                if anthropic is None or not os.environ.get('ANTHROPIC_API_KEY'):
                    self.send_json(503, {'error': 'AI service not available'})
                    return

                try:
                    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

                    prompt = f"""Based on the context and previous answers, suggest an answer for this question.

Question: {question_text}

Context Documents (excerpt):
{context[:5000]}

Previous Answers:
{responses_context}

Provide a suggested answer that is:
1. Consistent with previous answers
2. Based on the context provided
3. Concise but complete

Return JSON: {{"suggested_answer": "...", "confidence": "high/medium/low", "reasoning": "..."}}
Return ONLY the JSON, no other text."""

                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    response_text = message.content[0].text.strip()
                    if response_text.startswith('{'):
                        suggestion = json.loads(response_text)
                        self.send_json(200, suggestion)
                    else:
                        self.send_json(200, {'suggested_answer': '', 'confidence': 'low', 'reasoning': 'Could not generate suggestion'})

                except Exception as e:
                    self.send_json(500, {'error': f'Failed to generate suggestion: {str(e)}'})

            else:
                self.send_json(400, {'error': 'Invalid request path'})
        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
