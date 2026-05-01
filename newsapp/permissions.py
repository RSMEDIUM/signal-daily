"""Custom permissions for Signal Daily role-based API authorization."""

from rest_framework import permissions


class IsJournalist(permissions.BasePermission):
    """Allow only authenticated journalists to access the view."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'journalist'


class IsEditor(permissions.BasePermission):
    """Allow only authenticated editors to access the view."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'editor'


class IsEditorOrJournalist(permissions.BasePermission):
    """Allow editors or journalists to modify or delete content."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['editor', 'journalist']

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.role == 'editor':
            return True
        return obj.author == request.user


class IsReaderOrReadOnly(permissions.BasePermission):
    """Allow authenticated readers to view content but prevent writes."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return False
