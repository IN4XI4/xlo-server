from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.base.models import Topic
from apps.spaces.models import Space
from apps.users.models import CustomUser


def validate_file_size(value, max_size):
    if value.size > max_size:
        raise ValidationError(f"El archivo es demasiado grande. Máximo permitido: {max_size / (1024 * 1024)}MB.")


def audio_file_size(value):
    validate_file_size(value, 1 * 1024 * 1024)  # 1 MB


def image_file_size(value):
    validate_file_size(value, 5 * 1024 * 1024)  # 5 MB


def general_file_size(value):
    validate_file_size(value, 2 * 1024 * 1024)


def content_file_name(instance, filename):
    return f"assessments/assessment_images/{filename}"


class Assessment(models.Model):
    LANGUAGE_CHOICES = [
        ("EN", "English"),
        ("ES", "Spanish"),
        ("FR", "French"),
        ("DE", "German"),
        ("IT", "Italian"),
        ("PT", "Portuguese"),
        ("OT", "Other"),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField()
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    minimum_requirements = models.TextField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assessments")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to=content_file_name, validators=[image_file_size], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    spaces = models.ManyToManyField(Space, related_name="assessments", blank=True)
    min_score = models.PositiveIntegerField(default=70, validators=[MinValueValidator(60), MaxValueValidator(90)])
    number_of_questions = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(5), MaxValueValidator(50)]
    )
    # TODO: Attach to a story.
    allowed_attempts = models.PositiveIntegerField(default=2, validators=[MinValueValidator(2), MaxValueValidator(10)])
    time_limit = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(120)])
    difficulty = models.FloatField(default=5.0, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])
    user_difficulty_rating = models.FloatField(null=True, blank=True)
    average_score = models.FloatField(null=True, blank=True)
    attempts_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


def question_audio_upload(instance, filename):
    return f"assessments/questions/audios/{filename}"


def question_image_upload(instance, filename):
    return f"assessments/questions/images/{filename}"


def question_file_upload(instance, filename):
    return f"assessments/questions/files/{filename}"


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="questions")
    description = models.TextField()
    audio = models.FileField(upload_to=question_audio_upload, validators=[audio_file_size], blank=True, null=True)
    image = models.ImageField(upload_to=question_image_upload, validators=[image_file_size], blank=True, null=True)
    file = models.FileField(upload_to=question_file_upload, validators=[general_file_size], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..." if len(self.description) > 50 else self.description


def choice_audio_upload(instance, filename):
    return f"assessments/choices/audios/{filename}"


def choice_image_upload(instance, filename):
    return f"assessments/choices/images/{filename}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    description = models.TextField()
    correct_answer = models.BooleanField(default=False)
    audio = models.FileField(upload_to=choice_audio_upload, validators=[audio_file_size], blank=True, null=True)
    image = models.ImageField(upload_to=choice_image_upload, validators=[image_file_size], blank=True, null=True)

    def __str__(self):
        return self.description[:50] + "..." if len(self.description) > 50 else self.description


class AssessmentDifficultyRating(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="difficulty_ratings")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="difficulty_ratings")
    difficulty = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Assessment difficulty rating"
        verbose_name_plural = "Assessment difficulty ratings"
        constraints = [
            models.UniqueConstraint(fields=["user", "assessment"], name="uq_rating_user_assessment"),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.assessment} with {self.difficulty} difficulty"


class FollowAssessment(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assessments_followed")
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="assessments_followed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["follower", "assessment"], name="uq_rating_follower_assessment"),
        ]

    def __str__(self):
        return f"{self.follower} -> {self.assessment}"
