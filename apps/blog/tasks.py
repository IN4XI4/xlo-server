import logging
from celery import shared_task
from django.core.mail import send_mail

from .models import RecallCard

logger = logging.getLogger(__name__)


@shared_task
def send_weekly_recall_email():
    # from django.contrib.auth import get_user_model
    print("entraaaaa")
    logger.info("Entrada a send_weekly_recall_email")
    # User = get_user_model()
    # users = User.objects.filter(email_weekly_recalls=True)
    # subject = "Weekly Recall Update"

    # for user in users:
    #     greeting_name = user.first_name if user.first_name else user.email
    #     number_of_cards = RecallCard.objects.filter(user=user).count()
    #     message = f"""
    # Hey, {greeting_name},

    # Hope you're doing well!

    # 😃 Here is the weekly “Recall” update. - You have {number_of_cards} cards to consult on your recall board session!

    # 👍 To consult and practice the recalled cards follow this link: → Recall your Cards

    # The “recall card feature”, is the best way to improve your soft skills by rewatching the cards with the highest impact on you!

    # We wish you a great experience on your personal growth and a pleasant moment with Mixelo Stories.

    # Thank you for being a part of the Mixelo community.
    # If you enjoyed this email, do us a solid and forward it to a friend. We owe you one.

    # Until next week,
    # Mixelo Team
    # Guillaume, Juan & Yalit
    #     """
    # from_email = "Mixelo Notifications <contact@mixelo.io>"
    # recipient_list = [user.email]

    # send_mail(subject, message, from_email, recipient_list)


@shared_task
def send_like_email(user_id, comment, reply=False):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.get(id=user_id)
    subject_word = "replied" if reply else "liked"
    subject = f"Someone {subject_word} your comment"
    greeting_name = user.first_name if user.first_name else user.email

    message = f"""
Hey, {greeting_name},

Hope you're doing well!

😃 Someone from the community has just {subject_word} your comment: "{comment}"!

🏁 To see who {subject_word} you ... Follow this link: → My message

We're constantly improving the Mixelo user experience, so come as often as possible and experience real changes!

We wish you a great experience on your personal growth and a pleasant moment with Mixelo Stories.

Thank you for being a part of the Mixelo community.
If you enjoyed this email, do us a solid and forward it to a friend. We owe you one.

Until next time,
Mixelo Team
Guillaume, Juan & Yalit
    """
    from_email = "Mixelo Notifications <contact@mixelo.io>"
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)
