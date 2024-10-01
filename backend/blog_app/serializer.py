
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import OTP,CustomUser
from .models import BlogPost
import pyotp

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model =CustomUser
        fields = ['email', 'username','password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        otp_code = data.get('otp')
        user = self.context['request'].user

        try:
            otp_record = OTP.objects.get(user=user)
            otp = pyotp.TOTP(otp_record.otp)
            if not otp.verify(otp_code):
                raise serializers.ValidationError("Invalid OTP")
        except OTP.DoesNotExist:
            raise serializers.ValidationError("OTP does not exist")

        return data

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'profile_picture']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'content', 'tags', 'author', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at'] 



