from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping),
    path("echo/", views.echo),
    path("things/<int:pk>/", views.thing),
    path("notes/", views.Notes.as_view()),
    path("notes/<int:pk>/", views.NoteDetail.as_view()),
    path("make/", views.make),
]
