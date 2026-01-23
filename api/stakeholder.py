from http.server import BaseHTTPRequestHandler
import json
import os
import uuid
from supabase import create_client

try:
    import anthropic
except ImportError:
    anthropic = None


STAKEHOLDER_PROFILES = {
    'engineering': {
        'name': 'Engineering',
        'icon': '⚙️',
        'focus_areas': [
            'Technical Requirements',
            'System Architecture',
            'API Specifications',
            'Data Models',
            'Integration Points',
            'Performance Requirements',
            'Security Considerations',
            'Technical Constraints'
        ],
        'hide_sections': ['Market Analysis', 'Business Goals'],
        'summary_prompt': '''Create an engineering-focused summary that emphasizes:
- Technical architecture and system design
- API specifications and data models
- Integration requirements
- Performance benchmarks
- Security and compliance requirements
- Technical dependencies and risks'''
    },
    'design': {
        'name': 'Design',
        'icon': '🎨',
        'focus_areas': [
            'User Experience',
            'User Personas',
            'User Journeys',
            'UI Requirements',
            'Accessibility',
            'Design System',
            'Interaction Patterns'
        ],
        'hide_sections': ['Technical Architecture', 'API Specifications'],
        'summary_prompt': '''Create a design-focused summary that emphasizes:
- User personas and their needs
- User journey and flow
- UX requirements and expectations
- Visual and interaction guidelines
- Accessibility requirements
- Design constraints'''
    },
    'leadership': {
        'name': 'Leadership',
        'icon': '👔',
        'focus_areas': [
            'Business Goals',
            'Success Metrics',
            'Timeline',
            'Resource Requirements',
            'Strategic Alignment',
            'ROI',
            'Risk Assessment'
        ],
        'hide_sections': ['Technical Implementation', 'API Details'],
        'summary_prompt': '''Create an executive summary that emphasizes:
- Strategic value and business impact
- Key success metrics and KPIs
- Timeline and milestones
- Resource and budget requirements
- Risks and mitigation strategies
- Alignment with company goals'''
    },
    'qa': {
        'name': 'QA/Testing',
        'icon': '🧪',
        'focus_areas': [
            'Acceptance Criteria',
            'Test Scenarios',
            'Edge Cases',
            'Performance Benchmarks',
            'Security Testing',
            'Integration Testing'
        ],
        'hide_sections': ['Market Analysis', 'Business Strategy'],
        'summary_prompt': '''Create a QA-focused summary that emphasizes:
- Acceptance criteria for each feature
- Test scenarios and edge cases
- Performance and load testing requirements
- Security testing needs
- Integration test points
- Quality gates and release criteria'''
    },
    'marketing': {
        'name': 'Marketing',
        'icon': '📣',
        'focus_areas': [
            'Value Proposition',
            'Target Audience',
            'Competitive Advantage',
            'Key Features',
            'Launch Timeline',
            'Messaging'
        ],
        'hide_sections': ['Technical Details', 'API Specifications'],
        'summary_prompt': '''Create a marketing-focused summary that emphasizes:
- Target audience and personas
- Key value propositions
- Feature highlights and benefits
- Competitive differentiation
- Launch timeline and go-to-market
- Messaging themes'''
    }
}


def get_supabase():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured")
    return create_client(url, key)


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
    /api/stakeholder/profiles -> ('profiles', None, None)
    /api/stakeholder/view/{project_id}/{role} -> ('view', project_id, role)
    /api/stakeholder/summary/{project_id}/{role} -> ('summary', project_id, role)
    """
    parts = path.strip('/').split('/')

    if len(parts) >= 3:
        if parts[2] == 'profiles':
            return ('profiles', None, None)
        elif parts[2] == 'view' and len(parts) >= 5:
            return ('view', parts[3], parts[4])
        elif parts[2] == 'summary' and len(parts) >= 5:
            return ('summary', parts[3], parts[4])

    return (None, None, None)


def filter_prd_for_stakeholder(prd_content, role):
    """Filter PRD content based on stakeholder role"""
    if role not in STAKEHOLDER_PROFILES:
        return prd_content

    profile = STAKEHOLDER_PROFILES[role]
    hide_sections = profile.get('hide_sections', [])

    if not hide_sections:
        return prd_content

    # Simple section filtering based on headers
    lines = prd_content.split('\n')
    filtered_lines = []
    skip_section = False
    current_level = 0

    for line in lines:
        # Check if this is a header
        if line.startswith('#'):
            header_level = len(line) - len(line.lstrip('#'))
            header_text = line.lstrip('#').strip()

            # Check if this section should be hidden
            should_hide = any(hide.lower() in header_text.lower() for hide in hide_sections)

            if should_hide:
                skip_section = True
                current_level = header_level
            elif skip_section and header_level <= current_level:
                skip_section = False

        if not skip_section:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def generate_stakeholder_summary(prd_content, role, project_name=''):
    """Generate a role-specific summary using AI"""
    if anthropic is None:
        return None

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    if role not in STAKEHOLDER_PROFILES:
        return None

    profile = STAKEHOLDER_PROFILES[role]

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Based on the following PRD for "{project_name}", {profile['summary_prompt']}

PRD Content:
{prd_content[:12000]}

Create a concise summary (500-800 words) in markdown format with clear sections.
Focus only on information relevant to the {profile['name']} team.
Include specific details, metrics, and actionable items where available.
"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text.strip()
    except Exception as e:
        print(f"Stakeholder summary generation error: {e}")
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
            op, project_id, role = parse_path(self.path)

            if op == 'profiles':
                # Return all stakeholder profiles
                profiles = []
                for key, profile in STAKEHOLDER_PROFILES.items():
                    profiles.append({
                        'id': key,
                        'name': profile['name'],
                        'icon': profile['icon'],
                        'focus_areas': profile['focus_areas']
                    })
                self.send_json(200, {'profiles': profiles})
                return

            if op == 'view':
                if not project_id or not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                if role not in STAKEHOLDER_PROFILES:
                    self.send_json(400, {'error': f'Invalid role. Valid roles: {list(STAKEHOLDER_PROFILES.keys())}'})
                    return

                supabase = get_supabase()

                # Get the PRD
                prd_result = supabase.table('generated_prds').select('*').eq('project_id', project_id).execute()
                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                prd = prd_result.data[0]
                prd_content = prd.get('content_md', '')

                # Filter for stakeholder
                filtered_content = filter_prd_for_stakeholder(prd_content, role)

                profile = STAKEHOLDER_PROFILES[role]

                self.send_json(200, {
                    'role': role,
                    'profile': {
                        'name': profile['name'],
                        'icon': profile['icon'],
                        'focus_areas': profile['focus_areas']
                    },
                    'content': filtered_content,
                    'project_id': project_id
                })
                return

            self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return

    def do_POST(self):
        try:
            op, project_id, role = parse_path(self.path)

            if op == 'summary':
                if not project_id or not validate_uuid(project_id):
                    self.send_json(400, {'error': 'Invalid project ID'})
                    return

                if role not in STAKEHOLDER_PROFILES:
                    self.send_json(400, {'error': f'Invalid role. Valid roles: {list(STAKEHOLDER_PROFILES.keys())}'})
                    return

                supabase = get_supabase()

                # Get project name
                project_result = supabase.table('projects').select('name').eq('id', project_id).execute()
                project_name = project_result.data[0]['name'] if project_result.data else 'Project'

                # Get the PRD
                prd_result = supabase.table('generated_prds').select('content_md').eq('project_id', project_id).execute()
                if not prd_result.data:
                    self.send_json(404, {'error': 'PRD not found'})
                    return

                prd_content = prd_result.data[0].get('content_md', '')

                # Generate stakeholder summary
                summary = generate_stakeholder_summary(prd_content, role, project_name)

                if not summary:
                    self.send_json(500, {'error': 'Failed to generate summary'})
                    return

                profile = STAKEHOLDER_PROFILES[role]

                self.send_json(200, {
                    'role': role,
                    'profile': {
                        'name': profile['name'],
                        'icon': profile['icon']
                    },
                    'summary': summary,
                    'project_id': project_id
                })
                return

            self.send_json(400, {'error': 'Invalid request path'})

        except Exception as e:
            self.send_json(500, {'error': str(e)})
        return
