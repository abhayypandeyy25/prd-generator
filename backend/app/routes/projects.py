from flask import Blueprint, request, jsonify
from app.services.supabase_service import supabase_service

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.get_json()
    name = data.get('name', 'Untitled Project')

    project = supabase_service.create_project(name)
    if project:
        return jsonify(project), 201
    return jsonify({'error': 'Failed to create project'}), 500


@projects_bp.route('', methods=['GET'])
def list_projects():
    """List all projects"""
    projects = supabase_service.list_projects()
    return jsonify(projects)


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    project = supabase_service.get_project(project_id)
    if project:
        return jsonify(project)
    return jsonify({'error': 'Project not found'}), 404


@projects_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    supabase_service.delete_project(project_id)
    return jsonify({'message': 'Project deleted'}), 200
