
from rest_framework import status,viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ProfileSerializer
from .models import  Profile
import requests
from django.utils import timezone


# Create your views here.
class GenderizeViewSet(viewsets.ModelViewSet):
    http_methods_name = ['get','post','delete']
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        
        name = request.query_params.get('name')
        if not name:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        elif not name.isalpha():
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        instance = Profile.objects.filter(name=name)

        if instance:
            serializer = self.get_serializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data
            },status=status.HTTP_200_OK)
    
        gen_res = requests.get(f'https://api.genderize.io', params={'name': name})
        age_res = requests.get(f'https://api.agify.io', params={'name': name})
        nat_res = requests.get(f'https://api.nationalize.io', params={'name': name})

        if gen_res.status_code != 200 or age_res.status_code != 200 or nat_res.status_code != 200:
            return Response({
                'status': 'error',
                'message' : '{} returned an invalid response'.format('genderize.io' if gen_res.status_code != 200 else 'agify.io' if age_res.status_code != 200 else 'nationalize.io')
            },status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else :
            gen_data = gen_res.json()
            age_data = age_res.json()
            nat_data = nat_res.json()

            age_group = ''

            if (gen_data['gender'] == None or gen_data['count'] == 0) or age_data['age'] == None or nat_data['country'] == []:
                return Response(status=status.HTTP_502_BAD_GATEWAY)
            else:
                if (age_data['age'] >= 0 and age_data['age'] <=  12):
                    age_group = 'Child'
                elif (age_data['age'] >= 13 and age_data['age'] <= 19):
                    age_group = 'Teenager' 
                elif (age_data['age'] >= 20 and age_data['age'] <= 59):
                    age_group = 'Adult'
                else:
                    age_group = 'Senior'

                print(nat_data['country'])
                probable_country = max(nat_data['country'], key = lambda x:x['probability'])# or use itemgetter('probability')
                print(probable_country)
                payload = {
                    'status': 'success',
                    'data': {
                    'name': name,
                    'gender' : gen_data['gender'],
                    'gender_probability' : gen_data['probability'],
                    'sample_size' : gen_data['count'],
                    'age' : age_data['age'],
                    'age_group': age_group,
                    'country_id' : probable_country['country_id'],
                    'country_probability' : probable_country['probability'],
                    'created_at' : timezone.now().isoformat()
                    }
                }
                
                
                if request.method == 'POST': 
                    serializer = self.get_serializer(data=payload['data'])
                    if serializer.is_valid():
                        serializer.save()
                        
                        return Response({
                            'status': 'success',
                            'data': serializer.data}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({
                            'status': 'error',
                            'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
    def destroy(self,request, *args, **kwargs):
        name = request.query_params.get('name')

        instance = Profile.objects.filter(name=name).fist()

        if instance:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'status': 'error',
            'message': 'Data Not Found'
        },status=status.HTTP_404_NOT_FOUND)
