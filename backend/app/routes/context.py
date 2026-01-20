from flask import Blueprint, request, jsonify
from app.services.supabase_service import supabase_service
from app.services.file_processor import file_processor
from app.config import Config
import uuid

context_bp = Blueprint('context', __name__)


@context_bp.route('/upload/<project_id>', methods=['POST'])
def upload_files(project_id):
    """Upload context files for a project"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    uploaded = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        # Check file extension
        ext = file_processor.get_file_extension(file.filename)
        if ext not in Config.ALLOWED_EXTENSIONS:
            errors.append(f"Unsupported file type: {file.filename}")
            continue

        try:
            # Read file data
            file_data = file.read()

            # Extract text from file
            extracted_text = file_processor.extract_text(file_data, file.filename)

            # Generate unique filename
            unique_filename = f"{project_id}/{uuid.uuid4()}_{file.filename}"

            # Upload to Supabase Storage
            file_url = supabase_service.upload_file('context-files', unique_filename, file_data)

            # Save metadata to database
            context_file = supabase_service.save_context_file(
                project_id=project_id,
                file_name=file.filename,
                file_type=ext,
                file_url=file_url or '',
                extracted_text=extracted_text
            )

            uploaded.append({
                'id': context_file['id'],
                'file_name': file.filename,
                'file_type': ext,
                'text_preview': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text
            })

        except Exception as e:
            errors.append(f"Error processing {file.filename}: {str(e)}")

    return jsonify({
        'uploaded': uploaded,
        'errors': errors
    })


@context_bp.route('/<project_id>', methods=['GET'])
def get_context_files(project_id):
    """Get all context files for a project"""
    files = supabase_service.get_context_files(project_id)
    return jsonify(files)


@context_bp.route('/file/<file_id>', methods=['DELETE'])
def delete_context_file(file_id):
    """Delete a specific context file"""
    supabase_service.delete_context_file(file_id)
    return jsonify({'message': 'File deleted'}), 200


@context_bp.route('/<project_id>/text', methods=['GET'])
def get_aggregated_context(project_id):
    """Get all context text aggregated"""
    text = supabase_service.get_aggregated_context(project_id)
    return jsonify({'text': text, 'length': len(text)})
