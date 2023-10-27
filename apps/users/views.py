import random
import string

from django.core.mail import send_mail
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CustomUser
from .permissions import UserPermissions
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermissions]

    @action(detail=True, methods=["post"])
    def send_reset_code(self, request, pk=None):
        user = self.get_object()
        reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

        user.reset_code = reset_code
        user.save()

        send_mail(
            "Reset your password",
            f"Use the following code to reset your password: {reset_code}. Access http://localhost:5173/view:resetpassword to proceed.",
            "from_email@example.com",
            [user.email],
            fail_silently=False,
        )
        return Response({"message": "Reset code sent to email."})
