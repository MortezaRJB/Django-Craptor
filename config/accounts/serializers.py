from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class SignUpSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
  password2 = serializers.CharField(write_only=True, required=True)
  
  class Meta:
    model = User
    fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password2']
  
  def validate_username(self, value):
    if User.objects.filter(username__iexact=value).exists():
      raise serializers.ValidationError(_("A user with this username already exists."))
    return value
  
  def validate(self, attrs):
    if attrs['password'] != attrs['password2']:
      raise serializers.ValidationError({"password": _("Password fields didn't match.")})
    return attrs
  
  def create(self, validated_data):
    user = User.objects.create(
      username=validated_data.pop('username', None),
      first_name=validated_data.pop('first_name', None),
      last_name=validated_data.pop('last_name', None),
      email=validated_data.pop('email', None)
    )
    user.set_password(validated_data.get('password'))
    user.save()

    return user

