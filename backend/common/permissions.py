from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwner(BasePermission):
    """Only business owners may access this view."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'owner'
        )


class IsOwnerOrStaff(BasePermission):
    """Owners and staff may access this view."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('owner', 'staff')
        )


class IsOwnerOrReadOnly(BasePermission):
    """Owners have full access; staff may only read."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return request.user.role in ('owner', 'staff')
        return request.user.role == 'owner'
