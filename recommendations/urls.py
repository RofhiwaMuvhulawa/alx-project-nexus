from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollaborativeRecommendationView,
    ContentBasedRecommendationView,
    HybridRecommendationView,
    PersonalizedRecommendationView,
    RecommendationFeedbackView,
    UserInteractionView,
    RecommendationFeedbackHistoryView,
    UserInteractionHistoryView,
)

app_name = 'recommendations'

# Create a router for ViewSets
router = DefaultRouter()

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Recommendation endpoints
    path('collaborative/', CollaborativeRecommendationView.as_view(), name='collaborative'),
    path('content-based/', ContentBasedRecommendationView.as_view(), name='content_based'),
    path('hybrid/', HybridRecommendationView.as_view(), name='hybrid'),
    path('personalized/', PersonalizedRecommendationView.as_view(), name='personalized'),
    
    # User interaction tracking
    path('interactions/', UserInteractionView.as_view(), name='track_interaction'),
    path('interactions/history/', UserInteractionHistoryView.as_view(), name='user_interactions'),
    
    # Recommendation feedback
    path('feedback/', RecommendationFeedbackView.as_view(), name='feedback'),
    path('feedback/history/', RecommendationFeedbackHistoryView.as_view(), name='feedback_history'),
]