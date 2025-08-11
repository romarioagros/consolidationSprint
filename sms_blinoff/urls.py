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

     path('df_number/add/',
         login_required(views.add_defNumbers),
         name='add_dfNumbers'),



     

     path("alfa/<int:alfa_id>/edit/", login_required(views.edit_alfa), name="edit_alfa"),



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

     path('showID/',
         login_required(views.showIDReestrandMother),
         name='showID'),

     path("alfa/<int:alfa_id>/copy/", login_required(views.copy_alfa), name="copy_alfa"),

     path('alfa/mass-edit/', views.bulk_edit_alfa, name='mass_edit_alfa'),
     path('dfNumbers/', login_required(views.dfNumbersPrice), name='dfNumbers'),

     path('alfa/bulk-add/', login_required(views.bulk_add_alfa), name='bulk_add_alfa'),



]