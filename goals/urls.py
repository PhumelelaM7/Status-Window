from django.urls import path
from . import views


urlpatterns = [
    path("goals/", views.goal_list, name="goal_list"),
    path("goals/add/", views.add_goal, name="add_goal"),
    path("goals/<int:goal_id>/", views.goal_detail, name="goal_detail"),
]