from flask import Blueprint, request, jsonify
from app.services.supabase_service import supabase_service
from app.services.file_processor import file_processor
from app.config import Config
import uuid

context_bp = Blueprint('context', __name__)


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


@context_bp.route('/upload/<project_id>', methods=['POST'])
def upload_files(project_id):
    """Upload context files for a project"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        # Check if project exists
        project = supabase_service.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No valid files provided'}), 400

        uploaded = []
        errors = []

        for file in files:
            if file.filename == '':
                continue

            # Check file extension
            ext = file_processor.get_file_extension(file.filename)
            if ext not in Config.ALLOWED_EXTENSIONS:
                errors.append({
                    'file': file.filename,
                    'error': f"Unsupported file type: .{ext}. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
                })
                continue

            try:
                # Read file data
                file_data = file.read()

                # Check file size
                if len(file_data) > Config.MAX_FILE_SIZE:
                    errors.append({
                        'file': file.filename,
                        'error': f"File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
                    })
                    continue

                if len(file_data) == 0:
                    errors.append({
                        'file': file.filename,
                        'error': 'File is empty'
                    })
                    continue

                # Extract text from file
                extracted_text = file_processor.extract_text(file_data, file.filename)

                if extracted_text.startswith('Error extracting text:'):
                    errors.append({
                        'file': file.filename,
                        'error': extracted_text
                    })
                    continue

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

                if context_file:
                    uploaded.append({
                        'id': context_file['id'],
                        'file_name': file.filename,
                        'file_type': ext,
                        'text_length': len(extracted_text),
                        'text_preview': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text
                    })
                else:
                    errors.append({
                        'file': file.filename,
                        'error': 'Failed to save file metadata to database'
                    })

            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                errors.append({
                    'file': file.filename,
                    'error': f"Processing error: {str(e)}"
                })

        return jsonify({
            'uploaded': uploaded,
            'errors': errors,
            'summary': {
                'total_files': len(files),
                'successful': len(uploaded),
                'failed': len(errors)
            }
        })

    except Exception as e:
        print(f"Error in upload_files: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@context_bp.route('/<project_id>', methods=['GET'])
def get_context_files(project_id):
    """Get all context files for a project"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        files = supabase_service.get_context_files(project_id)
        return jsonify(files if files else [])

    except Exception as e:
        print(f"Error getting context files: {e}")
        return jsonify({'error': f'Failed to get files: {str(e)}'}), 500


@context_bp.route('/file/<file_id>', methods=['DELETE'])
def delete_context_file(file_id):
    """Delete a specific context file"""
    try:
        # Validate file_id
        if not file_id or not validate_uuid(file_id):
            return jsonify({'error': 'Invalid file ID format'}), 400

        success = supabase_service.delete_context_file(file_id)
        if success:
            return jsonify({'message': 'File deleted successfully'}), 200
        return jsonify({'error': 'Failed to delete file'}), 500

    except Exception as e:
        print(f"Error deleting context file: {e}")
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@context_bp.route('/<project_id>/text', methods=['GET'])
def get_aggregated_context(project_id):
    """Get all context text aggregated"""
    try:
        # Validate project_id
        if not project_id or not validate_uuid(project_id):
            return jsonify({'error': 'Invalid project ID format'}), 400

        text = supabase_service.get_aggregated_context(project_id)
        return jsonify({
            'text': text if text else '',
            'length': len(text) if text else 0,
            'has_content': bool(text and text.strip())
        })

    except Exception as e:
        print(f"Error getting aggregated context: {e}")
        return jsonify({'error': f'Failed to get context: {str(e)}'}), 500
