from rest_framework import serializers
from .models import Profile


class CreateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name']
    
    # def save(self, *args, **kwargs):
    #     payload = self.context.get('payload')
    #     return Profile.objects.create(**payload)

    def create(self, validated_data):
        # profile=Profile(**validated_data)
        # profile.save()
        # return profile
        payload = self.context.get('payload')

        if not payload:
            return Profile.objects.create(**validated_data)
        return Profile.objects.create(**payload)
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
    
    def create(self, validated_data):
        # profile=Profile(**validated_data)
        # profile.save()
        # return profile
        payload = self.context.get('payload')

        if not payload:
            return Profile.objects.create(**validated_data)
        return Profile.objects.create(**payload)
   
