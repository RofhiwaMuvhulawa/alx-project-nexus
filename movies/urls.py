from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MovieDiscoveryView,
    MovieDetailView,
    MovieSearchView,
    UserFavoriteView,
    GenreListView,
    TrendingMoviesView,
    PopularMoviesView,
    TopRatedMoviesView,
    UpcomingMoviesView,
)

app_name = 'movies'

# Create a router for ViewSets
router = DefaultRouter()

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Movie discovery endpoints
    path('discover/', MovieDiscoveryView.as_view(), name='discover'),
    path('trending/', TrendingMoviesView.as_view(), name='trending'),
    path('popular/', PopularMoviesView.as_view(), name='popular'),
    path('top-rated/', TopRatedMoviesView.as_view(), name='top_rated'),
    path('upcoming/', UpcomingMoviesView.as_view(), name='upcoming'),
    
    # Movie search and details
    path('search/', MovieSearchView.as_view(), name='search'),
    path('<int:movie_id>/', MovieDetailView.as_view(), name='detail'),
    
    # User favorites
    path('favorites/', UserFavoriteView.as_view(), name='favorites'),
    path('favorites/<int:movie_id>/', UserFavoriteView.as_view(), name='favorite_detail'),
    
    # Genres
    path('genres/', GenreListView.as_view(), name='genres'),
]