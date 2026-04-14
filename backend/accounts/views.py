# accounts/views.py - auth endpoints, user management, and surgery hours
# login uses JWT tokens with email instead of username
# surgery status is public so the frontend can show open/closed banners

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
    """swaps username for email on login - patients log in with their email"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # replace the username field with email
        self.fields['email'] = serializers.EmailField()
        self.fields.pop('username', None)

    def validate(self, attrs):
        # django expects 'username' internally so just swap it
        attrs['username'] = attrs.pop('email', '')
        data = super().validate(attrs)
        # include the user profile in the response so the frontend has it
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
    """returns the current logged-in user's profile"""
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
def user_list(request):
    """list all users - only care navigators and superusers can see this"""
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


# ---- Surgery Hours ----

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def surgery_status(request):
    """
    public endpoint - no login needed.
    checks if the surgery is open right now based on the configured hours.
    the frontend calls this to show the open/closed banner on the patient dashboard.
    """
    now = timezone.localtime()
    current_day = now.weekday()
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
        # if no hours are set up yet, default to always open
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
    """GET returns all 7 days of hours, PUT lets superuser update them all at once"""
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
        # bulk update - loop through the 7 days and update or create each one
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
