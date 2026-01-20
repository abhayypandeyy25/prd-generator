import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # File upload settings
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xlsx', 'md', 'eml', 'csv'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    # Claude settings
    CLAUDE_MODEL = 'claude-3-5-sonnet-20241022'
    MAX_TOKENS = 8192
