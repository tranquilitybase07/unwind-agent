"""
JWT Authentication handler for Unwind AI Assistant.

Validates Supabase JWT tokens and extracts user_id (auth.uid())
to ensure RLS compliance for all database queries.
"""

import os
import logging
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError
)

logger = logging.getLogger(__name__)


class AuthHandler:
    """
    Handles JWT token validation and user_id extraction from Supabase auth tokens.

    Supabase uses JWT tokens with the following structure:
    {
        "sub": "user-uuid",  # This is the user_id (auth.uid())
        "email": "user@example.com",
        "role": "authenticated",
        ...
    }
    """

    def __init__(self):
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
        self.supabase_url = os.getenv('SUPABASE_URL')

        if not self.jwt_secret:
            logger.warning(
                "SUPABASE_JWT_SECRET not set. JWT validation will fail. "
                "Get this from Supabase Dashboard -> Settings -> API -> JWT Secret"
            )

    def extract_user_id(self, authorization_header: Optional[str]) -> Optional[str]:
        """
        Extract user_id from Authorization header.

        Args:
            authorization_header: HTTP Authorization header value (e.g., "Bearer eyJ...")

        Returns:
            User ID (UUID string) if valid, None otherwise
        """
        if not authorization_header:
            logger.warning("No Authorization header provided")
            return None

        # Extract token from "Bearer <token>" format
        parts = authorization_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning(f"Invalid Authorization header format: {authorization_header[:20]}...")
            return None

        token = parts[1]
        return self.validate_token(token)

    def validate_token(self, token: str) -> Optional[str]:
        """
        Validate JWT token and extract user_id.

        Args:
            token: JWT token string

        Returns:
            User ID if token is valid, None otherwise
        """
        if not self.jwt_secret:
            logger.error("Cannot validate token: SUPABASE_JWT_SECRET not configured")
            return None

        try:
            # Decode and verify the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],  # Supabase uses HS256
                options={
                    'verify_signature': True,
                    'verify_exp': True,  # Check expiration
                    'verify_iat': True,  # Check issued at
                }
            )

            # Extract user_id from 'sub' claim (subject)
            user_id = payload.get('sub')
            if not user_id:
                logger.warning("Token payload missing 'sub' claim")
                return None

            logger.debug(f"Token validated for user: {user_id}")
            return user_id

        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except InvalidSignatureError:
            logger.warning("Invalid token signature")
            return None
        except DecodeError as e:
            logger.warning(f"Token decode error: {e}")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return None

    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token WITHOUT verification (for debugging/testing only).

        WARNING: Do NOT use this in production! Always use validate_token() instead.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload as dictionary
        """
        try:
            payload = jwt.decode(
                token,
                options={'verify_signature': False}  # UNSAFE!
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None

    def create_service_context(self, user_id: str) -> Dict[str, str]:
        """
        Create a context dictionary for service-to-service calls.

        This can be used when agents need to make authenticated requests
        on behalf of a user.

        Args:
            user_id: User ID to create context for

        Returns:
            Dictionary with user_id for service context
        """
        return {
            'user_id': user_id,
            'role': 'service',
        }


# Global auth handler instance
auth_handler = AuthHandler()


def get_user_id_from_header(authorization_header: Optional[str]) -> Optional[str]:
    """
    Convenience function to extract user_id from Authorization header.

    Args:
        authorization_header: HTTP Authorization header value

    Returns:
        User ID if valid, None otherwise
    """
    return auth_handler.extract_user_id(authorization_header)


def validate_jwt_token(token: str) -> Optional[str]:
    """
    Convenience function to validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise
    """
    return auth_handler.validate_token(token)
