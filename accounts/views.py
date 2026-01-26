from rest_framework import permissions, viewsets

from core.permissions import filter_queryset_by_site
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return filter_queryset_by_site(User.objects.all(), self.request.user, ["site"])