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
    path(
        "quest/<int:quest_id>/toggle-enabled/",
        views.toggle_quest_enabled,
        name="toggle_quest_enabled",
    ),
    path(
        "quest/<int:quest_id>/reschedule/",
        views.reschedule_quest,
        name="reschedule_quest",
    ),
    path(
        "quest/<int:quest_id>/mark-failed/",
        views.mark_quest_failed,
        name="mark_quest_failed",
    ),
    path(
        "quest/<int:quest_id>/notes/",
        views.update_quest_notes,
        name="update_quest_notes",
    ),
    path(
        "<int:year>/<int:month>/<int:day>/notes/",
        views.update_day_notes,
        name="update_day_notes",
    ),
    path(
        "<int:year>/<int:month>/<int:day>/set-start-time/",
        views.set_start_time,
        name="set_start_time",
    ),
    path("start-my-day/", views.start_my_day, name="start_my_day"),
]