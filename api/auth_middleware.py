"""
Firebase Authentication Middleware for PM Clarity API

This module provides authentication verification for all API endpoints
using Firebase Admin SDK to verify ID tokens from the frontend.
"""

import os
import json

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Warning: firebase-admin not installed. Authentication disabled.")

# Initialize Firebase Admin SDK (only once)
_firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    global _firebase_initialized

    if not FIREBASE_AVAILABLE:
        return False

    if _firebase_initialized:
        return True

    if firebase_admin._apps:
        _firebase_initialized = True
        return True

    try:
        # Get credentials from environment variables
        private_key = os.environ.get('FIREBASE_PRIVATE_KEY', '')
        # Handle escaped newlines in environment variable
        if private_key:
            private_key = private_key.replace('\\n', '\n')

        cred_dict = {
            "type": "service_account",
            "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
            "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": private_key,
            "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        }

        # Validate required fields
        required_fields = ['project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [f for f in required_fields if not cred_dict.get(f)]

        if missing_fields:
            print(f"Warning: Missing Firebase credentials: {missing_fields}")
            return False

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("Firebase Admin SDK initialized successfully")
        return True

    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        return False


def verify_token(id_token):
    """
    Verify a Firebase ID token and return the user's UID.

    Args:
        id_token: The Firebase ID token from the frontend

    Returns:
        The user's UID if valid, None otherwise
    """
    if not FIREBASE_AVAILABLE:
        return None

    if not initialize_firebase():
        return None

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token['uid']
    except firebase_auth.InvalidIdTokenError:
        print("Invalid ID token")
        return None
    except firebase_auth.ExpiredIdTokenError:
        print("Expired ID token")
        return None
    except firebase_auth.RevokedIdTokenError:
        print("Revoked ID token")
        return None
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def get_user_from_request(handler):
    """
    Extract and verify the Firebase ID token from the request headers.

    Args:
        handler: The HTTP request handler with headers

    Returns:
        The user's UID if authenticated, None otherwise
    """
    auth_header = handler.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return None

    id_token = auth_header[7:]  # Remove 'Bearer ' prefix
    return verify_token(id_token)


def require_auth(handler_method):
    """
    Decorator to require authentication for API endpoints.

    Usage:
        @require_auth
        def do_GET(self):
            # self.user_id is now available
            ...

    If authentication fails, returns 401 Unauthorized response.
    """
    def wrapper(self):
        user_id = get_user_from_request(self)

        if not user_id:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Unauthorized',
                'message': 'Please sign in to continue'
            }).encode())
            return

        # Store user_id for use in the handler
        self.user_id = user_id
        return handler_method(self)

    return wrapper


def get_user_id_for_query(handler):
    """
    Get the user_id for database queries.
    Returns None if not authenticated (for optional auth endpoints).

    Usage:
        user_id = get_user_id_for_query(self)
        if user_id:
            # Filter by user
            query = query.eq('user_id', user_id)
    """
    return get_user_from_request(handler)


# For testing/development - allow bypass if no Firebase configured
def is_auth_enabled():
    """Check if authentication is properly configured."""
    if not FIREBASE_AVAILABLE:
        return False

    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY_ID',
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_CLIENT_ID'
    ]

    return all(os.environ.get(var) for var in required_vars)
