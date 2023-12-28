from django.urls import path

from apps.core import views

urlpatterns = [
    path('verify/email', views.VerifyEmailView.as_view(), name="verify_email"),
    path(
        'resend/email/verify/code/resend',
        views.ResendEmailVerificationCodeView.as_view(),
        name="resend_email_verification_code"
    ),
    path(
        'new-email/verify/code',
        views.SendNewEmailVerificationCodeView.as_view(),
        name="send_new_email_verification_code"
    ),
    path('change/email', views.ChangeEmailView.as_view(), name="change_email"),
    path('agent-login', views.AgentLoginView.as_view(), name="agent_log_in"),
    path('user-login', views.UserLoginView.as_view(), name="user_log_in"),
    path('logout', views.LogoutView.as_view(), name="logout"),
    path('refresh/token', views.RefreshView.as_view(), name="refresh_token"),
    path('request/forgot-password/code', views.RequestForgotPasswordCodeView.as_view(),
         name="request_forgotten_password_code"),
    path('verify/forgot-password/code', views.VerifyForgotPasswordCodeView.as_view(),
         name="verify_forgot_password_code"),
    path('change/forgot-password/<str:token>', views.ChangeForgottenPasswordView.as_view(),
         name="change_forgot_password"),
    path('change/new-password', views.ChangePasswordView.as_view(), name="change_password"),
    path('create-account', views.RegistrationView.as_view(), name="create_account"),
    path('user_profile/details', views.RetrieveUpdateDeleteProfileView.as_view(),
         name="get_update_delete_suer_profile"),
    path('agent_profile/details', views.RetrieveUpdateDeleteAgentProfileView.as_view(),
         name="get_update_delete_agent_profile"),

]
