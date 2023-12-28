from http import HTTPStatus

from rest_framework.exceptions import AuthenticationFailed, ValidationError, APIException, PermissionDenied

from apps.common.errors import ErrorCode
from apps.common.responses import CustomResponse


class RequestError(APIException):
    default_detail = "An error occurred"

    def __init__(self, err_code: str, err_msg: str, status_code: int = 400, data: dict = None):
        self.status_code = HTTPStatus(status_code)
        self.err_code = err_code
        self.err_msg = err_msg
        self.data = data
        super().__init__()


def handle_authentication_failed(exc):
    exc_list = str(exc).split("DETAIL: ")
    return CustomResponse.error(
        message=exc_list[-1],
        status_code=401,
        err_code=ErrorCode.UNAUTHORIZED_USER,
    )


def handle_request_error(exc):
    return CustomResponse.error(
        message=exc.err_msg,
        data=exc.data,
        status_code=exc.status_code,
        err_code=exc.err_code,
    )


def handle_permission_error(exc):
    exc_list = str(exc).split("DETAIL: ")

    return CustomResponse.error(
        message=exc_list[-1],
        status_code=403,
        err_code=ErrorCode.UNAUTHORIZED_USER,
    )


def handle_validation_error(exc):
    errors = {}
    for key, error_list in exc.detail.items():
        if isinstance(error_list, list):
            error_message = str(error_list[0]).strip('"')
        else:
            error_message = str(error_list).strip('"')
        errors[key] = error_message

    return CustomResponse.error(
        message="Invalid Entry",
        data=errors,
        status_code=422,
        err_code=ErrorCode.INVALID_ENTRY,
    )


def custom_exception_handler(exc, context):
    try:
        if isinstance(exc, AuthenticationFailed):
            return handle_authentication_failed(exc)
        elif isinstance(exc, RequestError):
            return handle_request_error(exc)
        elif isinstance(exc, ValidationError):
            return handle_validation_error(exc)
        elif isinstance(exc, PermissionDenied):
            return handle_permission_error(exc)
        else:
            status_code = 500 if not hasattr(exc, 'status_code') else exc.status_code
            return CustomResponse.error(
                message="Something went wrong!",
                status_code=status_code,
                err_code=ErrorCode.SERVER_ERROR,
            )
    except APIException as e:
        return CustomResponse.error(
            message="Server Error", status_code=500, err_code=ErrorCode.SERVER_ERROR
        )
