import jwt
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError

User = get_user_model()


def encrypt_profile_to_token(user):
    # Assuming you have a `Profile` model related to the user model.
    # You can customize this payload with additional user data as needed.
    expiration_time = timezone.now() + timezone.timedelta(minutes=5)
    expiration_timestamp = int(expiration_time.timestamp())  # Convert expiration_time to Unix timestamp

    payload = {
        'user_id': str(user.id),  # Convert UUID to string
        'exp': expiration_timestamp  # Use the Unix timestamp for the exp claim
    }

    token = jwt.encode(payload=payload, key='JWT_SECRET_KEY', algorithm='HS256')
    return token


def decrypt_token_to_profile(token):
    try:
        payload = jwt.decode(jwt=token, key='JWT_SECRET_KEY', algorithms=['HS256'])
        user_id = payload['user_id']
        user = User.objects.get(id=user_id)
        # Assuming you have a `Profile` model related to the user model.
        # You can retrieve additional user data here and attach it to the user object.
        return user

    except jwt.ExpiredSignatureError:
        raise RequestError(err_code=ErrorCode.EXPIRED_TOKEN, err_msg="Token has expired",
                           status_code=status.HTTP_401_UNAUTHORIZED)

    except (jwt.DecodeError, jwt.InvalidTokenError, User.DoesNotExist) as e:
        raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=f"Error: {e}",
                           status_code=status.HTTP_400_BAD_REQUEST)
