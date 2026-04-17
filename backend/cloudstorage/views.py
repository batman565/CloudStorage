import logging
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import FileResponse, Http404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import IsAdmin, encode_token, hash_password, verify_password
from .models import File, Folder, User
from .serializers import (
    AdminUserPatchSerializer,
    FileUpdateSerializer,
    FolderCreateSerializer,
    FolderUpdateSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from .utils import (
    calculate_folder_weight,
    folder_contents,
    gather_descendants,
    update_parent_weights,
)

logger = logging.getLogger('cloudstorage')


# ---------- AUTH / USER ----------

class TokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=400)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning('Login failed: unknown user %s', username)
            return Response({'detail': 'Incorrect username or password'}, status=401)
        if not verify_password(password, user.password):
            logger.warning('Login failed: bad password for %s', username)
            return Response({'detail': 'Incorrect username or password'}, status=401)
        token, expires_at = encode_token(user.username, user.is_admin)
        logger.info('Login ok: %s', username)
        return Response({
            'access_token': token,
            'token_type': 'bearer',
            'expired': expires_at.isoformat(),
        })


class UserCreateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors), 'errors': serializer.errors}, status=400)
        data = serializer.validated_data
        if User.objects.filter(username=data['username']).exists() or User.objects.filter(email=data['email']).exists():
            return Response({'detail': 'Username or email already registered'}, status=400)
        with transaction.atomic():
            user = User.objects.create(
                username=data['username'],
                email=data['email'],
                password=hash_password(data['password']),
                is_admin=False,
            )
            Folder.objects.create(name='disk', parent_folder=None, user=user)
        token, expires_at = encode_token(user.username, user.is_admin)
        logger.info('User registered: %s', user.username)
        return Response({
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'access_token': token,
            'token_type': 'bearer',
            'expire': expires_at.isoformat(),
        })


class UserMeView(APIView):
    def get(self, request):
        u = request.user
        return Response({
            'username': u.username,
            'email': u.email,
            'storage_max': u.storage_max,
            'storage_used': u.storage_used,
            'is_admin': u.is_admin,
        })

    def patch(self, request):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors), 'errors': serializer.errors}, status=400)
        u = request.user
        data = serializer.validated_data
        if 'password' in data:
            u.password = hash_password(data.pop('password'))
        for field, value in data.items():
            setattr(u, field, value)
        u.save()
        logger.info('User updated: %s', u.username)
        return Response({'username': u.username, 'email': u.email, 'is_admin': u.is_admin})


def _flat_errors(errors):
    parts = []
    for field, msgs in errors.items():
        if isinstance(msgs, list):
            parts.append(f'{field}: {msgs[0]}')
        else:
            parts.append(f'{field}: {msgs}')
    return '; '.join(parts)


# ---------- FOLDERS ----------

class DiskView(APIView):
    def get(self, request):
        root = Folder.objects.filter(user=request.user, parent_folder__isnull=True).first()
        if not root:
            root = Folder.objects.create(name='disk', user=request.user, parent_folder=None)
        return Response(folder_contents(request.user, root))


class FolderView(APIView):
    def get(self, request, idfolder):
        folder = _get_user_folder(request.user, idfolder)
        return Response(folder_contents(request.user, folder))

    def post(self, request, idfolder):
        parent = _get_user_folder(request.user, idfolder)
        serializer = FolderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors)}, status=400)
        name = serializer.validated_data['name']
        if Folder.objects.filter(user=request.user, parent_folder=parent, name=name).exists():
            return Response({'detail': 'Folder already exists'}, status=400)
        new_folder = Folder.objects.create(name=name, user=request.user, parent_folder=parent)
        logger.info('Folder created: id=%s name=%s parent=%s user=%s', new_folder.id, name, parent.id, request.user.username)
        return Response({
            'id': new_folder.id,
            'name': new_folder.name,
            'parent_id': parent.id,
            'status': 'created',
        })

    def delete(self, request, idfolder):
        folder = _get_user_folder(request.user, idfolder)
        with transaction.atomic():
            all_folders, all_files = gather_descendants(folder)
            total_size = sum(f.weight for f in all_files)
            for f in all_files:
                try:
                    if f.path and os.path.exists(f.path):
                        os.remove(f.path)
                except OSError as e:
                    logger.error('Failed to remove file %s: %s', f.path, e)
            folder.delete()  # cascades in DB
            user = request.user
            user.storage_used = max(0, (user.storage_used or 0) - total_size)
            user.save(update_fields=['storage_used'])
            if folder.parent_folder_id and total_size:
                parent = Folder.objects.filter(id=folder.parent_folder_id).first()
                if parent is not None:
                    update_parent_weights(parent, -total_size)
        logger.info('Folder deleted: id=%s user=%s freed=%s', idfolder, request.user.username, total_size)
        return Response({'code': 200, 'status': 'Deleted'})

    def patch(self, request, idfolder):
        target = _get_user_folder(request.user, idfolder)
        serializer = FolderUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors)}, status=400)
        data = serializer.validated_data
        old_parent = target.parent_folder
        old_weight = calculate_folder_weight(target)
        new_parent = old_parent
        if 'parent_folder_id' in data:
            new_parent_id = data['parent_folder_id']
            if new_parent_id is None:
                return Response({'detail': 'Cannot move to no parent'}, status=400)
            new_parent = _get_user_folder(request.user, new_parent_id)
            cur = new_parent
            while cur is not None:
                if cur.id == target.id:
                    return Response({'detail': 'Cannot move folder to its own subfolder'}, status=400)
                cur = cur.parent_folder
        new_name = data.get('name', target.name)
        conflict = Folder.objects.filter(
            user=request.user, parent_folder=new_parent, name=new_name
        ).exclude(id=target.id).exists()
        if conflict:
            return Response({'detail': 'Folder with this name already exists in target directory'}, status=400)
        with transaction.atomic():
            if old_parent and (not new_parent or new_parent.id != old_parent.id):
                update_parent_weights(old_parent, -old_weight)
            if new_parent and (not old_parent or new_parent.id != old_parent.id):
                update_parent_weights(new_parent, old_weight)
            if 'name' in data:
                target.name = data['name']
            if 'parent_folder_id' in data:
                target.parent_folder = new_parent
            target.save()
        logger.info('Folder updated: id=%s user=%s', idfolder, request.user.username)
        return Response({'id': target.id, 'name': target.name, 'parent_folder_id': target.parent_folder_id})


class ResolvePathView(APIView):
    def get(self, request, path):
        parts = [p for p in path.split('/') if p]
        parent = None
        for name in parts:
            folder = Folder.objects.filter(user=request.user, name=name, parent_folder=parent).first()
            if not folder:
                return Response({'detail': 'Folder not found'}, status=404)
            parent = folder
        return Response({'folder_id': parent.id if parent else None})


def _get_user_folder(user, folder_id):
    folder = Folder.objects.filter(id=folder_id, user=user).first()
    if not folder:
        raise Http404('Folder not found')
    return folder


# ---------- FILES ----------

class FileUploadView(APIView):
    def post(self, request, folderid):
        folder = _get_user_folder(request.user, folderid)
        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': 'No file provided'}, status=400)
        size = upload.size
        user = request.user
        if (user.storage_used or 0) + size > user.storage_max:
            return Response({'detail': 'Not enough storage space'}, status=400)
        if File.objects.filter(folder=folder, name=upload.name).exists():
            return Response({'detail': 'File is exist'}, status=409)
        file_id = str(uuid.uuid4())
        file_path = Path(settings.STORAGE_PATH) / file_id
        try:
            with open(file_path, 'wb') as out:
                for chunk in upload.chunks():
                    out.write(chunk)
            with transaction.atomic():
                File.objects.create(
                    name=upload.name,
                    path=str(file_path),
                    weight=size,
                    owner=user,
                    folder=folder,
                )
                user.storage_used = (user.storage_used or 0) + size
                user.save(update_fields=['storage_used'])
                update_parent_weights(folder, size)
        except Exception as e:
            logger.exception('Upload failed for user %s: %s', user.username, e)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
            return Response({'detail': str(e)}, status=500)
        logger.info('File uploaded: %s (%s bytes) user=%s folder=%s', upload.name, size, user.username, folder.id)
        return Response({'Status': f'File {file_id} created', 'Code': '200'})


class FileDownloadView(APIView):
    def get(self, request, file_id):
        f = File.objects.filter(id=file_id, owner=request.user).first()
        if not f:
            return Response({'detail': 'File not found'}, status=404)
        if not os.path.exists(f.path):
            f.delete()
            return Response({'detail': 'File not detected in storage, file was deleted from DB'}, status=404)
        return FileResponse(open(f.path, 'rb'), as_attachment=True, filename=f.name)


class FileDeleteView(APIView):
    def delete(self, request, file_id):
        f = File.objects.filter(id=file_id, owner=request.user).first()
        if not f:
            return Response({'detail': 'File not found'}, status=404)
        folder = f.folder
        size = f.weight
        with transaction.atomic():
            try:
                if os.path.exists(f.path):
                    os.remove(f.path)
            except OSError as e:
                logger.error('Failed to remove file %s: %s', f.path, e)
            f.delete()
            user = request.user
            user.storage_used = max(0, (user.storage_used or 0) - size)
            user.save(update_fields=['storage_used'])
            if folder:
                update_parent_weights(folder, -size)
        logger.info('File deleted: id=%s user=%s', file_id, request.user.username)
        return Response(status=204)


class FileUpdateView(APIView):
    def patch(self, request, file_id):
        f = File.objects.filter(id=file_id, owner=request.user).first()
        if not f:
            return Response({'detail': 'File not found'}, status=404)
        serializer = FileUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors)}, status=400)
        data = serializer.validated_data
        old_folder = f.folder
        new_folder = old_folder
        if 'parent_folder_id' in data:
            new_folder_id = data['parent_folder_id']
            if new_folder_id is None:
                return Response({'detail': 'Folder is required'}, status=400)
            new_folder = _get_user_folder(request.user, new_folder_id)
        new_name = data.get('name', f.name)
        conflict = File.objects.filter(
            owner=request.user, folder=new_folder, name=new_name
        ).exclude(id=f.id).exists()
        if conflict:
            return Response({'detail': 'File with this name already exists in target directory'}, status=400)
        with transaction.atomic():
            if old_folder and new_folder and old_folder.id != new_folder.id:
                update_parent_weights(old_folder, -f.weight)
                update_parent_weights(new_folder, f.weight)
            if 'name' in data:
                f.name = data['name']
            if 'parent_folder_id' in data:
                f.folder = new_folder
            f.save()
        logger.info('File updated: id=%s user=%s', file_id, request.user.username)
        return Response({'id': f.id, 'name': f.name, 'folder_id': f.folder_id})


# ---------- SHARE ----------

class FileShareView(APIView):
    def post(self, request, file_id):
        f = File.objects.filter(id=file_id, owner=request.user).first()
        if not f:
            return Response({'detail': 'File not found'}, status=404)
        if not f.share_token:
            f.generate_share_token()
            f.save(update_fields=['share_token'])
        url = f'{settings.PUBLIC_BASE_URL.rstrip("/")}/api/public/download/{f.share_token}'
        logger.info('Share link issued: file=%s user=%s', file_id, request.user.username)
        return Response({'share_token': str(f.share_token), 'url': url})


class PublicDownloadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            uuid.UUID(str(token))
        except (ValueError, AttributeError):
            return Response({'detail': 'Invalid token'}, status=404)
        f = File.objects.filter(share_token=token).first()
        if not f or not os.path.exists(f.path):
            return Response({'detail': 'File not found'}, status=404)
        logger.info('Public download: token=%s file=%s', token, f.id)
        return FileResponse(open(f.path, 'rb'), as_attachment=True, filename=f.name)


# ---------- ADMIN ----------

class AdminUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by('id')
        result = []
        for u in users:
            files_qs = File.objects.filter(owner=u)
            result.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'is_admin': u.is_admin,
                'storage_max': u.storage_max,
                'storage_used': u.storage_used,
                'files_count': files_qs.count(),
                'files_size': sum(files_qs.values_list('weight', flat=True)) or 0,
            })
        return Response(result)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        target = User.objects.filter(id=user_id).first()
        if not target:
            return Response({'detail': 'User not found'}, status=404)
        serializer = AdminUserPatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': _flat_errors(serializer.errors)}, status=400)
        target.is_admin = serializer.validated_data['is_admin']
        target.save(update_fields=['is_admin'])
        logger.info('Admin %s set is_admin=%s for user %s', request.user.username, target.is_admin, target.username)
        return Response({'id': target.id, 'username': target.username, 'is_admin': target.is_admin})

    def delete(self, request, user_id):
        target = User.objects.filter(id=user_id).first()
        if not target:
            return Response({'detail': 'User not found'}, status=404)
        if target.id == request.user.id:
            return Response({'detail': 'Cannot delete yourself'}, status=400)
        files = list(File.objects.filter(owner=target))
        for f in files:
            try:
                if f.path and os.path.exists(f.path):
                    os.remove(f.path)
            except OSError as e:
                logger.error('Admin delete: cannot remove %s: %s', f.path, e)
        username = target.username
        target.delete()
        logger.info('Admin %s deleted user %s', request.user.username, username)
        return Response(status=204)


class AdminUserStorageView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        target = User.objects.filter(id=user_id).first()
        if not target:
            return Response({'detail': 'User not found'}, status=404)
        folder_id = request.query_params.get('folder_id')
        if folder_id:
            folder = Folder.objects.filter(id=folder_id, user=target).first()
        else:
            folder = Folder.objects.filter(user=target, parent_folder__isnull=True).first()
        if not folder:
            return Response({'detail': 'Folder not found'}, status=404)
        data = folder_contents(target, folder)
        data['owner'] = {'id': target.id, 'username': target.username}
        return Response(data)
