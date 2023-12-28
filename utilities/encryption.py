import jwt
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

User = get_user_model()


def encrypt_profile_to_token(user):
    # Assuming you have a `Profile` model related to the user model.
    # You can customize this payload with additional user data as needed.
    expiration_time = timezone.now() + timezone.timedelta(minutes=15)
    expiration_timestamp = int(expiration_time.timestamp())  # Convert expiration_time to Unix timestamp
    payload = {
        'user_id': str(user.id),  # Convert UUID to string
        'exp': expiration_timestamp  # Use the Unix timestamp for the exp claim
    }
    token = jwt.encode(payload, 'JWT_SECRET_KEY', algorithm='HS256')
    return token


def decrypt_token_to_profile(token):
    try:
        payload = jwt.decode(token, 'JWT_SECRET_KEY', algorithms=['HS256'])
        user_id = payload['user_id']
        user = User.objects.get(id=user_id)
        # Assuming you have a `Profile` model related to the user model.
        # You can retrieve additional user data here and attach it to the user object.
        return user
    except jwt.ExpiredSignatureError:
        return Response({"message": "Token has expired", "status": "failed"}, status=status.HTTP_401_UNAUTHORIZED)
    except (jwt.DecodeError, jwt.InvalidTokenError, User.DoesNotExist) as e:
        return Response({"message": f"Error: {e}", "status": "failed"},
                        status=status.HTTP_404_NOT_FOUND)