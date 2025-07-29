from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

FROM_EMAIL_TEXT = "Mixelo Invitations <contact@mixelo.io>"


@shared_task
def send_space_invitation_email(emails, space_name, space_slug):
    subject = f"Invitation to join {space_name} on Mixelo"
    from_email = FROM_EMAIL_TEXT

    for email in emails:
        html_message = render_to_string(
            "space_invite_email.html",
            {"space_name": space_name, "space_slug": space_slug, "signup_link": "https://mixelo.io"},
        )
        send_mail(subject, "", from_email, [email], html_message=html_message)
