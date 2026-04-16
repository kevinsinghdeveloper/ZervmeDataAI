"""Azure AD OAuth 2.0 + OIDC provider - SCAFFOLD (not yet implemented)."""
import os
from abstractions.IOAuthProvider import IOAuthProvider, OAuthTokens, OAuthUserInfo


class AzureADOAuthService(IOAuthProvider):
    """Scaffolded Azure AD OAuth provider. Enable after tenant configuration."""

    def __init__(self):
        self.client_id = os.getenv("AZURE_AD_CLIENT_ID", "")
        self.client_secret = os.getenv("AZURE_AD_CLIENT_SECRET", "")
        self.tenant_id = os.getenv("AZURE_AD_TENANT_ID", "")
        self.enabled = os.getenv("AZURE_AD_ENABLED", "false").lower() == "true"

    @property
    def provider_name(self) -> str:
        return "azure_ad"

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError("Azure AD integration pending tenant configuration")

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> OAuthTokens:
        raise NotImplementedError("Azure AD integration pending tenant configuration")

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        raise NotImplementedError("Azure AD integration pending tenant configuration")

    def validate_id_token(self, id_token: str) -> dict:
        raise NotImplementedError("Azure AD integration pending tenant configuration")
