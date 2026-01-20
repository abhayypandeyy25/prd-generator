from flask import Blueprint, request, jsonify
from app.services.supabase_service import supabase_service
from app.services.claude_service import claude_service
import json
import os

questions_bp = Blueprint('questions', __name__)

# Load questions from JSON file
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')


def load_questions():
    """Load questions from JSON file"""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'sections': []}


@questions_bp.route('', methods=['GET'])
def get_questions():
    """Get all 150 questions organized by section"""
    questions = load_questions()
    return jsonify(questions)


@questions_bp.route('/prefill/<project_id>', methods=['POST'])
def prefill_questions(project_id):
    """Use AI to prefill question answers based on context"""
    # Get aggregated context
    context = supabase_service.get_aggregated_context(project_id)

    if not context or len(context.strip()) == 0:
        return jsonify({'error': 'No context available. Please upload context files first.'}), 400

    # Get questions
    questions_data = load_questions()

    # Flatten questions for AI processing
    flat_questions = []
    for section in questions_data.get('sections', []):
        for subsection in section.get('subsections', []):
            for q in subsection.get('questions', []):
                flat_questions.append({
                    'id': q['id'],
                    'question': q['question'],
                    'type': q.get('type', 'text')
                })

    # Call Claude to analyze context and suggest answers
    ai_responses = claude_service.analyze_context_for_questions(context, flat_questions)

    # Save AI-suggested responses to database
    saved_responses = []
    for ai_resp in ai_responses:
        response = supabase_service.save_response(
            project_id=project_id,
            question_id=ai_resp.get('question_id'),
            response=ai_resp.get('suggested_answer', ''),
            ai_suggested=True,
            confirmed=False
        )
        if response:
            saved_responses.append({
                'question_id': ai_resp.get('question_id'),
                'response': ai_resp.get('suggested_answer'),
                'confidence': ai_resp.get('confidence', 'low'),
                'source_hint': ai_resp.get('source_hint', '')
            })

    return jsonify({
        'message': f'AI prefilled {len(saved_responses)} questions',
        'responses': saved_responses
    })


@questions_bp.route('/<project_id>/responses', methods=['GET'])
def get_responses(project_id):
    """Get all saved responses for a project"""
    responses = supabase_service.get_responses(project_id)
    return jsonify(responses)


@questions_bp.route('/<project_id>/responses', methods=['PUT'])
def save_responses(project_id):
    """Save/update multiple question responses"""
    data = request.get_json()
    responses = data.get('responses', [])

    if not responses:
        return jsonify({'error': 'No responses provided'}), 400

    saved = supabase_service.save_responses_batch(project_id, responses)
    return jsonify({
        'message': f'Saved {len(saved)} responses',
        'responses': saved
    })


@questions_bp.route('/<project_id>/response/<question_id>', methods=['PUT'])
def update_single_response(project_id, question_id):
    """Update a single question response"""
    data = request.get_json()

    response = supabase_service.save_response(
        project_id=project_id,
        question_id=question_id,
        response=data.get('response', ''),
        ai_suggested=data.get('ai_suggested', False),
        confirmed=data.get('confirmed', False)
    )

    return jsonify(response)


@questions_bp.route('/<project_id>/confirm/<question_id>', methods=['POST'])
def confirm_response(project_id, question_id):
    """Mark a response as confirmed"""
    data = request.get_json()
    confirmed = data.get('confirmed', True)

    response = supabase_service.confirm_response(project_id, question_id, confirmed)
    return jsonify(response)


@questions_bp.route('/<project_id>/stats', methods=['GET'])
def get_response_stats(project_id):
    """Get statistics about question responses"""
    responses = supabase_service.get_responses(project_id)
    questions_data = load_questions()

    # Count total questions
    total_questions = 0
    for section in questions_data.get('sections', []):
        for subsection in section.get('subsections', []):
            total_questions += len(subsection.get('questions', []))

    # Count responses
    confirmed_count = sum(1 for r in responses if r.get('confirmed'))
    ai_suggested_count = sum(1 for r in responses if r.get('ai_suggested'))
    answered_count = sum(1 for r in responses if r.get('response') and r.get('response').strip())

    return jsonify({
        'total_questions': total_questions,
        'answered': answered_count,
        'confirmed': confirmed_count,
        'ai_suggested': ai_suggested_count,
        'completion_percentage': round((confirmed_count / total_questions) * 100, 1) if total_questions > 0 else 0
    })
