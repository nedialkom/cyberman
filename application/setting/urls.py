from django.contrib import admin
from django.urls import path

from dashboard import views as dashboard_views

urlpatterns = [
    path("", dashboard_views.index, name="index"),
    path('admin/', admin.site.urls),

]