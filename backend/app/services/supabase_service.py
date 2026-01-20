from supabase import create_client, Client
from app.config import Config
import uuid

class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    # Projects
    def create_project(self, name: str) -> dict:
        result = self.client.table('projects').insert({'name': name}).execute()
        return result.data[0] if result.data else None

    def get_project(self, project_id: str) -> dict:
        result = self.client.table('projects').select('*').eq('id', project_id).execute()
        return result.data[0] if result.data else None

    def list_projects(self) -> list:
        result = self.client.table('projects').select('*').order('created_at', desc=True).execute()
        return result.data

    def delete_project(self, project_id: str) -> bool:
        self.client.table('projects').delete().eq('id', project_id).execute()
        return True

    # Context Files
    def save_context_file(self, project_id: str, file_name: str, file_type: str,
                          file_url: str, extracted_text: str) -> dict:
        result = self.client.table('context_files').insert({
            'project_id': project_id,
            'file_name': file_name,
            'file_type': file_type,
            'file_url': file_url,
            'extracted_text': extracted_text
        }).execute()
        return result.data[0] if result.data else None

    def get_context_files(self, project_id: str) -> list:
        result = self.client.table('context_files').select('*').eq('project_id', project_id).execute()
        return result.data

    def delete_context_file(self, file_id: str) -> bool:
        self.client.table('context_files').delete().eq('id', file_id).execute()
        return True

    def get_aggregated_context(self, project_id: str) -> str:
        files = self.get_context_files(project_id)
        texts = []
        for f in files:
            if f.get('extracted_text'):
                texts.append(f"=== {f['file_name']} ===\n{f['extracted_text']}")
        return "\n\n".join(texts)

    # Question Responses
    def save_response(self, project_id: str, question_id: str, response: str,
                      ai_suggested: bool = False, confirmed: bool = False) -> dict:
        # Upsert - insert or update
        result = self.client.table('question_responses').upsert({
            'project_id': project_id,
            'question_id': question_id,
            'response': response,
            'ai_suggested': ai_suggested,
            'confirmed': confirmed
        }, on_conflict='project_id,question_id').execute()
        return result.data[0] if result.data else None

    def save_responses_batch(self, project_id: str, responses: list) -> list:
        data = []
        for r in responses:
            data.append({
                'project_id': project_id,
                'question_id': r['question_id'],
                'response': r.get('response', ''),
                'ai_suggested': r.get('ai_suggested', False),
                'confirmed': r.get('confirmed', False)
            })
        result = self.client.table('question_responses').upsert(
            data, on_conflict='project_id,question_id'
        ).execute()
        return result.data

    def get_responses(self, project_id: str) -> list:
        result = self.client.table('question_responses').select('*').eq('project_id', project_id).execute()
        return result.data

    def confirm_response(self, project_id: str, question_id: str, confirmed: bool = True) -> dict:
        result = self.client.table('question_responses').update({
            'confirmed': confirmed
        }).eq('project_id', project_id).eq('question_id', question_id).execute()
        return result.data[0] if result.data else None

    # PRD
    def save_prd(self, project_id: str, content_md: str) -> dict:
        # Delete existing PRD for this project first
        self.client.table('generated_prds').delete().eq('project_id', project_id).execute()
        result = self.client.table('generated_prds').insert({
            'project_id': project_id,
            'content_md': content_md
        }).execute()
        return result.data[0] if result.data else None

    def get_prd(self, project_id: str) -> dict:
        result = self.client.table('generated_prds').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(1).execute()
        return result.data[0] if result.data else None

    # File Storage
    def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> str:
        try:
            self.client.storage.from_(bucket).upload(file_path, file_data)
            return self.client.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            print(f"Upload error: {e}")
            return None

    def delete_file(self, bucket: str, file_path: str) -> bool:
        try:
            self.client.storage.from_(bucket).remove([file_path])
            return True
        except Exception:
            return False


# Singleton instance
supabase_service = SupabaseService()
