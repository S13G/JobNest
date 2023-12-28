import json

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.exceptions import ValidationError

from apps.common.errors import ErrorCode


class BaseConsumer(AsyncWebsocketConsumer):

    async def err_handler(self, exc):
        err = {}
        if isinstance(exc, json.decoder.JSONDecodeError) or exc.detail.get(
                "non_field_errors"
        ):
            err["type"] = ErrorCode.INVALID_DATA_TYPE
            err["message"] = "Data is not a valid json"

        elif isinstance(exc, ValidationError):
            errors = exc.detail
            for key in errors:
                err_val = str(errors[key][0]).replace('"', "")
                errors[key] = err_val
                if isinstance(err_val, list):
                    errors[key] = err_val

            err["type"] = ErrorCode.INVALID_ENTRY
            err["message"] = "Invalid entry data"
            err["data"] = errors
        return err

    async def send_error_message(self, error):
        err = {"status": "error"} | error
        # Send an error message to the client
        await self.send(json.dumps(err))
