from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

FROM_EMAIL = "Mixelo Notifications <contact@mixelo.io>"


@shared_task
def send_coin_purchase_email(user_id, coins, price_cents, currency):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(id=user_id)
    greeting_name = user.first_name if user.first_name else user.email
    price_str = f"{price_cents / 100:.2f}"
    subject = f"Your Mixelo Coins Purchase – {coins} coins"
    html_message = render_to_string(
        "coin_purchase_email.html",
        {
            "greeting_name": greeting_name,
            "coins": coins,
            "price_str": price_str,
            "currency": currency.upper(),
        },
    )
    send_mail(subject, "", FROM_EMAIL, [user.email], html_message=html_message)
