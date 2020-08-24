from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path, include


urlpatterns = [
    #path('login/', views.user_login, name='login'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('table/', views.check_state, name='check_state'),
    #path('', views.update_state, name='update_state'),
    path('pushall/', include('django_pushall.urls')),

]