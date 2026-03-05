from django.urls import path
from . import views

app_name = "administrators"

urlpatterns = [
    path("staff/create/", views.CreateStaffAdminView.as_view(), name="create-staff"),
    path("list/", views.AdminListView.as_view(), name="admin-list"),
    path("profile/", views.AdminProfileView.as_view(), name="admin-profile"),
    path("profile/update/", views.AdminProfileUpdateView.as_view(), name="admin-profile-update"),
    path("password/change/", views.AdminChangePasswordView.as_view(), name="admin-change-password"),
    path("users/<uuid:pk>/disable/", views.DisableAdminView.as_view(), name="disable-admin"),
    path("users/<uuid:pk>/enable/", views.EnableAdminView.as_view(), name="enable-admin"),
    path("users/<uuid:pk>/delete/", views.DeleteAdminView.as_view(), name="delete-admin"),
]
