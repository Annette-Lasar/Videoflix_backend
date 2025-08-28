from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that reads the JWT access token from HttpOnly cookies.

    Skips authentication for admin routes. For all other requests, the token
    is injected into the Authorization header before delegating to the parent
    JWTAuthentication class.
    """

    def authenticate(self, request):
        if request.path.startswith("/admin"):
            return None

        access_token = request.COOKIES.get('access_token')
        if access_token is None:
            return None

        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return super().authenticate(request)
