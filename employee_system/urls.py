from django.contrib import admin
from django.urls import path, include
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('pushall/', include('django_pushall.urls')),
]
