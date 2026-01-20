from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Allow CORS from localhost (dev) and Vercel domains (production)
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Add Vercel domain from environment variable if set
    frontend_url = os.getenv('FRONTEND_URL')
    if frontend_url:
        allowed_origins.append(frontend_url)

    # Also allow any vercel.app subdomain for preview deployments
    CORS(app, origins=allowed_origins, supports_credentials=True, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
    app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
    app.config['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY')

    # Register blueprints
    from app.routes.context import context_bp
    from app.routes.questions import questions_bp
    from app.routes.prd import prd_bp
    from app.routes.projects import projects_bp

    app.register_blueprint(context_bp, url_prefix='/api/context')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(prd_bp, url_prefix='/api/prd')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')

    return app
