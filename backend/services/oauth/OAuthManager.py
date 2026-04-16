"""OAuth provider registry - maps provider names to IOAuthProvider instances."""
from typing import Dict, List, Optional
from abstractions.IOAuthProvider import IOAuthProvider
from services.oauth.GoogleOAuthService import GoogleOAuthService
from services.oauth.AzureADOAuthService import AzureADOAuthService


class OAuthManager:
    def __init__(self):
        self._providers: Dict[str, IOAuthProvider] = {}
        self._register_providers()

    def _register_providers(self):
        google = GoogleOAuthService()
        if google.enabled:
            self._providers["google"] = google

        azure = AzureADOAuthService()
        if azure.enabled:
            self._providers["azure_ad"] = azure

    def get_provider(self, name: str) -> Optional[IOAuthProvider]:
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def is_provider_enabled(self, name: str) -> bool:
        return name in self._providers
