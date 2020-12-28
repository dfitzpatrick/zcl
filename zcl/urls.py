from django.views.decorators.csrf import ensure_csrf_cookie

from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include, re_path
import debug_toolbar
# Just serve the react app from here.+

@ensure_csrf_cookie
def index(request):
    return render(request, "build/index.html")


urlpatterns = [
    path("", index, name='index'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('websub/', include('websub.urls')),
    path('api/', include('api.urls')),
    path('overlays/', include('overlays.urls')),
    re_path(r'^.*/$', index, name='all'),
]

