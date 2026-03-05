"""
Unified API response envelope.
Every endpoint returns: {status, code, message, data/errors}
"""
from rest_framework.response import Response
from rest_framework import status as http_status


def success_response(
    message="Operation completed successfully.",
    data=None,
    status=http_status.HTTP_200_OK,
):
    return Response(
        {"status": True, "code": status, "message": message, "data": data},
        status=status,
    )


def error_response(
    message="An error occurred.",
    errors=None,
    status=http_status.HTTP_400_BAD_REQUEST,
):
    return Response(
        {
            "status": False,
            "code": status,
            "message": message,
            "errors": errors or {},
        },
        status=status,
    )


def created_response(message="Resource created successfully.", data=None):
    return success_response(
        message=message, data=data, status=http_status.HTTP_201_CREATED
    )
