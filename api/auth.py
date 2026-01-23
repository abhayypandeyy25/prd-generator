"""
Firebase Authentication Helper Module

Provides Firebase ID token verification for API endpoints.
Uses lightweight JWT verification instead of heavy Firebase Admin SDK.
"""

import os
import json
import time

# Use PyJWT for lightweight token verification
try:
    import jwt
    from jwt import PyJWKClient
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: PyJWT not installed. Auth will be disabled.")

# Cache for Google's public keys
_jwk_client = None
_jwk_client_initialized = False


def get_jwk_client():
    """Get or create JWK client for Google's public keys (singleton)."""
    global _jwk_client, _jwk_client_initialized

    if _jwk_client_initialized:
        return _jwk_client

    try:
        # Google's public key endpoint for Firebase tokens
        _jwk_client = PyJWKClient(
            "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com",
            cache_keys=True
        )
        _jwk_client_initialized = True
        return _jwk_client
    except Exception as e:
        print(f"Failed to initialize JWK client: {e}")
        _jwk_client_initialized = True
        return None


def verify_token(request_handler):
    """
    Verify Firebase ID token from Authorization header.

    Uses lightweight JWT verification with Google's public keys.

    Args:
        request_handler: HTTP request handler with headers attribute

    Returns:
        str: User ID (uid) if token is valid
        None: If token is missing, invalid, or verification fails
    """
    if not JWT_AVAILABLE:
        print("PyJWT not available - auth disabled")
        return None

    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    if not project_id:
        print("FIREBASE_PROJECT_ID not configured")
        return None

    try:
        # Extract Authorization header
        auth_header = request_handler.headers.get('Authorization', '')

        if not auth_header:
            return None

        if not auth_header.startswith('Bearer '):
            return None

        # Extract token (remove 'Bearer ' prefix)
        token = auth_header[7:]

        if not token:
            return None

        # Get the JWK client
        jwk_client = get_jwk_client()
        if not jwk_client:
            print("JWK client not available")
            return None

        # Get the signing key from Google's public keys
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        # Verify the token
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True
            }
        )

        # Additional validation per Firebase requirements
        # Check auth_time is in the past
        auth_time = decoded_token.get('auth_time')
        if auth_time and auth_time > time.time():
            print("auth_time is in the future")
            return None

        # Check sub (user ID) exists and matches uid
        sub = decoded_token.get('sub')
        uid = decoded_token.get('user_id', sub)

        if not sub or not uid:
            print("Missing sub or user_id in token")
            return None

        return uid

    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidAudienceError:
        print("Invalid audience")
        return None
    except jwt.InvalidIssuerError:
        print("Invalid issuer")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def get_user_info(user_id):
    """
    Get user information from token (limited without Admin SDK).

    Note: Without Firebase Admin SDK, we can't fetch additional user info.
    This function is provided for API compatibility.

    Args:
        user_id: Firebase user ID

    Returns:
        dict: Basic user info
    """
    return {
        'uid': user_id,
        'email': None,
        'display_name': None
    }
