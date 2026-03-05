"""
Shared view mixins.
FIX #13 (DRY): PaginatedListMixin eliminates duplicated sl_no logic.
"""


class ViewerContextMixin:
    """Injects the requesting admin user info into paginated response."""

    def get_viewer_data(self, request):
        user = request.user
        pic = None
        if hasattr(user, "profile_picture") and user.profile_picture:
            pic = request.build_absolute_uri(user.profile_picture.url)
        return {
            "name": user.full_name or user.email,
            "profile_picture": pic,
            "role": user.role,
        }


class PaginatedListMixin(ViewerContextMixin):
    """
    Adds viewer data and sequential sl_no to paginated list responses.
    Eliminates duplicated list() overrides across AdminListView and UserListView.
    """

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        page_data = response.data.get("data", {})
        page_data["viewer"] = self.get_viewer_data(request)

        page_num = page_data.get("current_page", 1)
        page_size = self.pagination_class.page_size
        offset = (page_num - 1) * page_size
        for idx, item in enumerate(page_data.get("results", []), start=1):
            item["sl_no"] = offset + idx

        return response
