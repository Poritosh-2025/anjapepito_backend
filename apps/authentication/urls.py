from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("register/superadmin/", views.RegisterSuperadminView.as_view(), name="register-superadmin"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("resend-otp/", views.ResendOTPView.as_view(), name="resend-otp"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("password/reset-request/", views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/verify-reset-otp/", views.VerifyResetOTPView.as_view(), name="verify-reset-otp"),
    path("password/reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path("password/change/", views.ChangePasswordView.as_view(), name="password-change"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("profile/update/", views.UserProfileUpdateView.as_view(), name="profile-update"),
]
