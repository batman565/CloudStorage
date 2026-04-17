from rest_framework import serializers

from .validators import validate_email, validate_password, validate_username


def _drf_validator(fn):
    """Adapt a plain validator (raises ValueError) to a DRF validator (raises ValidationError)."""
    def _inner(value):
        try:
            fn(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    return _inner


USERNAME_VALIDATORS = [_drf_validator(validate_username)]
EMAIL_VALIDATORS = [_drf_validator(validate_email)]
PASSWORD_VALIDATORS = [_drf_validator(validate_password)]


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(validators=USERNAME_VALIDATORS)
    email = serializers.CharField(validators=EMAIL_VALIDATORS)
    password = serializers.CharField(validators=PASSWORD_VALIDATORS)


class UserUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, validators=USERNAME_VALIDATORS)
    email = serializers.CharField(required=False, validators=EMAIL_VALIDATORS)
    password = serializers.CharField(required=False, validators=PASSWORD_VALIDATORS)


class FolderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class FolderUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    parent_folder_id = serializers.IntegerField(required=False, allow_null=True)


class FileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    parent_folder_id = serializers.IntegerField(required=False, allow_null=True)


class AdminUserPatchSerializer(serializers.Serializer):
    is_admin = serializers.BooleanField()
