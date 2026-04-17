from django.urls import path,include
from rest_framework import routers 
from .views import GenderizeViewSet

router = routers.DefaultRouter()
router.register(r'profiles', GenderizeViewSet, basename='profiles')

urlpatterns = [
    path('api/', include(router.urls)),
    ]



