from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates email uniqueness, prevents use of @example.com addresses,
    ensures password confirmation matches, and creates an inactive user account.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Please check your input and try again.')

        if value.lower().endswith('@example.com'):
            raise serializers.ValidationError(
                "Registrations with @example.com are not allowed.")

        return value

    def validate(self, data):
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(
                "Invalid input. Please try again.")

        return data

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = User(
            email=email,
            username=email,
            is_active=False
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """
    Serializer for user login using email and password.

    Overrides default behavior to authenticate by email instead of username,
    validates credentials, and returns JWT tokens along with the user object.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        attrs['username'] = user.username
        data = super().validate(attrs)
        self.user = user
        return data
