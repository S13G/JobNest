import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        super().__init__(group=None)

    def run(self):
        self.email.send()


def send_email(subject: str, recipients: list, message: str = None, context: dict = None, template: str = None):
    if context is None:
        context = {}
    email = EmailMultiAlternatives(
            subject=subject,
            body=message or strip_tags(render_to_string(template, context)),
            from_email=settings.EMAIL_HOST_USER,
            to=recipients
    )

    if template:
        email.attach_alternative(render_to_string(template, context), "text/html")

    try:
        EmailThread(email).start()
    except ConnectionError:
        print("Something went wrong\nCouldn't send email")
