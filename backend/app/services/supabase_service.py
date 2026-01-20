from supabase import create_client, Client
from app.config import Config
import uuid


class SupabaseServiceError(Exception):
    """Custom exception for Supabase service errors"""
    pass


class SupabaseService:
    def __init__(self):
        try:
            if not Config.SUPABASE_URL:
                raise SupabaseServiceError("SUPABASE_URL not configured")
            if not Config.SUPABASE_KEY:
                raise SupabaseServiceError("SUPABASE_KEY not configured")
            self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            raise SupabaseServiceError(f"Supabase initialization failed: {str(e)}")

    # Projects
    def create_project(self, name: str) -> dict:
        """Create a new project"""
        try:
            if not name or not name.strip():
                raise ValueError("Project name is required")

            result = self.client.table('projects').insert({'name': name.strip()}).execute()
            print(f"Supabase create_project result: {result}")

            if not result.data:
                raise SupabaseServiceError("No data returned from database")

            return result.data[0]
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase create_project error: {e}")
            raise SupabaseServiceError(f"Failed to create project: {str(e)}")

    def get_project(self, project_id: str) -> dict:
        """Get a project by ID"""
        try:
            if not project_id:
                return None

            result = self.client.table('projects').select('*').eq('id', project_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase get_project error: {e}")
            return None

    def list_projects(self) -> list:
        """List all projects"""
        try:
            result = self.client.table('projects').select('*').order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Supabase list_projects error: {e}")
            return []

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID"""
        try:
            if not project_id:
                return False

            self.client.table('projects').delete().eq('id', project_id).execute()
            return True
        except Exception as e:
            print(f"Supabase delete_project error: {e}")
            raise SupabaseServiceError(f"Failed to delete project: {str(e)}")

    # Context Files
    def save_context_file(self, project_id: str, file_name: str, file_type: str,
                          file_url: str, extracted_text: str) -> dict:
        """Save context file metadata"""
        try:
            if not project_id:
                raise ValueError("Project ID is required")
            if not file_name:
                raise ValueError("File name is required")

            result = self.client.table('context_files').insert({
                'project_id': project_id,
                'file_name': file_name,
                'file_type': file_type or 'unknown',
                'file_url': file_url or '',
                'extracted_text': extracted_text or ''
            }).execute()

            if not result.data:
                raise SupabaseServiceError("No data returned from database")

            return result.data[0]
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase save_context_file error: {e}")
            raise SupabaseServiceError(f"Failed to save context file: {str(e)}")

    def get_context_files(self, project_id: str) -> list:
        """Get all context files for a project"""
        try:
            if not project_id:
                return []

            result = self.client.table('context_files').select('*').eq('project_id', project_id).order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Supabase get_context_files error: {e}")
            return []

    def delete_context_file(self, file_id: str) -> bool:
        """Delete a context file by ID"""
        try:
            if not file_id:
                return False

            self.client.table('context_files').delete().eq('id', file_id).execute()
            return True
        except Exception as e:
            print(f"Supabase delete_context_file error: {e}")
            raise SupabaseServiceError(f"Failed to delete context file: {str(e)}")

    def get_aggregated_context(self, project_id: str) -> str:
        """Get all context text aggregated for a project"""
        try:
            files = self.get_context_files(project_id)
            texts = []
            for f in files:
                extracted_text = f.get('extracted_text')
                if extracted_text and extracted_text.strip():
                    texts.append(f"=== {f.get('file_name', 'Unknown')} ===\n{extracted_text}")
            return "\n\n".join(texts)
        except Exception as e:
            print(f"Supabase get_aggregated_context error: {e}")
            return ""

    # Question Responses
    def save_response(self, project_id: str, question_id: str, response: str,
                      ai_suggested: bool = False, confirmed: bool = False) -> dict:
        """Save or update a question response"""
        try:
            if not project_id:
                raise ValueError("Project ID is required")
            if not question_id:
                raise ValueError("Question ID is required")

            result = self.client.table('question_responses').upsert({
                'project_id': project_id,
                'question_id': question_id,
                'response': response or '',
                'ai_suggested': bool(ai_suggested),
                'confirmed': bool(confirmed)
            }, on_conflict='project_id,question_id').execute()

            return result.data[0] if result.data else None
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase save_response error: {e}")
            raise SupabaseServiceError(f"Failed to save response: {str(e)}")

    def save_responses_batch(self, project_id: str, responses: list) -> list:
        """Save multiple question responses at once"""
        try:
            if not project_id:
                raise ValueError("Project ID is required")
            if not responses:
                return []

            data = []
            for r in responses:
                question_id = r.get('question_id')
                if not question_id:
                    continue

                data.append({
                    'project_id': project_id,
                    'question_id': question_id,
                    'response': r.get('response', ''),
                    'ai_suggested': bool(r.get('ai_suggested', False)),
                    'confirmed': bool(r.get('confirmed', False))
                })

            if not data:
                return []

            result = self.client.table('question_responses').upsert(
                data, on_conflict='project_id,question_id'
            ).execute()

            return result.data if result.data else []
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase save_responses_batch error: {e}")
            raise SupabaseServiceError(f"Failed to save responses batch: {str(e)}")

    def get_responses(self, project_id: str) -> list:
        """Get all responses for a project"""
        try:
            if not project_id:
                return []

            result = self.client.table('question_responses').select('*').eq('project_id', project_id).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Supabase get_responses error: {e}")
            return []

    def confirm_response(self, project_id: str, question_id: str, confirmed: bool = True) -> dict:
        """Mark a response as confirmed or unconfirmed"""
        try:
            if not project_id:
                raise ValueError("Project ID is required")
            if not question_id:
                raise ValueError("Question ID is required")

            result = self.client.table('question_responses').update({
                'confirmed': bool(confirmed)
            }).eq('project_id', project_id).eq('question_id', question_id).execute()

            return result.data[0] if result.data else None
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase confirm_response error: {e}")
            raise SupabaseServiceError(f"Failed to confirm response: {str(e)}")

    # PRD
    def save_prd(self, project_id: str, content_md: str) -> dict:
        """Save or update the PRD for a project"""
        try:
            if not project_id:
                raise ValueError("Project ID is required")
            if not content_md:
                raise ValueError("PRD content is required")

            # Delete existing PRD for this project first
            try:
                self.client.table('generated_prds').delete().eq('project_id', project_id).execute()
            except Exception as del_error:
                print(f"Warning: Error deleting existing PRD: {del_error}")

            result = self.client.table('generated_prds').insert({
                'project_id': project_id,
                'content_md': content_md
            }).execute()

            if not result.data:
                raise SupabaseServiceError("No data returned from database")

            return result.data[0]
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase save_prd error: {e}")
            raise SupabaseServiceError(f"Failed to save PRD: {str(e)}")

    def get_prd(self, project_id: str) -> dict:
        """Get the most recent PRD for a project"""
        try:
            if not project_id:
                return None

            result = self.client.table('generated_prds').select('*').eq('project_id', project_id).order('created_at', desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Supabase get_prd error: {e}")
            return None

    # File Storage
    def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> str:
        """Upload a file to Supabase storage"""
        try:
            if not bucket:
                raise ValueError("Bucket name is required")
            if not file_path:
                raise ValueError("File path is required")
            if not file_data:
                raise ValueError("File data is required")

            self.client.storage.from_(bucket).upload(file_path, file_data)
            url = self.client.storage.from_(bucket).get_public_url(file_path)
            return url
        except ValueError:
            raise
        except Exception as e:
            print(f"Supabase upload_file error: {e}")
            # Return None instead of raising - file upload failure shouldn't block metadata save
            return None

    def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete a file from Supabase storage"""
        try:
            if not bucket or not file_path:
                return False

            self.client.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            print(f"Supabase delete_file error: {e}")
            return False


# Singleton instance
try:
    supabase_service = SupabaseService()
except Exception as e:
    print(f"Warning: Supabase service initialization failed: {e}")
    supabase_service = None
