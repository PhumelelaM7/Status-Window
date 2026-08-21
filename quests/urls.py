from django.urls import path
from . import views


urlpatterns = [
    path("", views.today_schedule, name="today_schedule"),
    path(
        "<int:year>/<int:month>/<int:day>/",
        views.today_schedule,
        name="today_schedule_dated",
    ),
    path("add/", views.add_quest, name="add_quest"),
    path("clear-day/", views.clear_day, name="clear_day"),
    path(
        "quest/<int:quest_id>/toggle-complete/",
        views.toggle_quest_complete,
        name="toggle_quest_complete",
    ),
    path(
        "quest/<int:quest_id>/move/<str:direction>/",
        views.move_quest,
        name="move_quest",
    ),
]