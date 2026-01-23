from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timedelta
from supabase import create_client


def get_supabase():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured")
    return create_client(url, key)


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }


def validate_uuid(uuid_str):
    try:
        import uuid
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def parse_path(path):
    """Parse path to determine operation
    /api/analytics/overview -> ('overview', None)
    /api/analytics/project/{project_id} -> ('project', project_id)
    /api/analytics/timeline/{project_id} -> ('timeline', project_id)
    """
    parts = path.strip('/').split('/')

    if len(parts) >= 3:
        if parts[2] == 'overview':
            return ('overview', None)
        elif parts[2] == 'project' and len(parts) >= 4:
            return ('project', parts[3])
        elif parts[2] == 'timeline' and len(parts) >= 4:
            return ('timeline', parts[3])

    return (None, None)


def calculate_time_spent(created_at, updated_at):
    """Estimate time spent based on creation and update times"""
    if not created_at or not updated_at:
        return 0

    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        delta = updated - created
        # Cap at 8 hours to avoid unrealistic estimates
        return min(delta.total_seconds() / 3600, 8.0)
    except:
        return 0


def get_overview_analytics(supabase):
    """Get overall analytics across all projects"""

    # Get all projects
    projects_result = supabase.table('projects').select('*').execute()
    projects = projects_result.data or []

    total_projects = len(projects)

    # Get PRDs
    prds_result = supabase.table('generated_prds').select('*').execute()
    prds = prds_result.data or []

    prds_generated = len(prds)

    # Get context files
    context_result = supabase.table('context_files').select('*').execute()
    context_files = context_result.data or []

    total_context_files = len(context_files)
    total_context_chars = sum(len(f.get('extracted_text', '')) for f in context_files)

    # Get question responses
    responses_result = supabase.table('question_responses').select('*').execute()
    responses = responses_result.data or []

    total_responses = len(responses)
    confirmed_responses = sum(1 for r in responses if r.get('confirmed'))
    ai_suggested = sum(1 for r in responses if r.get('ai_suggested'))

    # Calculate time metrics
    total_time_spent = 0
    for project in projects:
        time_spent = calculate_time_spent(
            project.get('created_at'),
            project.get('updated_at')
        )
        total_time_spent += time_spent

    # Recent activity (last 7 days)
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_projects = [p for p in projects if p.get('created_at', '') > seven_days_ago]
    recent_prds = [p for p in prds if p.get('created_at', '') > seven_days_ago]

    # Calculate averages
    avg_context_per_project = total_context_files / total_projects if total_projects > 0 else 0
    avg_responses_per_project = total_responses / total_projects if total_projects > 0 else 0
    avg_time_per_project = total_time_spent / total_projects if total_projects > 0 else 0

    return {
        'summary': {
            'total_projects': total_projects,
            'prds_generated': prds_generated,
            'total_context_files': total_context_files,
            'total_responses': total_responses,
            'confirmed_responses': confirmed_responses,
            'ai_suggested_responses': ai_suggested
        },
        'recent_activity': {
            'projects_last_7_days': len(recent_projects),
            'prds_last_7_days': len(recent_prds)
        },
        'averages': {
            'context_files_per_project': round(avg_context_per_project, 1),
            'responses_per_project': round(avg_responses_per_project, 1),
            'hours_per_project': round(avg_time_per_project, 2)
        },
        'efficiency': {
            'ai_assistance_rate': round((ai_suggested / total_responses * 100) if total_responses > 0 else 0, 1),
            'confirmation_rate': round((confirmed_responses / total_responses * 100) if total_responses > 0 else 0, 1)
        }
    }


def get_project_analytics(supabase, project_id):
    """Get detailed analytics for a specific project"""

    # Get project
    project_result = supabase.table('projects').select('*').eq('id', project_id).execute()
    if not project_result.data:
        return None

    project = project_result.data[0]

    # Get context files
    context_result = supabase.table('context_files').select('*').eq('project_id', project_id).execute()
    context_files = context_result.data or []

    # Get features
    features_result = supabase.table('features').select('*').eq('project_id', project_id).execute()
    features = features_result.data or []

    selected_features = [f for f in features if f.get('is_selected')]

    # Get question responses
    responses_result = supabase.table('question_responses').select('*').eq('project_id', project_id).execute()
    responses = responses_result.data or []

    # Get PRD
    prd_result = supabase.table('generated_prds').select('*').eq('project_id', project_id).execute()
    prd = prd_result.data[0] if prd_result.data else None

    # Get PRD history
    history_count = 0
    if prd:
        history_result = supabase.table('prd_edit_snapshots').select('id').eq('prd_id', prd['id']).execute()
        history_count = len(history_result.data or [])

    # Get feedback
    feedback_result = supabase.table('prd_feedback').select('*').eq('project_id', project_id).execute()
    feedback = feedback_result.data or []

    # Calculate metrics
    time_spent = calculate_time_spent(project.get('created_at'), project.get('updated_at'))

    confirmed = sum(1 for r in responses if r.get('confirmed'))
    ai_suggested = sum(1 for r in responses if r.get('ai_suggested'))

    total_context_chars = sum(len(f.get('extracted_text', '')) for f in context_files)

    avg_feedback_rating = None
    if feedback:
        ratings = [f['rating'] for f in feedback if f.get('rating')]
        avg_feedback_rating = sum(ratings) / len(ratings) if ratings else None

    # Completion stages
    stages = {
        'context_uploaded': len(context_files) > 0,
        'features_extracted': len(features) > 0,
        'questions_confirmed': confirmed >= 10,
        'prd_generated': prd is not None,
        'feedback_provided': len(feedback) > 0
    }

    completion_percentage = sum(1 for v in stages.values() if v) / len(stages) * 100

    return {
        'project_info': {
            'id': project_id,
            'name': project.get('name'),
            'created_at': project.get('created_at'),
            'updated_at': project.get('updated_at'),
            'time_spent_hours': round(time_spent, 2)
        },
        'completion': {
            'percentage': round(completion_percentage, 1),
            'stages': stages
        },
        'context': {
            'files_uploaded': len(context_files),
            'total_characters': total_context_chars,
            'file_types': list(set(f.get('file_type') for f in context_files))
        },
        'features': {
            'total_extracted': len(features),
            'selected': len(selected_features),
            'in_parking_lot': len(features) - len(selected_features)
        },
        'questions': {
            'total_responses': len(responses),
            'confirmed': confirmed,
            'ai_suggested': ai_suggested,
            'confirmation_rate': round((confirmed / len(responses) * 100) if responses else 0, 1)
        },
        'prd': {
            'generated': prd is not None,
            'version': prd.get('version', 1) if prd else 0,
            'edit_history_count': history_count,
            'word_count': len(prd.get('content_md', '').split()) if prd else 0
        },
        'feedback': {
            'total_feedback': len(feedback),
            'average_rating': round(avg_feedback_rating, 2) if avg_feedback_rating else None
        }
    }


def get_project_timeline(supabase, project_id):
    """Get timeline of events for a project"""

    timeline = []

    # Project creation
    project_result = supabase.table('projects').select('*').eq('id', project_id).execute()
    if project_result.data:
        project = project_result.data[0]
        timeline.append({
            'type': 'project_created',
            'timestamp': project.get('created_at'),
            'description': f"Project '{project.get('name')}' created"
        })

    # Context files
    context_result = supabase.table('context_files').select('file_name, created_at').eq('project_id', project_id).order('created_at').execute()
    for file in (context_result.data or []):
        timeline.append({
            'type': 'context_uploaded',
            'timestamp': file.get('created_at'),
            'description': f"Uploaded {file.get('file_name')}"
        })

    # Features extracted
    features_result = supabase.table('features').select('created_at').eq('project_id', project_id).limit(1).execute()
    if features_result.data:
        timeline.append({
            'type': 'features_extracted',
            'timestamp': features_result.data[0].get('created_at'),
            'description': 'Features extracted from context'
        })

    # PRD generated
    prd_result = supabase.table('generated_prds').select('created_at, version').eq('project_id', project_id).execute()
    if prd_result.data:
        prd = prd_result.data[0]
        timeline.append({
            'type': 'prd_generated',
            'timestamp': prd.get('created_at'),
            'description': f"PRD generated (v{prd.get('version', 1)})"
        })

    # Sort by timestamp
    timeline.sort(key=lambda x: x.get('timestamp', ''))

    return timeline


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
            op, project_id = parse_path(self.path)
            supabase = get_supabase()

            if op == 'overview':
                analytics = get_overview_analytics(supabase)
                self.send_json(200, analytics)
                return

            elif op == 'project':
                if not project_id or not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                analytics = get_project_analytics(supabase, project_id)
                if analytics:
                    self.send_json(200, analytics)
                else:
                    self.send_json(404, {'error': 'Project not found'})
                return

            elif op == 'timeline':
                if not project_id or not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                timeline = get_project_timeline(supabase, project_id)
                self.send_json(200, {'timeline': timeline})
                return

            self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
