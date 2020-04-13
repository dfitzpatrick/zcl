from django.urls import path
from . import views

urlpatterns = [
    path('streams/<uuid:id>/', views.WebSubView.as_view('streams'), name='streams'),
]
