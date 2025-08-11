from django.urls import path
from .views import (RegistrationView,
                    LoginView,
                    CookieTokenRefreshView,
                    LogoutView,
                    ActivateAccountView)


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("activate/<uidb64>/<token>/",
         ActivateAccountView.as_view(), name="activate"),
]
