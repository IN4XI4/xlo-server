from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from .models import RecallCard

FROM_EMAIL_TEXT = "Mixelo Notifications <contact@mixelo.io>"


@shared_task
def send_weekly_recall_email():
    from django.contrib.auth import get_user_model

    user = get_user_model()
    users = user.objects.filter(email_weekly_recalls=True)
    if not users:
        return
    subject = "Weekly Recall Update"
    from_email = FROM_EMAIL_TEXT
    for user in users:
        greeting_name = user.first_name if user.first_name else user.email
        number_of_cards = RecallCard.objects.filter(user=user).count()
        if number_of_cards == 0:
            continue
        recipient_list = [user.email]
        html_message = render_to_string(
            "recall_weekly_email.html", {"greeting_name": greeting_name, "number_of_cards": number_of_cards}
        )
        send_mail(subject, "", from_email, recipient_list, html_message=html_message)


@shared_task
def send_like_email(user_id, comment, reply=False, story_slug=None):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.get(id=user_id)
    subject_word = "replied" if reply else "liked"
    subject = f"Someone {subject_word} your comment"
    greeting_name = user.first_name if user.first_name else user.email
    html_message = render_to_string(
        "send_like_email.html",
        {
            "greeting_name": greeting_name,
            "subject_word": subject_word,
            "comment": comment,
            "story_slug": story_slug,
        },
    )

    from_email = FROM_EMAIL_TEXT
    recipient_list = [user.email]
    send_mail(subject, "", from_email, recipient_list, html_message=html_message)


@shared_task
def send_new_stories_email(topic_id):
    from django.contrib.auth import get_user_model
    from apps.base.models import Topic

    topic_content_type = ContentType.objects.get_for_model(Topic)
    users = get_user_model().objects.filter(
        email_new_stories=True,
        like__content_type=topic_content_type,
        like__object_id=topic_id,
        like__liked=True,
    )
    topic_title = Topic.objects.filter(id=topic_id).values_list("title", flat=True).first()
    words = topic_title.split()
    trimmed_title = " ".join(words[:7]) + ("..." if len(words) > 7 else "")
    subject = f"New stories Alert | {trimmed_title}"
    from_email = FROM_EMAIL_TEXT
    for user in users:
        greeting_name = user.first_name if user.first_name else user.email
        html_message = render_to_string(
            "new_stories_email.html", {"greeting_name": greeting_name, "topic_title": topic_title}
        )
        recipient_list = [user.email]
        send_mail(subject, "", from_email, recipient_list, html_message=html_message)


@shared_task
def send_ask_for_help_email(user_id, comment, story_title, story_slug):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.get(id=user_id)
    username = user.first_name if user.first_name else user.email
    words = story_title.split()
    story_short = " ".join(words[:7]) + ("..." if len(words) > 7 else "")
    subject = f"Someone is asking for help | Story: {story_short}"
    html_message = render_to_string(
        "ask_help_email.html",
        {
            "user": username,
            "story": story_short,
            "comment": comment,
            "story_slug": story_slug,
        },
    )
    recipient_list = ["support@mixelo.io"]
    send_mail(subject, "", FROM_EMAIL_TEXT, recipient_list, html_message=html_message)
