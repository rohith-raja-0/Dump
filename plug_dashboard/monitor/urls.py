from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name = 'dashboard'),
    path('dashboard/api/latest-reading/', views.latest_reading),
    path('dashboard/api/chart-data/', views.chart_data),
    path('dashboard/api/heatmap-data/', views.heatmap_data),
    path('home/',views.home, name='home'),
    path('login/',views.loginn, name='login'),
    path('logout/',views.logoutt, name='logout'),
    path('register/', views.register, name='register')
]