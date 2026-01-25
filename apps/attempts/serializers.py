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
    country = serializers.SerializerMethodField()
    country_flag = serializers.SerializerMethodField()
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")

    class Meta:
        model = UserPoints
        fields = "__all__"

    def get_country(self, obj):
        return obj.user.country.name

    def get_country_flag(self, obj):
        request = self.context.get("request")
        if obj.user.country and request:
            flag_url = obj.user.country.flag
            return request.build_absolute_uri(flag_url)
        return None
