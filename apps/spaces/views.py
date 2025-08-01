import re

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from .models import Space, MembershipRequest
from .permissions import SpacePermissions, MembershipRequestPermissions, MembershipInvitationPermissions
from .serializers import (
    SpaceSerializer,
    SpaceActiveSerializer,
    SpaceDetailSerializer,
    MembershipRequestSerializer,
    MembershipRequestInvitationSerializer,
    MembershipRequestUpdateSerializer,
)
from .tasks import send_space_invitation_email

from apps.base.models import TopicTag
from apps.users.models import CustomUser
from apps.base.serializers import TopicTagSerializer
from apps.users.serializers import UserDetailSerializer


class SpacesPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 50


class SpaceViewSet(viewsets.ModelViewSet):
    permission_classes = [SpacePermissions]
    filterset_fields = {
        "name": ("exact", "icontains"),
        "access_type": ("exact",),
        "owner": ("exact",),
        "slug": ("exact", "icontains"),
        "created_time": ("gte", "lte"),
        "updated_time": ("gte", "lte"),
        "admins": ("exact",),
        "members": ("exact",),
    }
    pagination_class = SpacesPagination

    def get_queryset(self):
        base_queryset = Space.objects.all().order_by("name")

        if self.action == "list":
            user = self.request.user
            public_spaces = Q(access_type="free")

            if user.is_authenticated:
                private_user_spaces = Q(owner=user) | Q(admins=user) | Q(members=user)
                return base_queryset.filter(public_spaces | private_user_spaces).distinct()

            return base_queryset.filter(public_spaces)

        return base_queryset

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

    def perform_update(self, serializer):
        instance = serializer.save()

        categories_ids = self.request.data.get("categories", None)
        if categories_ids is not None:
            if not isinstance(categories_ids, list):
                return Response(
                    {"detail": "Categories must be a list of IDs."},
                    status=400,
                )
            valid_categories = TopicTag.objects.filter(id__in=categories_ids)
            instance.categories.set(valid_categories)
        return instance

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
        search = request.query_params.get("search")
        spaces = Space.objects.filter(Q(owner=user) | Q(members__in=[user]) | Q(admins__in=[user])).distinct()
        if search:
            spaces = spaces.filter(name__icontains=search)
        serializer = SpaceDetailSerializer(spaces, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="(?P<slug>[^/.]+)/members", permission_classes=[IsAuthenticated])
    def members(self, request, slug=None):
        try:
            space = Space.objects.get(slug=slug)
        except Space.DoesNotExist:
            return Response({"detail": "Space not found."}, status=404)
        queryset = space.members.all()

        search_term = request.query_params.get("search")
        if search_term:
            queryset = queryset.filter(
                Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(email__icontains=search_term)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserDetailSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = UserDetailSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="(?P<slug>[^/.]+)/admins", permission_classes=[IsAuthenticated])
    def admins(self, request, slug=None):
        try:
            space = Space.objects.get(slug=slug)
        except Space.DoesNotExist:
            return Response({"detail": "Space not found."}, status=404)
        queryset = space.admins.all()

        search_term = request.query_params.get("search")
        if search_term:
            queryset = queryset.filter(
                Q(first_name__icontains=search_term)
                | Q(last_name__icontains=search_term)
                | Q(email__icontains=search_term)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserDetailSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = UserDetailSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="(?P<slug>[^/.]+)/pending_requests",
        permission_classes=[IsAuthenticated],
    )
    def pending_requests(self, request, slug=None):
        try:
            space = Space.objects.get(slug=slug)
        except Space.DoesNotExist:
            return Response({"detail": "Space not found."}, status=404)
        search_term = request.query_params.get("search", "").strip()
        pending_requests = MembershipRequest.objects.filter(
            space=space, request_type="request", status="pending"
        ).select_related("user")
        if search_term:
            pending_requests = pending_requests.filter(
                Q(user__first_name__icontains=search_term)
                | Q(user__last_name__icontains=search_term)
                | Q(user__email__icontains=search_term)
            )

        users = [req.user for req in pending_requests]
        request_map = {req.user.id: req.id for req in pending_requests}

        page = self.paginate_queryset(users)
        serializer_context = self.get_serializer_context()
        serializer_context["request_map"] = request_map
        if page is not None:
            serializer = UserDetailSerializer(page, many=True, context=serializer_context)
            return self.get_paginated_response(serializer.data)

        serializer = UserDetailSerializer(users, many=True, context=serializer_context)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="make-admin")
    def make_admin(self, request, pk=None):
        space = self.get_object()
        user_id = request.data.get("user_id")
        user = space.members.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User is not a member of this space."}, status=400)

        space.members.remove(user)
        space.admins.add(user)

        return Response({"detail": f"User {user_id} promoted to admin."}, status=200)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="make-member")
    def make_member(self, request, pk=None):
        space = self.get_object()
        user_id = request.data.get("user_id")

        user = space.admins.filter(id=user_id).first()
        if not user:
            return Response({"detail": "User is not an admin of this space."}, status=400)

        space.admins.remove(user)
        space.members.add(user)

        return Response({"detail": f"User {user_id} demoted to member."}, status=200)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="leave")
    def leave_space(self, request, pk=None):
        space = self.get_object()
        user = request.user

        if space.owner == user:
            return Response(
                {"detail": "You cannot leave your own space. Transfer ownership or delete the space."}, status=400
            )

        if space.admins.filter(id=user.id).exists():
            space.admins.remove(user)
            return Response({"detail": "You have left the space."}, status=200)
        if space.members.filter(id=user.id).exists():
            space.members.remove(user)
            return Response({"detail": "You have left the space."}, status=200)
        return Response({"detail": "You are not a member of this space."}, status=400)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="remove-user")
    def remove_user(self, request, pk=None):
        space = self.get_object()
        current_user = request.user
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required."}, status=400)

        target_user = space.members.filter(id=user_id).first() or space.admins.filter(id=user_id).first()
        if not target_user:
            return Response({"detail": "User is not part of this space."}, status=400)

        if current_user == space.owner:
            if target_user == space.owner:
                return Response({"detail": "Owner cannot remove themselves."}, status=400)
            space.admins.remove(target_user)
            space.members.remove(target_user)
            return Response({"detail": f"User {user_id} removed."}, status=200)

        if space.admins.filter(id=current_user.id).exists():
            if target_user == space.owner or space.admins.filter(id=user_id).exists():
                return Response({"detail": "Admins cannot remove other admins or the owner."}, status=403)
            space.members.remove(target_user)
            return Response({"detail": f"Member {user_id} removed."}, status=200)

        return Response({"detail": "You do not have permission to remove this user."}, status=403)

    @action(detail=True, methods=["get"], url_path="users-to-invite", permission_classes=[IsAuthenticated])
    def users_to_invite(self, request, pk=None):
        space = self.get_object()

        excluded_ids = [space.owner_id]
        excluded_ids += list(space.admins.values_list("id", flat=True))
        excluded_ids += list(space.members.values_list("id", flat=True))
        pending_ids = MembershipRequest.objects.filter(space=space, status="pending").values_list("user_id", flat=True)
        excluded_ids += list(pending_ids)

        queryset = CustomUser.objects.exclude(id__in=excluded_ids)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))

        page = self.paginate_queryset(queryset)
        serializer = UserDetailSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post"], url_path="invite-multiple")
    def invite_multiple(self, request, pk=None):
        space = self.get_object()
        user_ids = request.data.get("user_ids", [])

        for uid in user_ids:
            if space.members.filter(id=uid).exists():
                continue
            if space.admins.filter(id=uid).exists():
                continue

            if MembershipRequest.objects.filter(
                space=space, user_id=uid, request_type="invite", status="pending"
            ).exists():
                continue
            MembershipRequest.objects.create(space=space, user_id=uid, request_type="invite", status="pending")

        return Response({"detail": "Invitations sent successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="invite-emails", permission_classes=[IsAuthenticated])
    def invite_emails(self, request, pk=None):
        space = self.get_object()
        emails = request.data.get("emails", [])

        if not isinstance(emails, list) or not emails:
            return Response({"detail": "emails must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        # Validar correos
        email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
        valid_emails = [email for email in emails if email_regex.match(email)]

        if not valid_emails:
            return Response({"detail": "No valid emails provided."}, status=status.HTTP_400_BAD_REQUEST)

        send_space_invitation_email.delay(valid_emails, space.name, space.slug)

        return Response(
            {"detail": f"Invitation emails are being sent to {len(valid_emails)} recipients."},
            status=status.HTTP_200_OK,
        )

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
        serializer.save(user=self.request.user, status="pending", request_type="request")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="accept")
    def accept_request(self, request, pk=None):
        try:
            user_request = MembershipRequest.objects.get(pk=pk, request_type="request", status="pending")
        except MembershipRequest.DoesNotExist:
            return Response({"detail": "Request not found or already processed."}, status=status.HTTP_404_NOT_FOUND)
        user_request.status = "approved"
        user_request.save()
        user_request.space.members.add(user_request.user)

        return Response({"detail": "request accepted successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="reject")
    def reject_request(self, request, pk=None):
        try:
            user_request = MembershipRequest.objects.get(pk=pk, request_type="request", status="pending")
        except MembershipRequest.DoesNotExist:
            return Response({"detail": "Request not found or already processed."}, status=status.HTTP_404_NOT_FOUND)

        user_request.status = "rejected"
        user_request.save()

        return Response({"detail": "Request rejected successfully."}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="my-invitations")
    def my_invitations(self, request):
        """
        Retrieve the list of invitations where the user is being invited to a space.
        """
        invitations = MembershipRequest.objects.filter(user=request.user, request_type="invite", status="pending")
        serializer = MembershipRequestInvitationSerializer(invitations, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="accept")
    def accept_invitation(self, request, pk=None):
        try:
            invitation = MembershipRequest.objects.get(
                pk=pk, user=request.user, request_type="invite", status="pending"
            )
        except MembershipRequest.DoesNotExist:
            return Response({"detail": "Invitation not found or already processed."}, status=status.HTTP_404_NOT_FOUND)
        invitation.status = "approved"
        invitation.save()
        invitation.space.members.add(request.user)

        return Response({"detail": "Invitation accepted successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="reject")
    def reject_invitation(self, request, pk=None):
        try:
            invitation = MembershipRequest.objects.get(
                pk=pk, user=request.user, request_type="invite", status="pending"
            )
        except MembershipRequest.DoesNotExist:
            return Response({"detail": "Invitation not found or already processed."}, status=status.HTTP_404_NOT_FOUND)

        invitation.status = "rejected"
        invitation.save()

        return Response({"detail": "Invitation rejected successfully."}, status=status.HTTP_200_OK)
