from django.urls import path
from . import views
from .views import (
    Rtu19SrcDaysView ,
    Rtu19DstDaysView,
    Rtu26SrcDaysView,
    Rtu26DstDaysView ,
    RtuNew1SrcDaysView,
    RtuNew1DstDaysView,
    RtuNew2SrcDaysView,
    RtuNew2DstDaysView,
    RtuCbSrcDaysView,
    RtuDstDaysView,
    PostgresSrcDaysView,
    PostgresDstDaysView,
    MvtsSrcDaysView,
    MvtsDstDaysView,
    
    
    )
app_name = 'voice'

urlpatterns = [
    path('rtu19SrcDays/',    Rtu19SrcDaysView.as_view(), name='rtu19SrcDays'),
    path('rtu19DstDays/',    Rtu19DstDaysView.as_view(), name='rtu19DstDays'),
    path('rtu26SrcDays/',    Rtu26SrcDaysView.as_view(), name='rtu26SrcDays'),
    path('rtu26DstDays/',    Rtu26DstDaysView.as_view(), name='rtu26DstDays'),
    path('rtuNew1SrcDays/',  RtuNew1SrcDaysView.as_view(), name='rtuNew1SrcDays'),
    path('rtuNew1DstDays/',  RtuNew1DstDaysView.as_view(), name='rtuNew1DstDays'),
    path('rtuNew2SrcDays/',  RtuNew2SrcDaysView.as_view(), name='rtuNew2SrcDays'),
    path('rtuNew2DstDays/',  RtuNew2DstDaysView.as_view(), name='rtuNew2DstDays'),
    path('rtuCbSrcDays/',  RtuCbSrcDaysView.as_view(), name='rtuCbSrcDays'),
    path('rtuCbDstDays/',  RtuDstDaysView.as_view(), name='rtuCbDstDays'),
    path('postgresSrcDays/',  PostgresSrcDaysView.as_view(), name='postgresSrcDays'),
    path('postgresDstDays/',  PostgresDstDaysView.as_view(), name='postgresDstDays'),
    path('mvtsSrcDays/',  MvtsSrcDaysView.as_view(), name='mvtsSrcDays'),
    path('mvtsDstDays/',  MvtsDstDaysView.as_view(), name='mvtsDstDays'),
]