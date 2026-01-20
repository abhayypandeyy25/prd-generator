from flask import Blueprint, request, jsonify
from app.services.supabase_service import supabase_service
from app.services.claude_service import claude_service
import json
import os
import uuid

questions_bp = Blueprint('questions', __name__)

# Load questions from JSON file
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def load_questions():
    """Load questions from JSON file"""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Questions file not found: {QUESTIONS_FILE}")
        return {'sections': []}
    except json.JSONDecodeError as e:
        print(f"Error parsing questions JSON: {e}")
        return {'sections': []}
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {'sections': []}


@questions_bp.route('', methods=['GET'])
def get_questions():
    """Get all 150 questions organized by section"""
    try:
        questions = load_questions()
        if not questions.get('sections'):
            return jsonify({
                'error': 'No questions available',
                'sections': []
            }), 500
        return jsonify(questions)
    except Exception as e:
        print(f"Error getting questions: {e}")
        return jsonify({'error': f'Failed to load questions: {str(e)}'}), 500


@questions_bp.route('/prefill/<project_id>', methods=['POST'])
def prefill_questions(project_id):
    """Use AI to prefill question answers based on context"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        # Check if project exists
        project = supabase_service.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Get aggregated context
        context = supabase_service.get_aggregated_context(project_id)

        if not context or len(context.strip()) == 0:
            return jsonify({
                'error': 'No context available. Please upload context files first.',
                'hint': 'Upload documents, emails, or notes in the Context tab before using AI prefill.'
            }), 400

        # Get questions
        questions_data = load_questions()
        if not questions_data.get('sections'):
            return jsonify({'error': 'Questions data not available'}), 500

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

        if not flat_questions:
            return jsonify({'error': 'No questions found to process'}), 500

        # Call Claude to analyze context and suggest answers
        try:
            ai_responses = claude_service.analyze_context_for_questions(context, flat_questions)
        except Exception as e:
            print(f"Claude API error: {e}")
            return jsonify({
                'error': 'AI service temporarily unavailable',
                'details': str(e)
            }), 503

        if not ai_responses:
            return jsonify({
                'error': 'AI could not generate responses',
                'hint': 'The context might not contain enough relevant information.'
            }), 422

        # Save AI-suggested responses to database
        saved_responses = []
        save_errors = []

        for ai_resp in ai_responses:
            try:
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
            except Exception as e:
                save_errors.append({
                    'question_id': ai_resp.get('question_id'),
                    'error': str(e)
                })

        return jsonify({
            'message': f'AI prefilled {len(saved_responses)} questions',
            'responses': saved_responses,
            'total_processed': len(ai_responses),
            'save_errors': save_errors if save_errors else None
        })

    except Exception as e:
        print(f"Error in prefill_questions: {e}")
        return jsonify({'error': f'Prefill failed: {str(e)}'}), 500


@questions_bp.route('/<project_id>/responses', methods=['GET'])
def get_responses(project_id):
    """Get all saved responses for a project"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        responses = supabase_service.get_responses(project_id)
        return jsonify(responses if responses else [])

    except Exception as e:
        print(f"Error getting responses: {e}")
        return jsonify({'error': f'Failed to get responses: {str(e)}'}), 500


@questions_bp.route('/<project_id>/responses', methods=['PUT'])
def save_responses(project_id):
    """Save/update multiple question responses"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        # Check if project exists
        project = supabase_service.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        responses = data.get('responses', [])
        if not responses:
            return jsonify({'error': 'No responses provided'}), 400

        # Validate response format
        for i, resp in enumerate(responses):
            if not resp.get('question_id'):
                return jsonify({'error': f'Response at index {i} missing question_id'}), 400

        saved = supabase_service.save_responses_batch(project_id, responses)
        return jsonify({
            'message': f'Saved {len(saved) if saved else 0} responses',
            'responses': saved if saved else []
        })

    except Exception as e:
        print(f"Error saving responses: {e}")
        return jsonify({'error': f'Failed to save responses: {str(e)}'}), 500


@questions_bp.route('/<project_id>/response/<question_id>', methods=['PUT'])
def update_single_response(project_id, question_id):
    """Update a single question response"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        if not question_id:
            return jsonify({'error': 'Question ID is required'}), 400

        # Check if project exists
        project = supabase_service.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        response = supabase_service.save_response(
            project_id=project_id,
            question_id=question_id,
            response=data.get('response', ''),
            ai_suggested=data.get('ai_suggested', False),
            confirmed=data.get('confirmed', False)
        )

        if response:
            return jsonify(response)
        return jsonify({'error': 'Failed to save response'}), 500

    except Exception as e:
        print(f"Error updating response: {e}")
        return jsonify({'error': f'Failed to update response: {str(e)}'}), 500


@questions_bp.route('/<project_id>/confirm/<question_id>', methods=['POST'])
def confirm_response(project_id, question_id):
    """Mark a response as confirmed"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        if not question_id:
            return jsonify({'error': 'Question ID is required'}), 400

        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400

        confirmed = data.get('confirmed', True)

        response = supabase_service.confirm_response(project_id, question_id, confirmed)
        if response:
            return jsonify(response)
        return jsonify({'error': 'Response not found or failed to confirm'}), 404

    except Exception as e:
        print(f"Error confirming response: {e}")
        return jsonify({'error': f'Failed to confirm response: {str(e)}'}), 500


@questions_bp.route('/<project_id>/stats', methods=['GET'])
def get_response_stats(project_id):
    """Get statistics about question responses"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        responses = supabase_service.get_responses(project_id)
        questions_data = load_questions()

        # Count total questions
        total_questions = 0
        for section in questions_data.get('sections', []):
            for subsection in section.get('subsections', []):
                total_questions += len(subsection.get('questions', []))

        # Count responses
        responses = responses if responses else []
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

    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500
