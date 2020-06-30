from django.shortcuts import render

# Create your views here.
def alerter(request, id):
    return render(request, 'overlays/alerter.html', {})