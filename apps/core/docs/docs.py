from drf_spectacular.utils import OpenApiResponse, OpenApiExample, extend_schema
from rest_framework import status

from apps.core.serializers import LoginSerializer


def employee_registration_docs():
    return extend_schema(
        summary="Register a new employee account",
        description=(
            """
            This endpoint allows the registration of a new employee account. 
            The request must include the following data:

            - `email`: The email address of the employee.
            - `password`: The password for the new account.

            Upon successful registration, the response will include a secret 
            that should be used for email verification.
            """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Registration successful, check your email for verification.",
                            "data": {
                                "secret": "XWHXT4UCQGTDQEE3QDDV6JRNXELTQJ2R",
                                "user_data": {
                                    "user_id": "58d91861-b5d3-4325-b7e3-703dd6149ded",
                                    "id": "aa0fb59e-2f9e-42c8-9a01-b921f9f696bc",
                                    "full_name": "",
                                    "date_of_birth": "",
                                    "email": "a0@gmail.com",
                                    "address": "",
                                    "occupation": "",
                                    "avatar": ""
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Account already exists and has Employee or Company profile",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has Employee or Company profile",
                            "code": "already_exists"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )


def company_registration_docs():
    return extend_schema(
        summary="Register a new company account",
        description=(
            """
            This endpoint allows the registration of a new company account.
            The request must include the following data:

            - `email`: The email address of the company.
            - `password`: The password for the new account.

            Upon successful registration, the response will include a secret
            that should be used for email verification.
            """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Registration successful, check your email for verification.",
                            "data": {
                                "secret": "W3VZAP6W75P5AUTFR7XLFIR3W4V5YAWM",
                                "user_data": {
                                    "user_id": "4889ff71-9f07-4674-9b0b-13f29924f3c4",
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "",
                                    "country": "",
                                    "email": "s@gmail.com",
                                    "avatar": "",
                                    "address": ""
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Account already exists and has Employee or Company profile",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has Employee or Company profile",
                            "code": "already_exists"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )


def verify_email_docs():
    return extend_schema(
        summary="Verify email address with OTP",
        description=(
            """
            This endpoint allows a registered user to verify their email address using a one-time password (OTP).
            The request must include the following data:

            - `email_address`: The user's email address.
            - `otp`: The OTP sent to the user's email address.

            Ensure you pass the email OTP secret generated during the registration process.
            """
        ),
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Email verification successful or already verified.",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Email verification successful"
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "success",
                            "message": "Email already verified",
                            "code": "verified_user"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="User with this email not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )


def resend_email_verification_code_docs():
    return extend_schema(
        summary="Send or resend email verification code",
        description=(
            """
            This endpoint allows a registered user to send or resend an email verification code to their registered email address.
            The request must include the following data:

            - `email_address`: The user's email address.
            """
        ),
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Verification code sent successfully. Please check your mail.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your mail."
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "success",
                            "message": "Email already verified",
                            "error_code": "already_verified"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="User with this email not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )


def send_new_email_verification_code_docs():
    return extend_schema(
        summary="Send email change verification code",
        description=(
            """
            This endpoint allows an authenticated user to send a verification code to a new email address they want to change to.
            The request must include the following data:

            - `email_address`: The user's new email address.
            """
        ),
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Verification code sent successfully. Please check your new email.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your new email."
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Account with this email already exists",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account with this email already exists",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )


def change_email_docs():
    return extend_schema(
        summary="Change account email address",
        description=(
            """
            This endpoint allows an authenticated user to change their account's email address. 
            Note that the email address can only be changed once every 10 days. 
            The request must include the following data:

            - `email_address`: The user's new email address.
            - `otp`: The verification code sent to the new email address.

            Ensure you pass the OTP secret generated during the verification process.
            """
        ),
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Email changed successfully.",
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "status": "success",
                            "message": "Email changed successfully."
                        }
                    )
                ]
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response={"application/json"},
                description="You can't use your previous email",
                examples=[
                    OpenApiExample(
                        name="Old email response",
                        value={
                            "status": "failure",
                            "message": "You can't use your previous email",
                            "code": "old_email"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    )
                ]
            ),
        }
    )


def login_docs():
    return extend_schema(
        summary="Authenticate and obtain authentication tokens",
        description=(
            """
            This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
            The request must be made using the LoginSerializer.
            """
        ),
        request=LoginSerializer,
        tags=['Login'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Logged in successfully",
                examples=[
                    OpenApiExample(
                        name="Employee success response",
                        value={
                            "status": "success",
                            "message": "Logged in successfully",
                            "data": {
                                "tokens": {
                                    "refresh": "token",
                                    "access": "token"
                                },
                                "profile_data": {
                                    "user_id": "58d91861-b5d3-4325-b7e3-703dd6149ded",
                                    "id": "aa0fb59e-2f9e-42c8-9a01-b921f9f696bc",
                                    "full_name": "",
                                    "date_of_birth": "",
                                    "email": "ayflix0@gmail.com",
                                    "address": "",
                                    "occupation": "",
                                    "avatar": ""
                                }
                            }
                        }
                    ),
                    OpenApiExample(
                        name="Company success response",
                        value={
                            "status": "success",
                            "message": "Logged in successfully",
                            "data": {
                                "tokens": {
                                    "refresh": "token",
                                    "access": "token"
                                },
                                "profile_data": {
                                    "user_id": "4889ff71-9f07-4674-9b0b-13f29924f3c4",
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "",
                                    "country": "",
                                    "email": "s@gmail.com",
                                    "avatar": "",
                                    "address": ""
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Unverified email response",
                        value={
                            "status": "failure",
                            "message": "Verify your email first",
                            "code": "unverified_email"
                        }
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response={"application/json"},
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Invalid credentials",
                        value={
                            "status": "failure",
                            "message": "Invalid credentials",
                            "code": "invalid_credentials"
                        }
                    ),
                ]
            )
        }
    )


def logout_docs():
    return extend_schema(
        summary="Logout",
        description=
        """
        This endpoint logs out an authenticated user by blacklisting their access token.
        The request should include the following data:

        - `refresh`: The refresh token used for authentication.
        """,
        tags=['Logout'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="Token is blacklisted",
                examples=[
                    OpenApiExample(
                        name="Blacklisted token response",
                        value={
                            "status": "failure",
                            "message": "Token is blacklisted",
                            "code": "invalid_entry"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Logged out successfully",
                examples=[
                    OpenApiExample(
                        name="Logout successful response",
                        value={
                            "status": "success",
                            "message": "Logged out successfully"
                        }
                    )
                ]
            )
        }
    )


def refresh_docs():
    return extend_schema(
        summary="Refresh token",
        description=
        """
        This endpoint allows a user to refresh an expired access token.
        The request should include the following data:

        - `refresh`: The refresh token.
        """,
        tags=['Token'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Refreshed successfully",
                examples=[
                    OpenApiExample(
                        name="Refresh successful response",
                        value={
                            "status": "success",
                            "message": "Refreshed successfully",
                            "data": "access_token"
                        }
                    )
                ]
            ),
        }
    )


def request_forgot_password_code_docs():
    return extend_schema(
        summary="Request password reset code",
        description=(
            """
            This endpoint allows a user to request a verification code to reset their password if it has been forgotten.
            The request must include the following data:

            - `email`: The user's email address.

            The response will also include an OTP secret that can be used to reset the password.
            """
        ),
        tags=['Password Change'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Account not found",
                examples=[
                    OpenApiExample(
                        name="Account not found response",
                        value={
                            "status": "failure",
                            "message": "Account not found",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Password code sent successfully",
                examples=[
                    OpenApiExample(
                        name="Password code sent response",
                        value={
                            "status": "success",
                            "message": "Password code sent successfully"
                        }
                    )
                ]
            )
        }
    )


def verify_forgot_password_code_docs():
    return extend_schema(
        summary="Verify password reset code for unauthenticated users",
        description=(
            """
            This endpoint allows a user to verify the verification code received for resetting their password if forgotten.
            The user will be identified and stored in a token to ensure that the correct user is changing their password.

            The request must include the following data:

            - `email`: The user's email address.
            - `otp`: The verification code sent to the user's email.
            """
        ),
        tags=['Password Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Otp verified successfully.",
                examples=[
                    OpenApiExample(
                        name="Otp verified response",
                        value={
                            "status": "success",
                            "message": "Otp verified successfully",
                            "data": "<token>"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )


def change_forgotten_password_docs():
    return extend_schema(
        summary="Change password for forgotten password (unauthenticated)",
        description=(
            """
            This endpoint allows an unauthenticated user to change their password after requesting a verification code.
            The request must include the following data:
            - `token`: The encrypted token received from the previous endpoint.
            - `password`: The new password.
            - `confirm_password`: The new password again to confirm.
            """
        ),
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"application/json"},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully.",
                        }
                    )
                ]
            ),
        }
    )


def change_password_docs():
    return extend_schema(
        summary="Change password for authenticated users",
        description=(
            """
            This endpoint allows an authenticated user to change their password.
            The request must include the following data:

            - `password`: The new password.
            - `confirm_password`: The new password again for confirmation.
            """
        ),
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"application/json"},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully",
                        }
                    )
                ]
            ),
        }
    )


def retrieve_employee_profile_docs():
    return extend_schema(
        summary="Retrieve employee profile",
        description=
        """
        This endpoint allows a user to retrieve his/her employee profile.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No profile found for this user",
                examples=[
                    OpenApiExample(
                        name="No profile found response",
                        value={
                            "status": "failure",
                            "message": "No profile found for this user",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Retrieved profile successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Retrieved profile successfully",
                            "data": {
                                "user_id": "58d91861-b5d3-4325-b7e3-703dd6149ded",
                                "id": "aa0fb59e-2f9e-42c8-9a01-b921f9f696bc",
                                "full_name": "",
                                "date_of_birth": "",
                                "email": "a@gmail.com",
                                "address": "",
                                "occupation": "",
                                "avatar": ""
                            }
                        }
                    )
                ]
            )
        }
    )


def update_employee_profile_docs():
    return extend_schema(
        summary="Update employee profile",
        description=
        """
        This endpoint allows a user to update his/her employee profile.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated profile successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Updated profile response",
                        value={
                            "status": "success",
                            "message": "Updated profile successfully",
                            "data": {
                                "user_id": "58d91861-b5d3-4325-b7e3-703dd6149ded",
                                "id": "aa0fb59e-2f9e-42c8-9a01-b921f9f696bc",
                                "full_name": "",
                                "date_of_birth": "",
                                "email": "a@gmail.com",
                                "address": "",
                                "occupation": "",
                                "avatar": ""
                            }
                        }
                    )
                ]
            )
        }
    )


def delete_employee_profile_docs():
    return extend_schema(
        summary="Delete employee account",
        description=
        """
        This endpoint allows a user to delete his/her employee account.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response={"application/json"},
                description="Deleted successfully",
                examples=[
                    OpenApiExample(
                        name="Deleted response",
                        value={
                            "status": "success",
                            "message": "Account deleted successfully"
                        }
                    )
                ]
            )
        }
    )


def retrieve_company_profile_docs():
    return extend_schema(
        summary="Retrieve company profile",
        description=
        """
        This endpoint allows a user to retrieve his/her company profile.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No profile found for this user",
                examples=[
                    OpenApiExample(
                        name="No profile found response",
                        value={
                            "status": "failure",
                            "message": "No profile found for this user",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Retrieved profile successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Retrieved profile successfully",
                            "data": {
                                "user_id": "4889ff71-9f07-4674-9b0b-13f29924f3c4",
                                "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                "name": "",
                                "country": "",
                                "email": "s@gmail.com",
                                "avatar": "",
                                "address": ""
                            }
                        }
                    )
                ]
            )
        }
    )


def update_company_profile_docs():
    return extend_schema(
        summary="Update company profile",
        description=
        """
        This endpoint allows a user to update his/her company profile.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated profile successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Updated response",
                        value={
                            "status": "success",
                            "message": "Updated profile successfully",
                            "data": {
                                "user_id": "4889ff71-9f07-4674-9b0b-13f29924f3c4",
                                "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                "name": "",
                                "country": "",
                                "email": "s@gmail.com",
                                "avatar": "",
                                "address": ""
                            }
                        }
                    )
                ]
            )
        }
    )


def delete_company_profile_docs():
    return extend_schema(
        summary="Delete company account",
        description=
        """
        This endpoint allows a user to delete his/her account.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response={"status": "success", "message": "Deleted successfully"},
                description="Deleted successfully",
                examples=[
                    OpenApiExample(
                        name="Deleted response",
                        value={
                            "status": "success",
                            "message": "Account deleted successfully"
                        }
                    )
                ]
            )
        }
    )
