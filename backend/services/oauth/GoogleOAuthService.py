"""Google OAuth 2.0 + OIDC provider implementation."""
import os
import requests
from abstractions.IOAuthProvider import IOAuthProvider, OAuthTokens, OAuthUserInfo


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthService(IOAuthProvider):
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
        self.enabled = os.getenv("GOOGLE_OAUTH_ENABLED", "false").lower() == "true"

    @property
    def provider_name(self) -> str:
        return "google"

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> OAuthTokens:
        response = requests.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        return OAuthTokens(
            access_token=data["access_token"],
            id_token=data.get("id_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 3600),
        )

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        response = requests.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}",
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        return OAuthUserInfo(
            provider="google",
            provider_user_id=data["sub"],
            email=data["email"],
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            avatar_url=data.get("picture"),
        )

    def validate_id_token(self, id_token: str) -> dict:
        response = requests.get(f"{GOOGLE_TOKENINFO_URL}?id_token={id_token}", timeout=10)
        response.raise_for_status()
        return response.json()
