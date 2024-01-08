import json
import random
import string

from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CustomUser
from .permissions import UserPermissions
from .serializers import UserSerializer, PasswordResetSerializer, UserMeSerializer, CompleteUserSerializer

with open("secret.json") as f:
    secret = json.loads(f.read())


def get_secret(secret_name, secrets=secret):
    try:
        return secrets[secret_name]

    except:
        msg = "This variable %s doesn't exist" % secret_name
        return ImproperlyConfigured(msg)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermissions]

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
            f"Use the following code to reset your password: {reset_code}. Access {get_secret('CORS_ALLOWED_ORIGINS')}/?view=resetpassword to proceed.",
            "from_email@example.com",
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