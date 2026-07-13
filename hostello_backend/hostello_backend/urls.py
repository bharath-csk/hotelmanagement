from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from fees.admin import FeesAdminSite
from fees import admin as fees_admin 
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('students.urls')),  # All student views
    path("api/", include("requests.urls")),  # All request views
    # path("fees/", include("fees.urls")),
    path("fees/", include("fees.urls", namespace="fees")),
    path("accounts/login/", RedirectView.as_view(url="/login/", permanent=False))
    
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
