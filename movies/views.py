from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import MovieCache, Genre, UserFavorite
from .serializers import (
    MovieSerializer,
    GenreSerializer,
    UserFavoriteSerializer,
    MovieDetailSerializer
)
from .services import TMDbService


class MoviePagination(PageNumberPagination):
    """
    Custom pagination for movie lists.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TrendingMoviesView(generics.ListAPIView):
    """
    Get trending movies from TMDb.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Get trending movies",
        description="Retrieve a list of trending movies from TMDb API.",
        parameters=[
            OpenApiParameter(
                name='time_window',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Time window for trending (day or week)',
                enum=['day', 'week'],
                default='week'
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        time_window = request.query_params.get('time_window', 'week')
        tmdb_service = TMDbService()
        
        try:
            movies_data = tmdb_service.get_trending_movies(time_window=time_window)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch trending movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PopularMoviesView(generics.ListAPIView):
    """
    Get popular movies from TMDb.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Get popular movies",
        description="Retrieve a list of popular movies from TMDb API."
    )
    def get(self, request, *args, **kwargs):
        page = request.query_params.get('page', 1)
        tmdb_service = TMDbService()
        
        try:
            movies_data = tmdb_service.get_popular_movies(page=page)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch popular movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopRatedMoviesView(generics.ListAPIView):
    """
    Get top-rated movies from TMDb.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Get top-rated movies",
        description="Retrieve a list of top-rated movies from TMDb API."
    )
    def get(self, request, *args, **kwargs):
        page = request.query_params.get('page', 1)
        tmdb_service = TMDbService()
        
        try:
            movies_data = tmdb_service.get_top_rated_movies(page=page)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch top-rated movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpcomingMoviesView(generics.ListAPIView):
    """
    Get upcoming movies from TMDb.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Get upcoming movies",
        description="Retrieve a list of upcoming movies from TMDb API."
    )
    def get(self, request, *args, **kwargs):
        page = request.query_params.get('page', 1)
        tmdb_service = TMDbService()
        
        try:
            movies_data = tmdb_service.get_upcoming_movies(page=page)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch upcoming movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MovieDiscoveryView(generics.ListAPIView):
    """
    Discover movies with filters.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Discover movies",
        description="Discover movies with various filters like genre, year, rating, etc.",
        parameters=[
            OpenApiParameter('with_genres', OpenApiTypes.STR, description='Genre IDs (comma-separated)'),
            OpenApiParameter('primary_release_year', OpenApiTypes.INT, description='Release year'),
            OpenApiParameter('vote_average.gte', OpenApiTypes.FLOAT, description='Minimum rating'),
            OpenApiParameter('vote_average.lte', OpenApiTypes.FLOAT, description='Maximum rating'),
            OpenApiParameter('sort_by', OpenApiTypes.STR, description='Sort by field'),
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        ]
    )
    def get(self, request, *args, **kwargs):
        tmdb_service = TMDbService()
        
        # Extract query parameters
        filters = {
            'with_genres': request.query_params.get('with_genres'),
            'primary_release_year': request.query_params.get('primary_release_year'),
            'vote_average.gte': request.query_params.get('vote_average.gte'),
            'vote_average.lte': request.query_params.get('vote_average.lte'),
            'sort_by': request.query_params.get('sort_by', 'popularity.desc'),
            'page': request.query_params.get('page', 1),
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        try:
            movies_data = tmdb_service.discover_movies(**filters)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to discover movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MovieSearchView(generics.ListAPIView):
    """
    Search movies by query.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    @extend_schema(
        summary="Search movies",
        description="Search for movies by title or keywords.",
        parameters=[
            OpenApiParameter(
                'query',
                OpenApiTypes.STR,
                description='Search query',
                required=True
            ),
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        ]
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query')
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = request.query_params.get('page', 1)
        tmdb_service = TMDbService()
        
        try:
            movies_data = tmdb_service.search_movies(query=query, page=page)
            return Response({
                'results': movies_data.get('results', []),
                'total_pages': movies_data.get('total_pages', 1),
                'total_results': movies_data.get('total_results', 0)
            })
        except Exception as e:
            return Response(
                {'error': 'Failed to search movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MovieDetailView(generics.RetrieveAPIView):
    """
    Get detailed information about a specific movie.
    """
    serializer_class = MovieDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'movie_id'

    @extend_schema(
        summary="Get movie details",
        description="Retrieve detailed information about a specific movie."
    )
    def get(self, request, movie_id, *args, **kwargs):
        tmdb_service = TMDbService()
        
        try:
            # Try to get from cache first
            try:
                movie = MovieCache.objects.get(tmdb_id=movie_id)
                serializer = self.get_serializer(movie)
                return Response(serializer.data)
            except MovieCache.DoesNotExist:
                # Fetch from TMDb API
                movie_data = tmdb_service.get_movie_details(movie_id)
                if not movie_data:
                    return Response(
                        {'error': 'Movie not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Cache the movie data
                movie = tmdb_service.cache_movie(movie_data)
                serializer = self.get_serializer(movie)
                return Response(serializer.data)
                
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch movie details'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserFavoriteView(generics.ListCreateAPIView, generics.DestroyAPIView):
    """
    Manage user favorite movies.
    """
    serializer_class = UserFavoriteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MoviePagination

    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user).order_by('-created_at')

    @extend_schema(
        summary="Get user favorites",
        description="Retrieve a list of user's favorite movies."
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @extend_schema(
        summary="Add movie to favorites",
        description="Add a movie to user's favorites list."
    )
    def post(self, request, *args, **kwargs):
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already favorited
        if UserFavorite.objects.filter(user=request.user, movie_id=movie_id).exists():
            return Response(
                {'error': 'Movie already in favorites'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate movie exists
        tmdb_service = TMDbService()
        movie_data = tmdb_service.get_movie_details(movie_id)
        if not movie_data:
            return Response(
                {'error': 'Movie not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cache movie if not already cached
        try:
            movie = MovieCache.objects.get(tmdb_id=movie_id)
        except MovieCache.DoesNotExist:
            movie = tmdb_service.cache_movie(movie_data)
        
        # Create favorite
        favorite = UserFavorite.objects.create(
            user=request.user,
            movie_id=movie_id
        )
        
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Remove movie from favorites",
        description="Remove a movie from user's favorites list."
    )
    def delete(self, request, movie_id=None, *args, **kwargs):
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            favorite = UserFavorite.objects.get(user=request.user, movie_id=movie_id)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserFavorite.DoesNotExist:
            return Response(
                {'error': 'Movie not in favorites'},
                status=status.HTTP_404_NOT_FOUND
            )


class GenreListView(generics.ListAPIView):
    """
    Get list of movie genres.
    """
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get movie genres",
        description="Retrieve a list of all available movie genres."
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
