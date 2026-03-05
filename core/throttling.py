"""Custom throttle classes for OTP rate-limiting."""
from rest_framework.throttling import SimpleRateThrottle


class OTPRateThrottle(SimpleRateThrottle):
    """Limits OTP requests to 5/minute per email."""
    scope = "otp"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "")
        if not email:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": email.lower().strip(),
        }
