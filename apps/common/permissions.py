from rest_framework.permissions import BasePermission


class IsAuthenticatedEmployee(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, "employee_profile")
        )


class IsAuthenticatedCompany(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, "company_profile")
        )
