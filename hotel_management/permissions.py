from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAdminUser, IsAuthenticated


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


IsAdminOrReadOnly = ReadOnly | (IsAuthenticated & IsAdminUser)
