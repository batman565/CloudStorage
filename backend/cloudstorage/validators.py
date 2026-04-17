import re

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PASSWORD_RE = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$')


def validate_username(value: str):
    if not USERNAME_RE.match(value or ''):
        raise ValueError('Username must be 3-30 chars (letters, numbers, _)')


def validate_email(value: str):
    if not EMAIL_RE.match(value or ''):
        raise ValueError('Invalid email format')


def validate_password(value: str):
    if not PASSWORD_RE.match(value or ''):
        raise ValueError('Password must contain: 8+ chars, 1 uppercase, 1 number, 1 special symbol (!@#$%^&*)')
