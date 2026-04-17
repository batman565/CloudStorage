from django.urls import re_path

from . import views


def _r(pattern, view, **kw):
    """Register a URL with an optional trailing slash (frontend is inconsistent)."""
    if not pattern.endswith('$'):
        pattern = pattern + '/?$'
    return re_path(pattern, view, **kw)


urlpatterns = [
    _r(r'^api/token',                                 views.TokenView.as_view()),

    _r(r'^api/user/create',                           views.UserCreateView.as_view()),
    _r(r'^api/user',                                  views.UserMeView.as_view()),

    _r(r'^api/admin/users/(?P<user_id>\d+)/storage',  views.AdminUserStorageView.as_view()),
    _r(r'^api/admin/users/(?P<user_id>\d+)',          views.AdminUserDetailView.as_view()),
    _r(r'^api/admin/users',                           views.AdminUsersView.as_view()),

    _r(r'^api/client/disk',                           views.DiskView.as_view()),
    _r(r'^api/client/folder/(?P<idfolder>\d+)',       views.FolderView.as_view()),

    re_path(r'^api/resolve-path/(?P<path>.+)$',       views.ResolvePathView.as_view()),

    _r(r'^api/file/upload/(?P<folderid>\d+)',         views.FileUploadView.as_view()),
    _r(r'^api/file/download/(?P<file_id>\d+)',        views.FileDownloadView.as_view()),
    _r(r'^api/file/delete/(?P<file_id>\d+)',          views.FileDeleteView.as_view()),
    _r(r'^api/file/update/(?P<file_id>\d+)',          views.FileUpdateView.as_view()),
    _r(r'^api/file/(?P<file_id>\d+)/share',           views.FileShareView.as_view()),

    _r(r'^api/public/download/(?P<token>[0-9a-f-]+)', views.PublicDownloadView.as_view()),
]
