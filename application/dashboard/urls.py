from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("metadata/", views.metadata, name="metadata"),
    path("latest-data/", views.latest_data,name="latest-data"),
    path("toggle-fetch/<str:action>/", views.toggle_fetch, name="toggle_fetch"),
]