from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions


class APIKeyUser(AnonymousUser):
    """Trivial user object that always counts as authenticated."""

    @property
    def is_authenticated(self) -> bool:  # pragma: no cover - simple property
        return True


class APIKeyAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request) -> Optional[Tuple[AnonymousUser, None]]:
        auth_header = authentication.get_authorization_header(request).decode()
        if not auth_header:
            raise exceptions.AuthenticationFailed("Authorization header required")

        try:
            keyword, token = auth_header.split(" ", 1)
        except ValueError as exc:
            raise exceptions.AuthenticationFailed("Invalid authorization header") from exc

        if keyword != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid authorization scheme")

        expected_token = getattr(settings, "BFL_CORE_API_TOKEN", "")
        if not expected_token or token != expected_token:
            raise exceptions.AuthenticationFailed("Invalid API token")

        return APIKeyUser(), None
