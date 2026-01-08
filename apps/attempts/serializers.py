from rest_framework import serializers

from apps.attempts.models import Attempt, QuestionAttempt, UserPoints


class AttemptSerializer(serializers.ModelSerializer):
    assessment_time_limit = serializers.ReadOnlyField(source="assessment.time_limit")
    assessment_name = serializers.ReadOnlyField(source="assessment.name")
    assessment_min_score = serializers.ReadOnlyField(source="assessment.min_score")
    assessment_number_of_questions = serializers.ReadOnlyField(source="assessment.number_of_questions")

    class Meta:
        model = Attempt
        fields = "__all__"
        read_only_fields = ("user", "score", "approved", "start_time", "end_time")


class QuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttempt
        fields = "__all__"
        read_only_fields = ("is_correct",)



class UserPointsSerializer(serializers.ModelSerializer):
    country_display = serializers.SerializerMethodField()

    class Meta:
        model = UserPoints
        fields = "__all__"

    def get_country_display(self, obj):
        return obj.user.country.name
