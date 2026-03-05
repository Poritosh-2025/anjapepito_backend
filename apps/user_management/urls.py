from django.urls import path
from . import views

app_name = "user_management"

urlpatterns = [
    path("list/", views.UserListView.as_view(), name="user-list"),
    path("<uuid:pk>/detail/", views.UserDetailView.as_view(), name="user-detail"),
    path("<uuid:pk>/disable/", views.DisableUserView.as_view(), name="disable-user"),
    path("<uuid:pk>/enable/", views.EnableUserView.as_view(), name="enable-user"),
    path("<uuid:pk>/delete/", views.DeleteUserView.as_view(), name="delete-user"),
]
