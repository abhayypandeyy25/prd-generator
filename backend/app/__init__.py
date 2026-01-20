from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    # Check if we're serving static files (production)
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    if os.path.exists(static_folder):
        app = Flask(__name__, static_folder=static_folder, static_url_path='')
    else:
        app = Flask(__name__)

    # Allow CORS from all origins in production (since frontend is served from same domain)
    # In development, allow localhost
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:5001",
        "*"  # Allow all in production since same domain
    ]

    # Add custom domain from environment variable if set
    frontend_url = os.getenv('FRONTEND_URL')
    if frontend_url:
        allowed_origins.append(frontend_url)

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

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'pm-clarity'}

    # Serve frontend in production
    if os.path.exists(static_folder):
        @app.route('/')
        def serve_index():
            return send_from_directory(app.static_folder, 'index.html')

        @app.route('/<path:path>')
        def serve_static(path):
            # Check if the file exists in static folder
            if os.path.exists(os.path.join(app.static_folder, path)):
                return send_from_directory(app.static_folder, path)
            # Otherwise serve index.html for SPA routing
            return send_from_directory(app.static_folder, 'index.html')

    return app
