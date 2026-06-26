from rest_framework import serializers

from apps.attempts.models import Attempt, QuestionAttempt, UserPoints


class AttemptListSerializer(serializers.ModelSerializer):
    assessment_name = serializers.ReadOnlyField(source="assessment.name")

    class Meta:
        model = Attempt
        fields = [
            "id",
            "assessment",
            "assessment_name",
            "user",
            "score",
            "approved",
            "is_finished",
            "start_time",
            "end_time",
            "points_obtained",
            "questions_provided",
        ]
        read_only_fields = ("user", "score", "approved", "start_time", "end_time")


class AttemptDetailSerializer(serializers.ModelSerializer):
    assessment_time_limit = serializers.ReadOnlyField(source="assessment.time_limit")
    assessment_name = serializers.ReadOnlyField(source="assessment.name")
    assessment_min_score = serializers.ReadOnlyField(source="assessment.min_score")
    assessment_number_of_questions = serializers.ReadOnlyField(source="assessment.number_of_questions")
    assessment_image = serializers.ImageField(source="assessment.image", read_only=True, use_url=True)
    assessment_author_first_name = serializers.ReadOnlyField(source="assessment.user.first_name")
    assessment_author_last_name = serializers.ReadOnlyField(source="assessment.user.last_name")
    assessment_author_username = serializers.ReadOnlyField(source="assessment.user.username")
    assessment_difficulty = serializers.ReadOnlyField(source="assessment.difficulty")
    assessment_community_difficulty = serializers.ReadOnlyField(source="assessment.user_difficulty_rating")
    available_attempts = serializers.SerializerMethodField()
    correct_answers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Attempt
        fields = "__all__"
        read_only_fields = ("user", "score", "approved", "start_time", "end_time")

    def get_available_attempts(self, obj):
        return obj.assessment.get_available_attempts(self.context["request"].user)


class QuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttempt
        fields = "__all__"
        read_only_fields = ("is_correct",)


class UserPointsSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    country_flag = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source="user.id")
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    picture = serializers.SerializerMethodField()
    birth_year = serializers.SerializerMethodField()
    profession = serializers.ReadOnlyField(source="user.profession")
    level = serializers.ReadOnlyField(source="user.level")
    badges_count = serializers.SerializerMethodField()

    class Meta:
        model = UserPoints
        fields = [
            "id",
            "user",
            "user_id",
            "category",
            "total_points",
            "average_score",
            "first_name",
            "last_name",
            "country",
            "country_flag",
            "picture",
            "birth_year",
            "profession",
            "level",
            "badges_count",
        ]

    def get_country(self, obj):
        return obj.user.country.name if obj.user.country else None

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.user.country and request:
            flag_url = obj.user.country.flag
            return request.build_absolute_uri(flag_url)
        return None

    def get_picture(self, obj):
        if obj.user.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.user.profile_picture.url)
        return None

    def get_birth_year(self, obj):
        return obj.user.birthday.year if obj.user.birthday else None

    def get_badges_count(self, obj):
        return obj.user.badges.count()
