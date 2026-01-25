from rest_framework import serializers

from apps.assessments.models import Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment
from apps.attempts.models import Attempt


class AssessmentSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")
    topic_name = serializers.ReadOnlyField(source="topic.title")
    topic_image = serializers.ImageField(source="topic.image", required=False, allow_null=True, use_url=True)

    class Meta:
        model = Assessment
        exclude = ["is_private"]
        read_only_fields = (
            "user",
            "average_score",
            "user_difficulty_rating",
            "attempts_count",
            "is_active",
            "created_at",
            "updated_at",
        )


class AssessmentDetailSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")
    topic_name = serializers.ReadOnlyField(source="topic.title")
    category_name = serializers.ReadOnlyField(source="topic.tag.name")
    followers_count = serializers.SerializerMethodField()
    available_attempts = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    language_name = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = "__all__"

    def get_followers_count(self, obj):
        return FollowAssessment.objects.filter(assessment=obj, follower__is_active=True).count()

    def get_available_attempts(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            attempts = Attempt.objects.filter(user=user, assessment=obj)
            perfect_score_exists = attempts.filter(score=100).exists()
            if perfect_score_exists:
                return 0
            attempts_made = attempts.count()
            return obj.allowed_attempts - attempts_made
        return 0

    def get_is_following(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            follow_assessment_id = (
                FollowAssessment.objects.filter(assessment=obj, follower=user).values_list("id", flat=True).first()
            )
            return follow_assessment_id if follow_assessment_id is not None else False
        return None

    def get_language_name(self, obj):
        return obj.get_language_display()


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ("is_active",)


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = "__all__"


class AssessmentDifficultyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentDifficultyRating
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class FollowAssessmentSerializer(serializers.ModelSerializer):
    assessment_name = serializers.ReadOnlyField(source="assessment.name")
    assessment_min_score = serializers.ReadOnlyField(source="assessment.min_score")
    assessment_allowed_attempts = serializers.ReadOnlyField(source="assessment.allowed_attempts")
    picture = serializers.SerializerMethodField()
    available_attempts = serializers.SerializerMethodField()

    class Meta:
        model = FollowAssessment
        fields = "__all__"
        read_only_fields = ["follower", "created_at"]

    def get_picture(self, obj):
        if obj.assessment.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.assessment.image.url)
        return None

    def get_available_attempts(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            attempts_made = Attempt.objects.filter(user=user, assessment=obj.assessment).count()
            return obj.assessment.allowed_attempts - attempts_made
        return 0
