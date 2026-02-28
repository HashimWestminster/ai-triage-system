from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import SurgeryHours
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserListSerializer,
    SurgeryHoursSerializer,
)

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
    """List all users - care navigators and superusers only."""
    if request.user.role not in ('care_navigator', 'superuser'):
        return Response(
            {"detail": "Only care navigators and site administrators can view the user list."},
            status=status.HTTP_403_FORBIDDEN
        )
    users = User.objects.all()
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    serializer = UserListSerializer(users, many=True)
    return Response(serializer.data)


# ---- Surgery Hours endpoints ----

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def surgery_status(request):
    """Public endpoint - tells patients whether the surgery is currently open."""
    now = timezone.localtime()
    current_day = now.weekday()  # Monday=0, Sunday=6
    current_time = now.time()

    try:
        hours = SurgeryHours.objects.get(day_of_week=current_day)
        if hours.is_closed:
            is_open = False
        else:
            is_open = hours.open_time <= current_time <= hours.close_time
        return Response({
            'is_open': is_open,
            'day': hours.get_day_of_week_display(),
            'open_time': str(hours.open_time)[:5] if not hours.is_closed else None,
            'close_time': str(hours.close_time)[:5] if not hours.is_closed else None,
            'is_closed_today': hours.is_closed,
            'current_time': current_time.strftime('%H:%M'),
        })
    except SurgeryHours.DoesNotExist:
        # No hours configured = always open (so it works out of the box)
        return Response({
            'is_open': True,
            'day': now.strftime('%A'),
            'open_time': None,
            'close_time': None,
            'is_closed_today': False,
            'current_time': current_time.strftime('%H:%M'),
            'not_configured': True,
        })


@api_view(['GET', 'PUT'])
def surgery_hours(request):
    """GET: list all surgery hours. PUT: bulk update (superuser only)."""
    if request.method == 'GET':
        if request.user.role not in ('care_navigator', 'superuser'):
            return Response({"detail": "Not authorised."}, status=status.HTTP_403_FORBIDDEN)
        hours = SurgeryHours.objects.all()
        return Response(SurgeryHoursSerializer(hours, many=True).data)

    if request.method == 'PUT':
        if request.user.role != 'superuser':
            return Response(
                {"detail": "Only site administrators can update surgery hours."},
                status=status.HTTP_403_FORBIDDEN,
            )
        for item in request.data:
            obj, _ = SurgeryHours.objects.update_or_create(
                day_of_week=item['day_of_week'],
                defaults={
                    'open_time': item.get('open_time', '08:00'),
                    'close_time': item.get('close_time', '18:00'),
                    'is_closed': item.get('is_closed', False),
                },
            )
        hours = SurgeryHours.objects.all()
        return Response(SurgeryHoursSerializer(hours, many=True).data)
