from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.users.models import CustomUser

TEMPLATES_MAPPING = {
    "send_info_with_username": "send_info_email_username.html",
}


@shared_task
def send_info_emails(subject, body, template):
    users_to_notify = CustomUser.objects.filter(email_info=True)
    from_email = "Mixelo Newsletter <info@mixelo.io>"
    for user in users_to_notify:
        greeting_name = user.first_name if user.first_name else user.email
        template_name = TEMPLATES_MAPPING.get(template, "send_info_email_username.html")
        html_message = render_to_string(template_name, {"greeting_name": greeting_name, "body": body})
        send_mail(subject, "", from_email, [user.email], html_message=html_message)
