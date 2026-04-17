import uuid
from django.db import models


class User(models.Model):
    DEFAULT_STORAGE_MAX = 21474836480  # 20 GB

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    storage_max = models.BigIntegerField(default=DEFAULT_STORAGE_MAX)
    storage_used = models.BigIntegerField(default=0)
    is_admin = models.BooleanField(default=False)

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.username


class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent_folder = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    weight = models.BigIntegerField(default=0)


class File(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    weight = models.BigIntegerField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    share_token = models.UUIDField(null=True, blank=True, unique=True)

    def generate_share_token(self):
        self.share_token = uuid.uuid4()
        return self.share_token
