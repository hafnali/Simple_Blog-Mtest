from django.shortcuts import render
from rest_framework import generics, status
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail, BadHeaderError
import pyotp
from django.views.decorators.csrf import csrf_exempt
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 10

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from .models import CustomUser, BlogPost, OTP
from .serializer import RegisterSerializer,LoginSerializer,OTPVerificationSerializer,BlogPostSerializer


# User Registration View
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = serializer.save()
    #     return Response({
    #         "message": "User registered successfully.",
    #         "user": {
    #             "email": user.email,
    #             "username": user.username
    #         }
    #     }, status=status.HTTP_201_CREATED)

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                otp = pyotp.TOTP(pyotp.random_base32())
                otp_code = otp.now()
                OTP.objects.update_or_create(user=user, defaults={'otp': otp_code})
                try:
                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is {otp_code}',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                    response_data = {
                        "status": 1,  
                        "message": "User created. Please verify your OTP.",
                        "user": {
                            "email": user.email,
                            "username": user.username
                        }
        
            }
                except BadHeaderError:
                    return Response({"error": "Invalid header found."}, status=status.HTTP_400_BAD_REQUEST)
              
                return Response({"message": "User created. Please verify your OTP."}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# User Login View
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        login(request, user)
        
        return Response({
            "message": "Login successful.",
            "user": {
                "email": user.email,
                "username": user.username
            }
        }, status=status.HTTP_200_OK)

# OTP Verification View
class OTPVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)


@csrf_exempt
# Blog Post List View
class BlogPostListView(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# Blog Post Detail View
class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Blog post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

