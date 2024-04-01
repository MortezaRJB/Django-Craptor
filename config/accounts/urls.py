from django.urls import path
from . import views
from dj_rest_auth.views import LoginView, LogoutView
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.jwt_auth import get_refresh_view

urlpatterns = [
    # Authentication & Authorization
    path("signup/", views.SignUpApiView.as_view(), name='signup'),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("token/verify/", TokenVerifyView.as_view()),
    path("token/refresh/", get_refresh_view().as_view()),
]

