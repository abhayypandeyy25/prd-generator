from flask import Blueprint, request, jsonify, Response
from app.services.supabase_service import supabase_service
from app.services.claude_service import claude_service
from app.services.prd_generator import prd_generator
import os
import json
import uuid

prd_bp = Blueprint('prd', __name__)

# Load PRD template
PRD_TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'templates', 'prd_template.md')


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def load_prd_template():
    """Load PRD template from file"""
    try:
        with open(PRD_TEMPLATE_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"PRD template file not found: {PRD_TEMPLATE_FILE}")
        return "# PRD Template\n\n[Template not found]"
    except Exception as e:
        print(f"Error loading PRD template: {e}")
        return "# PRD Template\n\n[Error loading template]"


def load_questions():
    """Load questions from JSON file"""
    questions_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')
    try:
        with open(questions_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Questions file not found: {questions_file}")
        return {'sections': []}
    except json.JSONDecodeError as e:
        print(f"Error parsing questions JSON: {e}")
        return {'sections': []}
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {'sections': []}


@prd_bp.route('/generate/<project_id>', methods=['POST'])
def generate_prd(project_id):
    """Generate PRD from confirmed responses"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        # Check if project exists
        project = supabase_service.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Get all responses
        responses = supabase_service.get_responses(project_id)

        if not responses:
            return jsonify({
                'error': 'No responses found. Please answer questions first.',
                'hint': 'Go to the Questions tab and answer at least some questions before generating a PRD.'
            }), 400

        # Check if there are confirmed responses
        confirmed_responses = [r for r in responses if r.get('confirmed')]
        if not confirmed_responses:
            return jsonify({
                'error': 'No confirmed responses found.',
                'hint': 'Please confirm at least some answers in the Questions tab before generating a PRD.',
                'total_responses': len(responses)
            }), 400

        # Load questions to get question text
        questions_data = load_questions()
        if not questions_data.get('sections'):
            return jsonify({'error': 'Questions data not available'}), 500

        question_map = {}
        for section in questions_data.get('sections', []):
            for subsection in section.get('subsections', []):
                for q in subsection.get('questions', []):
                    question_map[q['id']] = {
                        'question': q['question'],
                        'section': section['title'],
                        'subsection': subsection['title']
                    }

        # Organize responses by section
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

        # Load PRD template
        prd_template = load_prd_template()

        # Generate PRD using Claude
        try:
            prd_content = claude_service.generate_prd(organized_responses, prd_template)
        except Exception as e:
            print(f"Claude API error generating PRD: {e}")
            return jsonify({
                'error': 'AI service temporarily unavailable',
                'details': str(e)
            }), 503

        if not prd_content or prd_content.startswith('# Error'):
            return jsonify({
                'error': 'Failed to generate PRD content',
                'details': prd_content if prd_content else 'No content returned'
            }), 500

        # Save generated PRD
        try:
            saved_prd = supabase_service.save_prd(project_id, prd_content)
        except Exception as e:
            print(f"Error saving PRD: {e}")
            return jsonify({
                'error': 'PRD generated but failed to save',
                'content': prd_content,
                'details': str(e)
            }), 500

        return jsonify({
            'message': 'PRD generated successfully',
            'prd_id': saved_prd['id'] if saved_prd else None,
            'content': prd_content,
            'stats': {
                'total_responses': len(responses),
                'confirmed_responses': len(confirmed_responses),
                'sections_covered': len(organized_responses)
            }
        })

    except Exception as e:
        print(f"Error in generate_prd: {e}")
        return jsonify({'error': f'PRD generation failed: {str(e)}'}), 500


@prd_bp.route('/<project_id>', methods=['GET'])
def get_prd(project_id):
    """Get the generated PRD for a project"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        prd = supabase_service.get_prd(project_id)
        if prd:
            return jsonify(prd)
        return jsonify({
            'error': 'No PRD found. Please generate one first.',
            'hint': 'Go to the PRD tab and click Generate PRD.'
        }), 404

    except Exception as e:
        print(f"Error getting PRD: {e}")
        return jsonify({'error': f'Failed to get PRD: {str(e)}'}), 500


@prd_bp.route('/<project_id>/export/md', methods=['GET'])
def export_markdown(project_id):
    """Export PRD as Markdown file"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        prd = supabase_service.get_prd(project_id)
        if not prd:
            return jsonify({'error': 'No PRD found. Please generate one first.'}), 404

        content = prd.get('content_md', '')
        if not content:
            return jsonify({'error': 'PRD content is empty'}), 404

        try:
            md_bytes = prd_generator.generate_markdown_file(content)
        except Exception as e:
            print(f"Error generating markdown file: {e}")
            return jsonify({'error': f'Failed to generate markdown: {str(e)}'}), 500

        # Get project name for filename
        project = supabase_service.get_project(project_id)
        project_name = project.get('name', 'PRD') if project else 'PRD'
        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()

        return Response(
            md_bytes,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename=PRD_{safe_name}.md'
            }
        )

    except Exception as e:
        print(f"Error exporting markdown: {e}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@prd_bp.route('/<project_id>/export/docx', methods=['GET'])
def export_docx(project_id):
    """Export PRD as Word document"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        prd = supabase_service.get_prd(project_id)
        if not prd:
            return jsonify({'error': 'No PRD found. Please generate one first.'}), 404

        content = prd.get('content_md', '')
        if not content:
            return jsonify({'error': 'PRD content is empty'}), 404

        # Get project name for title
        project = supabase_service.get_project(project_id)
        project_name = project.get('name', 'Product') if project else 'Product'
        title = f"PRD - {project_name}"

        try:
            docx_bytes = prd_generator.markdown_to_docx(content, title)
        except Exception as e:
            print(f"Error generating DOCX: {e}")
            return jsonify({'error': f'Failed to generate Word document: {str(e)}'}), 500

        safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()

        return Response(
            docx_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                'Content-Disposition': f'attachment; filename=PRD_{safe_name}.docx'
            }
        )

    except Exception as e:
        print(f"Error exporting DOCX: {e}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@prd_bp.route('/<project_id>/preview', methods=['GET'])
def preview_prd(project_id):
    """Get PRD as HTML for preview"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        prd = supabase_service.get_prd(project_id)
        if not prd:
            return jsonify({
                'error': 'No PRD found. Please generate one first.',
                'markdown': '',
                'html': ''
            }), 404

        content = prd.get('content_md', '')

        try:
            html = prd_generator.markdown_to_html(content) if content else ''
        except Exception as e:
            print(f"Error converting to HTML: {e}")
            html = f'<p>Error converting to HTML: {str(e)}</p>'

        return jsonify({
            'markdown': content,
            'html': html,
            'created_at': prd.get('created_at'),
            'prd_id': prd.get('id')
        })

    except Exception as e:
        print(f"Error previewing PRD: {e}")
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500
