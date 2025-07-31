from django.urls import path

from .views import travel_form_view, travel_history_list

urlpatterns = [
    path('', travel_form_view, name='travel_form'),
    path('history/', travel_history_list, name='travel_history'),
]
