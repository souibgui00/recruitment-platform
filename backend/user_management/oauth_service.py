import os
from typing import Optional, Dict, Any
from authlib.integrations.base_client import OAuthError
from authlib.integrations.requests_client import OAuth2Session
from sqlalchemy.orm import Session
from user_management.models import User
from user_management.security import hash_password, generate_verification_token, get_token_expiry
from datetime import datetime
import secrets

class OAuthService:
    def __init__(self):
        self.google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
        
        self.github_client_id = os.environ.get("GITHUB_CLIENT_ID")
        self.github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
        self.github_redirect_uri = os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/github/callback")

    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        if not self.google_client_id:
            raise ValueError("Google OAuth not configured")
        
        google = OAuth2Session(
            self.google_client_id,
            redirect_uri=self.google_redirect_uri,
            scope="openid email profile"
        )
        authorization_url, state = google.authorization_url(
            "https://accounts.google.com/o/oauth2/v2/auth"
        )
        return authorization_url

    def get_github_auth_url(self) -> str:
        """Generate GitHub OAuth authorization URL"""
        if not self.github_client_id:
            raise ValueError("GitHub OAuth not configured")
        
        github = OAuth2Session(
            self.github_client_id,
            redirect_uri=self.github_redirect_uri
        )
        authorization_url, state = github.authorization_url(
            "https://github.com/login/oauth/authorize"
        )
        return authorization_url

    def handle_google_callback(self, code: str, db: Session) -> User:
        """Handle Google OAuth callback"""
        if not self.google_client_id or not self.google_client_secret:
            raise ValueError("Google OAuth not configured")
        
        google = OAuth2Session(
            self.google_client_id,
            redirect_uri=self.google_redirect_uri
        )
        
        try:
            # Fetch the access token
            token = google.fetch_token(
                "https://oauth2.googleapis.com/token",
                code=code,
                client_secret=self.google_client_secret
            )
            
            # Get user info
            google = OAuth2Session(self.google_client_id, token=token)
            user_info = google.get("https://www.googleapis.com/oauth2/v3/userinfo")
            
            return self.get_or_create_oauth_user(
                db=db,
                provider="google",
                oauth_id=user_info["id"],
                email=user_info["email"],
                full_name=user_info.get("name"),
                avatar_url=user_info.get("picture")
            )
            
        except OAuthError as e:
            raise ValueError(f"Google OAuth error: {str(e)}")

    def handle_github_callback(self, code: str, db: Session) -> User:
        """Handle GitHub OAuth callback"""
        if not self.github_client_id or not self.github_client_secret:
            raise ValueError("GitHub OAuth not configured")
        
        github = OAuth2Session(
            self.github_client_id,
            redirect_uri=self.github_redirect_uri
        )
        
        try:
            # Fetch the access token
            token = github.fetch_token(
                "https://github.com/login/oauth/access_token",
                code=code,
                client_secret=self.github_client_secret
            )
            
            # Get user info
            github = OAuth2Session(self.github_client_id, token=token)
            user_info = github.get("https://api.github.com/user")
            
            # Get user email (GitHub requires separate call for email)
            email_info = github.get("https://api.github.com/user/emails")
            primary_email = next((e["email"] for e in email_info if e["primary"] and e["verified"]), None)
            
            if not primary_email:
                raise ValueError("No verified email found from GitHub")
            
            return self.get_or_create_oauth_user(
                db=db,
                provider="github",
                oauth_id=str(user_info["id"]),
                email=primary_email,
                full_name=user_info.get("name"),
                avatar_url=user_info.get("avatar_url")
            )
            
        except OAuthError as e:
            raise ValueError(f"GitHub OAuth error: {str(e)}")

    def get_or_create_oauth_user(
        self, 
        db: Session, 
        provider: str, 
        oauth_id: str, 
        email: str, 
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """Get existing OAuth user or create new one"""
        # Check if user exists with this OAuth provider and ID
        user = db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id
        ).first()
        
        if user:
            # Update user info if needed
            if not user.is_active:
                user.is_active = True
            if full_name and not user.full_name:
                user.full_name = full_name
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user
        
        # Check if email is already used by another account
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.oauth_provider == provider and existing_user.oauth_id == oauth_id:
                return existing_user
            else:
                raise ValueError("Email already associated with another account")
        
        # Create new user
        verification_token = generate_verification_token()
        verification_expires = get_token_expiry(hours=24)
        
        new_user = User(
            email=email,
            hashed_password=None,  # OAuth users don't have passwords
            full_name=full_name,
            avatar_url=avatar_url,
            oauth_provider=provider,
            oauth_id=oauth_id,
            is_verified=True,  # OAuth emails are pre-verified
            verification_token=verification_token,
            verification_expires=verification_expires
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user

# Singleton instance
oauth_service = OAuthService()