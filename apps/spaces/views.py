from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from .models import Space, MembershipRequest
from .permissions import SpacePermissions, MembershipRequestPermissions, MembershipInvitationPermissions
from .serializers import (
    SpaceSerializer,
    SpaceActiveSerializer,
    SpaceDetailSerializer,
    MembershipRequestSerializer,
    MembershipRequestUpdateSerializer,
)
from apps.base.serializers import TopicTagSerializer


class SpaceViewSet(viewsets.ModelViewSet):
    permission_classes = [SpacePermissions]
    queryset = Space.objects.all()
    filterset_fields = {
        "name": ("exact", "icontains"),
        "owner": ("exact",),
        "slug": ("exact",),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
        "admins": ("exact",),
        "members": ("exact",),
    }

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        """
        if self.action in ["retrieve", "find_by_slug"]:
            return SpaceDetailSerializer
        if self.action == "active_space":
            return SpaceActiveSerializer
        return SpaceSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def categories(self, request, pk=None):
        space = self.get_object()
        categories = space.categories.all()
        serializer = TopicTagSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="find-by-slug/(?P<slug>[^/.]+)", url_name="find-by-slug")
    def find_by_slug(self, request, slug=None):
        """
        Retrieve a space by its slug, independent of its ID.
        """
        space = get_object_or_404(Space, slug=slug)
        serializer = self.get_serializer(space)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="active-space")
    def active_space(self, request, pk=None):
        story = self.get_object()
        serializer = self.get_serializer(story)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="my-spaces")
    def my_spaces(self, request):
        """
        Retrieve the list of spaces where the user is either the owner or a member.
        """
        user = request.user
        spaces = Space.objects.filter(Q(owner=user) | Q(members__in=[user])).distinct()
        serializer = SpaceDetailSerializer(spaces, many=True, context={"request": request})
        return Response(serializer.data)


class MembershipRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [MembershipRequestPermissions]
    serializer_class = MembershipRequestSerializer
    filterset_fields = {
        "space": ("exact",),
        "user": ("exact",),
        "status": ("exact", "in"),
        "created_time": ("gte", "lte"),
    }

    def get_queryset(self):
        user = self.request.user
        return (
            MembershipRequest.objects.filter(request_type="request")
            .filter(Q(user=user) | Q(space__admins__in=[user]) | Q(space__owner=user))
            .distinct()
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return MembershipRequestUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MembershipInvitationViewSet(viewsets.ModelViewSet):
    permission_classes = [MembershipInvitationPermissions]
    serializer_class = MembershipRequestSerializer
    filterset_fields = {
        "space": ("exact",),
        "user": ("exact",),
        "status": ("exact", "in"),
        "created_time": ("gte", "lte"),
    }

    def get_queryset(self):
        user = self.request.user
        return (
            MembershipRequest.objects.filter(request_type="invite")
            .filter(Q(user=user) | Q(space__admins__in=[user]) | Q(space__owner=user))
            .distinct()
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return MembershipRequestUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        space_id = self.request.data.get("space")
        space = Space.objects.get(id=space_id)

        if space.owner == self.request.user or space.admins.filter(id=self.request.user.id).exists():
            invitee_id = self.request.data.get("user")
            if invitee_id == self.request.user.id:
                raise ValidationError("You can't invite yourself")
            serializer.save()
        else:
            raise ValidationError("You don't have the permissions to invite someone to this space.")
