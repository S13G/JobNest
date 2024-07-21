from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin


class CurrentUserMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        if request.user.is_authenticated:
            request.current_user = request.user
        else:
            request.current_user = AnonymousUser()
