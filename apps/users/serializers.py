from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {"password": {"write_only": True, "style": {"input_type": "password"}}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("The password must be at least 8 characters long.")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("The password must contain at least one number.")

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "email", "date_joined", "picture"]

    def get_picture(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.profile_picture.url)
        return None


class PasswordResetSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("password", "password2", "reset_code")
