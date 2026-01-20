from flask import Blueprint, request, jsonify, Response
from app.services.supabase_service import supabase_service
from app.services.claude_service import claude_service
from app.services.prd_generator import prd_generator
import os
import json

prd_bp = Blueprint('prd', __name__)

# Load PRD template
PRD_TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'templates', 'prd_template.md')


def load_prd_template():
    """Load PRD template from file"""
    try:
        with open(PRD_TEMPLATE_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "# PRD Template\n\n[Template not found]"


def load_questions():
    """Load questions from JSON file"""
    questions_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions.json')
    try:
        with open(questions_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'sections': []}


@prd_bp.route('/generate/<project_id>', methods=['POST'])
def generate_prd(project_id):
    """Generate PRD from confirmed responses"""
    # Get all responses
    responses = supabase_service.get_responses(project_id)

    if not responses:
        return jsonify({'error': 'No responses found. Please answer questions first.'}), 400

    # Load questions to get question text
    questions_data = load_questions()
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
    prd_content = claude_service.generate_prd(organized_responses, prd_template)

    # Save generated PRD
    saved_prd = supabase_service.save_prd(project_id, prd_content)

    return jsonify({
        'message': 'PRD generated successfully',
        'prd_id': saved_prd['id'] if saved_prd else None,
        'content': prd_content
    })


@prd_bp.route('/<project_id>', methods=['GET'])
def get_prd(project_id):
    """Get the generated PRD for a project"""
    prd = supabase_service.get_prd(project_id)
    if prd:
        return jsonify(prd)
    return jsonify({'error': 'No PRD found. Please generate one first.'}), 404


@prd_bp.route('/<project_id>/export/md', methods=['GET'])
def export_markdown(project_id):
    """Export PRD as Markdown file"""
    prd = supabase_service.get_prd(project_id)
    if not prd:
        return jsonify({'error': 'No PRD found'}), 404

    content = prd.get('content_md', '')
    md_bytes = prd_generator.generate_markdown_file(content)

    return Response(
        md_bytes,
        mimetype='text/markdown',
        headers={
            'Content-Disposition': f'attachment; filename=PRD_{project_id[:8]}.md'
        }
    )


@prd_bp.route('/<project_id>/export/docx', methods=['GET'])
def export_docx(project_id):
    """Export PRD as Word document"""
    prd = supabase_service.get_prd(project_id)
    if not prd:
        return jsonify({'error': 'No PRD found'}), 404

    # Get project name for title
    project = supabase_service.get_project(project_id)
    title = f"PRD - {project.get('name', 'Product')}" if project else "Product Requirements Document"

    content = prd.get('content_md', '')
    docx_bytes = prd_generator.markdown_to_docx(content, title)

    return Response(
        docx_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f'attachment; filename=PRD_{project_id[:8]}.docx'
        }
    )


@prd_bp.route('/<project_id>/preview', methods=['GET'])
def preview_prd(project_id):
    """Get PRD as HTML for preview"""
    prd = supabase_service.get_prd(project_id)
    if not prd:
        return jsonify({'error': 'No PRD found'}), 404

    content = prd.get('content_md', '')
    html = prd_generator.markdown_to_html(content)

    return jsonify({
        'markdown': content,
        'html': html
    })
