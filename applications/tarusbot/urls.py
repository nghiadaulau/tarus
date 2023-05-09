from django.urls import path
from django.urls import include
from applications.tarusbot import views

urlpatterns = [
    path("", views.index)
]
