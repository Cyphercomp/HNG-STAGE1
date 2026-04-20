from rest_framework import serializers
from .models import Profile


class CreateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['name']
    

    def create(self, validated_data):
       
        payload = self.context.get('payload')

        if not payload:
            return Profile.objects.create(**validated_data)
        return Profile.objects.create(**payload)
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
    
    
   
