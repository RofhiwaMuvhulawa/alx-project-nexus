from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Movie Recommendation API',
        'version': '1.0.0'
    })


@require_http_methods(["GET"])
def api_info(request):
    """API information endpoint"""
    return JsonResponse({
        'name': 'Movie Recommendation API',
        'version': '1.0.0',
        'description': 'A Django REST API for movie recommendations using TMDb data',
        'documentation': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
            'schema': '/api/schema/'
        },
        'endpoints': {
            'authentication': '/api/auth/',
            'movies': '/api/movies/',
            'recommendations': '/api/recommendations/'
        }
    })


urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Health check and API info
    path('health/', health_check, name='health_check'),
    path('api/', api_info, name='api_info'),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/movies/', include('movies.urls')),
    path('api/recommendations/', include('recommendations.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'movie_api.views.handler404'
handler500 = 'movie_api.views.handler500'
