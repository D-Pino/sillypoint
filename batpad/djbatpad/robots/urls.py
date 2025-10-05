from django.urls import path
from . import views

app_name = "robots"
urlpatterns = [
    path("", views.robot_list, name="list"),
    path("<uuid:pk>/", views.robot_detail, name="detail"),
]
