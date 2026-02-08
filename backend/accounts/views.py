from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .serializers import UserRegistrationSerializer, UserSerializer, UserListSerializer

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept email instead of username for login."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'] = serializers.EmailField()
        self.fields.pop('username', None)

    def validate(self, attrs):
        attrs['username'] = attrs.pop('email', '')
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
def me(request):
    """Get current user profile."""
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
def user_list(request):
    """List all users (admin only)."""
    if request.user.role != 'admin':
        return Response(
            {"detail": "Only administrators can view user list."},
            status=status.HTTP_403_FORBIDDEN
        )
    users = User.objects.all()
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    serializer = UserListSerializer(users, many=True)
    return Response(serializer.data)
