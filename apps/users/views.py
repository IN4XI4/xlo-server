from rest_framework import viewsets

from .serializers import UserSerializer
from .models import CustomUser
from .permissions import UserPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = UserPermissions
