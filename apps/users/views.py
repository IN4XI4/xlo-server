import re
import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django_countries import countries
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import CustomUser, ProfileColor, Experience, Gender
from .permissions import UserPermissions
from .serializers import (
    UserSerializer,
    PasswordResetSerializer,
    UserMeSerializer,
    CompleteUserSerializer,
    ProfileColorSerializer,
    ExperienceSerializer,
    GenderSerializer,
)


class CountryListView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(countries)


class ProfileColorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProfileColor.objects.all().order_by("id")
    serializer_class = ProfileColorSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class ExperienceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Experience.objects.all().order_by("id")
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class GenderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Gender.objects.all().order_by("id")
    serializer_class = GenderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermissions]

    def get_serializer_class(self):
        """
        Devuelve un serializer diferente según el tipo de acción.
        """
        if self.action in ["update", "partial_update"]:
            return CompleteUserSerializer
        return UserSerializer

    def perform_update(self, serializer):
        instance = self.get_object()

        if "profile_picture" in serializer.validated_data.keys():
            if instance.profile_picture and instance.profile_picture != serializer.validated_data.get(
                "profile_picture"
            ):
                if default_storage.exists(instance.profile_picture.name):
                    default_storage.delete(instance.profile_picture.name)

        serializer.save()

    @action(detail=False, methods=["post"])
    def send_reset_code(self, request, pk=None):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=400)
        try:
            user = CustomUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=404)
        reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

        user.reset_code = reset_code
        user.save()

        send_mail(
            "Reset your password",
            f"Use the following code to reset your password: {reset_code}. Access http://www.mixelo.io/?view=resetpassword to proceed.",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        return Response({"message": "Reset code sent to email."})

    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            reset_code = serializer.validated_data["reset_code"]
            try:
                user = CustomUser.objects.get(reset_code=reset_code)
            except CustomUser.DoesNotExist:
                return Response(
                    {"detail": "Invalid reset code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["password"])
            user.reset_code = None
            user.save()
            return Response({"message": "Password reset successfully.", "email": user.email})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request, *args, **kwargs):
        """
        Return basic information about the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserMeSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="profile")
    def profile(self, request, *args, **kwargs):
        """
        Return all information about the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = CompleteUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_password(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        current_password = request.data.get("current_password")
        new_password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response(
                {"error": "Password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST
            )

        if (
            len(new_password) < 10
            or len(new_password) > 100
            or not re.search("[a-z]", new_password)
            or not re.search("[!@#?]", new_password)
        ):
            return Response(
                {"error": "New password does not meet the security requirements."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully."})
