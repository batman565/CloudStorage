import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions, permissions

from .models import User

logger = logging.getLogger('cloudstorage')


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, AttributeError):
        return False


def encode_token(username: str, is_admin: bool):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': username,
        'is_admin': bool(is_admin),
        'exp': int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth.startswith(self.keyword + ' '):
            return None
        token = auth[len(self.keyword) + 1:].strip()
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            logger.warning('Auth: token expired')
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            logger.warning('Auth: invalid token')
            raise exceptions.AuthenticationFailed('Invalid token')

        username = payload.get('sub')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        user.is_admin = bool(payload.get('is_admin', user.is_admin))
        return (user, token)

    def authenticate_header(self, request):
        return self.keyword


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request.user, 'is_admin', False))
