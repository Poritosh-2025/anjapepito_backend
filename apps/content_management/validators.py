"""
File upload validators for video and image fields.
Enforces format and size limits per the API specification.
"""
from django.core.exceptions import ValidationError


ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "webm"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5 MB


def _get_ext(filename):
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def validate_video_file(value):
    """Validates video file: format and size."""
    ext = _get_ext(value.name)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError(
            f"Unsupported video format '.{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}."
        )
    if value.size > MAX_VIDEO_SIZE:
        raise ValidationError(
            f"Video file exceeds the 500 MB limit "
            f"({value.size / (1024*1024):.1f} MB uploaded)."
        )


def validate_image_file(value):
    """Validates image/thumbnail file: format and size."""
    ext = _get_ext(value.name)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image format '.{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}."
        )
    if value.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"Image file exceeds the 5 MB limit "
            f"({value.size / (1024*1024):.1f} MB uploaded)."
        )
