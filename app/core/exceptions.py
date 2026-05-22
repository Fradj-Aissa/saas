from fastapi import HTTPException
from starlette import status


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


def bad_request(detail: str = "Invalid request") -> AppException:
    return AppException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def not_found(detail: str = "Resource not found") -> AppException:
    return AppException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def internal_error(detail: str = "Internal server error") -> AppException:
    return AppException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
