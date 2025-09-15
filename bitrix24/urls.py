from django.urls import path
from . import views

app_name = 'bitrix24'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('file/', views.files_list, name='files'),
     path('user_list/', views.user_list, name='user_list'),
]


