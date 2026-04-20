
from os import name

from rest_framework import status,viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from .serializers import ProfileSerializer, CreateProfileSerializer
from .models import  Profile
import requests
from django.utils import timezone

class ExternalAPIError(APIException):
    status_code = 502
    default_detail = 'External API returned an invalid response or is unavailable.'

def get_data(name):
        try:
            gen_res = requests.get(f'https://api.genderize.io', params={'name': name})
            age_res = requests.get(f'https://api.agify.io', params={'name': name})
            nat_res = requests.get(f'https://api.nationalize.io', params={'name': name})
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(detail=f"External API error: {str(e)}")
           
        gen_data = gen_res.json()
        print(f"DEBUG GENDERIZE: {gen_data}")
        age_data = age_res.json()
        print(f"DEBUG GENDERIZE: {age_data}")
        nat_data = nat_res.json()
        print(f"DEBUG GENDERIZE: {nat_data}")

        print(gen_data)
        print(age_data)
        print(nat_data)

     

        if (gen_data['gender'] is None or gen_data['count'] == 0) or age_data['age'] == None or nat_data['country'] == []:
            raise ValidationError({"detail": f"No data available for the name: {name}"})
       
        age = age_data['age']
        if age <= 12: age_group = 'Child'
        elif age <= 19: age_group = 'Teenager'
        elif age <= 59: age_group = 'Adult'
        else: age_group = 'Senior'

        print(nat_data['country'])
        countries = nat_data.get('country', [])
        if not countries:
            raise ValidationError(detail="No country data found for this name.")

        probable_country = max(countries, key=lambda x: x['probability'])
        
        #probable_country = max(nat_data['country'], key = lambda x:x['probability'])# or use itemgetter('probability')
        print(probable_country)
        return {
                'name': name,
                'gender' : gen_data.get('gender'),
                'gender_probability' : gen_data.get('probability'),
                'sample_size' : gen_data.get('count'),
                'age' : age_data.get('age'),
                'age_group': age_group,
                'country_id' : probable_country.get('country_id'),
                'country_probability' : probable_country.get('probability'),
                'created_at' : timezone.now().isoformat()
                }
                
            

# Create your views here.
class GenderizeViewSet(viewsets.ModelViewSet):
    http_method_names = ['get','post','delete']
    queryset = Profile.objects.all()
    #serializer_class = ProfileSerializer
    lookup_field = 'pk'

    # def get_serializer_context(self):
    #     if self.request.method == "POST":
    #         name = self.request.data.get('name')
    #     else:
    #         name = self.request.query_params.get('name')

    #     print(name)
    #     payload = get_data(name)
    #     return {'payload': payload}
    
    def get_serializer_class(self):
        if self.action == 'create' or (self.action == 'list' and 'name' in self.request.query_params):
            return CreateProfileSerializer
        return ProfileSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        
        if name:
            # Filter the database results by name
            queryset = queryset.filter(name__iexact=name)
            
        return queryset
        
    def create(self, request, *args, **kwargs):
        if request.method == 'GET':
            name = request.query_params.get('name')
        name = request.data.get('name') 

        print(name)

        if not name:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif not name.isalpha():
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        instance = Profile.objects.filter(name=name).first()

        if instance:
            serializer = ProfileSerializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data,
            },status=status.HTTP_200_OK)
       
        payload = get_data(name)
                
        
        serializer = self.get_serializer(data={'name': name}, context={'payload': payload})
        if serializer.is_valid(raise_exception = True):
            instance = serializer.save()
            return Response({
                'status': 'success',
                'data': ProfileSerializer(instance).data}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response({
                'status': 'error',
                'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def list(self, request, *args, **kwargs):
        name = request.query_params.get('name')

        # If no name is provided, perform the standard "list all" behavior
        if not name:
            return super().list(request, *args, **kwargs)

        # 1. Try to find the profile in the database
        # We use .filter().first() to handle cases where names might repeat
        instance = Profile.objects.filter(name__iexact=name).first()

        if instance:
            serializer = ProfileSerializer(instance)
            return Response({
                'status': 'success',
                'source': 'database',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        # 2. If not found, fetch from external APIs
        # (get_data will raise an exception if it fails, which DRF handles)
        try:
            payload = get_data(name)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

        # 3. Use the Serializer to save the new record
        # Note: We use the context trick again for your custom create()
        serializer = self.get_serializer(
            data={'name': name}, 
            context={'payload': payload}
        )
        
        if serializer.is_valid(raise_exception=True):
            new_instance = serializer.save()
            
            # Use the display serializer for the final output
            return Response({
                'status': 'success',
                'source': 'external_api',
                'data': ProfileSerializer(new_instance).data
            }, status=status.HTTP_201_CREATED)

        # Fallback error
        return Response({'status': 'error', 'message': 'Could not process request'}, status=400)
    
    def retrieve(self, request, *args, **kwargs):
        print(self.kwargs)
     
        pk = self.kwargs.get('pk')
        print(pk)
        instance = Profile.objects.get(id=pk)

        #instance = Profile.objects.filter(name=name).first()
        print('the instance:',instance)
        if instance:
            
            return Response({
                'status': 'success',
                'data': ProfileSerializer(instance).data
            },status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Data Not Found'
        },status=status.HTTP_404_NOT_FOUND)
            
    def destroy(self,request, *args, **kwargs):
    
        print(self.kwargs)
     
        pk = self.kwargs.get('pk')
        print(pk)
        instance = Profile.objects.get(id=pk)

        #instance = Profile.objects.filter(name=name).first()
        print('the instance:',instance)
        if instance:
            instance.delete()
            return Response({
                'status': 'success',
                'message': f"{instance.name}'s Profile deleted successfully"
            },status=status.HTTP_204_NO_CONTENT)
        return Response({
            'status': 'error',
            'message': 'Data Not Found'
        },status=status.HTTP_404_NOT_FOUND)
