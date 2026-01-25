from django.contrib import admin

from apps.attempts.models import Attempt, QuestionAttempt, UserPoints


admin.site.register(Attempt)
admin.site.register(QuestionAttempt)
admin.site.register(UserPoints)
