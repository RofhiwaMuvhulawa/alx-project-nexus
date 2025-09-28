from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def handler404(request, exception):
    """Custom 404 error handler"""
    logger.warning(f"404 error for URL: {request.path}")
    
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'status_code': 404,
        'path': request.path
    }, status=404)


@csrf_exempt
def handler500(request):
    """Custom 500 error handler"""
    logger.error(f"500 error for URL: {request.path}")
    
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.',
        'status_code': 500,
        'path': request.path
    }, status=500)