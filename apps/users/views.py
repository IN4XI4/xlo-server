import re
import random
import string

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.utils.timezone import now
from django_countries import countries
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.blog.models import Like, Story, Comment, UserStoryView

from .models import CustomUser, ProfileColor, Experience, Gender, UserBadge
from .permissions import UserPermissions
from .serializers import (
    UserSerializer,
    PasswordResetSerializer,
    UserMeSerializer,
    CompleteUserSerializer,
    ProfileColorSerializer,
    ExperienceSerializer,
    GenderSerializer,
    UserDetailSerializer,
    UserBadgeSerializer,
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
        elif self.action == "retrieve":
            return UserDetailSerializer
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
            f"Use the following code to reset your password: {reset_code}. Access https://www.mixelo.io/login?view=resetpassword to proceed.",
            settings.DEFAULT_FROM_EMAIL,
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

    @action(detail=False, methods=["put"])
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


class UserBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserBadge.objects.all().order_by("id")
    serializer_class = UserBadgeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_fields = {
        "user": ("exact",),
        "badge_type": ("exact",),
        "level": ("exact",),
    }

    @action(detail=False, methods=["post"], url_path="update-badges")
    def update_badges(self, request):
        user = request.user
        badges_to_add = []

        user_badges = UserBadge.objects.filter(user=user).values_list("badge_type", "level")
        user_badges_set = set(user_badges)

        # 1. Veteran Badge
        member_since = user.date_joined
        months_as_member = (now() - member_since).days // 30
        veteran_levels = {
            3: "Bronze",
            6: "Silver",
            12: "Gold",
            18: "Obsidian",
            24: "Mixelo",
        }
        for months, level in veteran_levels.items():
            if months_as_member >= months and ("VETERAN", level) not in user_badges_set:
                badges_to_add.append(UserBadge(user=user, badge_type="VETERAN", level=level))

        # 2. Storyteller Badge
        stories_count = user.stories.count()
        storyteller_levels = {
            5: "Bronze",
            20: "Silver",
            50: "Gold",
            100: "Obsidian",
            200: "Mixelo",
        }
        for stories, level in storyteller_levels.items():
            if stories_count >= stories and ("STORYTELLER", level) not in user_badges_set:
                badges_to_add.append(UserBadge(user=user, badge_type="STORYTELLER", level=level))

        # 3. Popular Badge
        story_likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Story),
            object_id__in=user.stories.values_list("id", flat=True),
            liked=True,
        ).count()

        comment_likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id__in=Comment.objects.filter(user=user).values_list("id", flat=True),
            liked=True,
        ).count()

        total_likes = story_likes + comment_likes

        popular_levels = {
            5: "Bronze",
            20: "Silver",
            50: "Gold",
            100: "Obsidian",
            200: "Mixelo",
        }
        for likes, level in popular_levels.items():
            if total_likes >= likes and ("POPULAR", level) not in user_badges_set:
                badges_to_add.append(UserBadge(user=user, badge_type="POPULAR", level=level))

        # 4. Collaborator Badge
        comments_count = user.comment_set.count()

        collaborator_levels = {
            10: "Bronze",
            30: "Silver",
            70: "Gold",
            130: "Obsidian",
            250: "Mixelo",
        }
        for comments, level in collaborator_levels.items():
            if comments_count >= comments and ("COLLABORATOR", level) not in user_badges_set:
                badges_to_add.append(UserBadge(user=user, badge_type="COLLABORATOR", level=level))

        # 5. Explorer Badge
        total_stories = Story.objects.count()

        viewed_stories = UserStoryView.objects.filter(user=user).count()

        if total_stories > 0:
            viewed_percentage = (viewed_stories / total_stories) * 100
        else:
            viewed_percentage = 0

        explorer_levels = {
            20: "Bronze",
            30: "Silver",
            40: "Gold",
            55: "Obsidian",
            70: "Mixelo",
        }
        for percentage, level in explorer_levels.items():
            if viewed_percentage >= percentage and ("EXPLORER", level) not in user_badges_set:
                badges_to_add.append(UserBadge(user=user, badge_type="EXPLORER", level=level))

        if badges_to_add:
            created_badges = UserBadge.objects.bulk_create(badges_to_add)

            serialized_badges = UserBadgeSerializer(created_badges, many=True).data
            return Response(
                {
                    "message": f"{len(created_badges)} badges added.",
                    "badges": serialized_badges,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "No new badges were added."},
            status=status.HTTP_200_OK,
        )
