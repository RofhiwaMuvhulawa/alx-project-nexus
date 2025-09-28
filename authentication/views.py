from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from .models import UserPreference
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserPreferenceSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user account.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account with email and password.",
        responses={201: UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user profile information.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information.",
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile information.",
        responses={200: UserSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """
    Change user password.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        description="Change the authenticated user's password.",
        request=ChangePasswordSerializer,
        responses={
            200: {"description": "Password changed successfully"},
            400: {"description": "Invalid data"}
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate new password
            try:
                validate_password(serializer.validated_data['new_password'], user)
            except ValidationError as e:
                return Response(
                    {'new_password': e.messages},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update user preferences.
    """
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        preference, created = UserPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

    @extend_schema(
        summary="Get user preferences",
        description="Retrieve the authenticated user's preferences.",
        responses={200: UserPreferenceSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update user preferences",
        description="Update the authenticated user's preferences.",
        responses={200: UserPreferenceSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update user preferences",
        description="Partially update the authenticated user's preferences.",
        responses={200: UserPreferenceSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Create or update user preferences.
        """
        preference = self.get_object()
        serializer = self.get_serializer(preference, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
