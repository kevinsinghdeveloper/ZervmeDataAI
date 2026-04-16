"""Base abstraction for OAuth/OIDC identity providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuthTokens:
    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int = 3600


@dataclass
class OAuthUserInfo:
    provider: str
    provider_user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class IOAuthProvider(ABC):
    """Base class for all OAuth/OIDC identity providers."""

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        pass

    @abstractmethod
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> OAuthTokens:
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        pass

    @abstractmethod
    def validate_id_token(self, id_token: str) -> dict:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
