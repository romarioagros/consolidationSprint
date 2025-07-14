from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'sms_blinoff'


urlpatterns = [
    path('tranks/',
         login_required(views.company_list),
         name='company_list'),

    path('companies/add/',
         login_required(views.add_company),
         name='add_account'),

    path('mother/add/',
         login_required(views.add_mother),
         name='add_mother'),

    path('mother/',
         login_required(views.mother_list),
         name='mother_list'),

    path('alfa/',
         login_required(views.alfa_list),
         name='alfa_list'),

    path('alfa/add/',
         login_required(views.add_alfa),
         name='add_alfa'),

    path('services/',
         login_required(views.sms_services),
         name='sms_services'),

    path('category3/',
         login_required(views.category3_list),
         name='category3_list'),

    path('paymed_sms/',
         login_required(views.paymed_sms_list),
         name='paymed_sms_list'),

    path('sms_periode/',
         login_required(views.sms_periode),
         name='sms_periode'),

    path('sms_periode/<str:period>/',
         login_required(views.sms_periode),
         name='sms_periode'),

 path('sms/mother_delete/<int:id>/', login_required(views.delete_mother), name='delete_mother'),


]