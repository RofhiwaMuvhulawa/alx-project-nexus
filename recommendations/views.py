from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    UserInteraction,
    RecommendationFeedback,
    RecommendationCache,
    UserSimilarity,
    MovieSimilarity
)
from .serializers import (
    UserInteractionSerializer,
    RecommendationFeedbackSerializer,
    RecommendationSerializer
)
from .services import RecommendationService
from movies.models import MovieCache
from movies.serializers import MovieSerializer


class RecommendationPagination(PageNumberPagination):
    """
    Custom pagination for recommendations.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class CollaborativeRecommendationView(generics.ListAPIView):
    """
    Get collaborative filtering recommendations.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    @extend_schema(
        summary="Get collaborative recommendations",
        description="Get movie recommendations based on collaborative filtering algorithm.",
        parameters=[
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of recommendations to return',
                default=20
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        limit = int(request.query_params.get('limit', 20))
        recommendation_service = RecommendationService()
        
        try:
            recommendations = recommendation_service.get_collaborative_recommendations(
                user=request.user,
                limit=limit
            )
            
            # Get movie details for recommendations
            movie_ids = [rec['movie_id'] for rec in recommendations]
            movies = MovieCache.objects.filter(tmdb_id__in=movie_ids)
            
            # Create a mapping for ordering
            movie_dict = {movie.tmdb_id: movie for movie in movies}
            ordered_movies = [movie_dict[movie_id] for movie_id in movie_ids if movie_id in movie_dict]
            
            serializer = self.get_serializer(ordered_movies, many=True)
            return Response({
                'results': serializer.data,
                'algorithm': 'collaborative_filtering',
                'count': len(serializer.data)
            })
            
        except Exception as e:
            return Response(
                {'error': 'Failed to generate collaborative recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContentBasedRecommendationView(generics.ListAPIView):
    """
    Get content-based recommendations.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    @extend_schema(
        summary="Get content-based recommendations",
        description="Get movie recommendations based on content similarity.",
        parameters=[
            OpenApiParameter(
                'movie_id',
                OpenApiTypes.INT,
                description='Movie ID to base recommendations on'
            ),
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of recommendations to return',
                default=20
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        movie_id = request.query_params.get('movie_id')
        limit = int(request.query_params.get('limit', 20))
        recommendation_service = RecommendationService()
        
        try:
            if movie_id:
                # Get recommendations based on specific movie
                recommendations = recommendation_service.get_content_based_recommendations(
                    movie_id=int(movie_id),
                    limit=limit
                )
            else:
                # Get recommendations based on user preferences
                recommendations = recommendation_service.get_content_based_recommendations_for_user(
                    user=request.user,
                    limit=limit
                )
            
            # Get movie details for recommendations
            movie_ids = [rec['movie_id'] for rec in recommendations]
            movies = MovieCache.objects.filter(tmdb_id__in=movie_ids)
            
            # Create a mapping for ordering
            movie_dict = {movie.tmdb_id: movie for movie in movies}
            ordered_movies = [movie_dict[movie_id] for movie_id in movie_ids if movie_id in movie_dict]
            
            serializer = self.get_serializer(ordered_movies, many=True)
            return Response({
                'results': serializer.data,
                'algorithm': 'content_based',
                'count': len(serializer.data)
            })
            
        except Exception as e:
            return Response(
                {'error': 'Failed to generate content-based recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HybridRecommendationView(generics.ListAPIView):
    """
    Get hybrid recommendations (combination of collaborative and content-based).
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    @extend_schema(
        summary="Get hybrid recommendations",
        description="Get movie recommendations using hybrid algorithm (collaborative + content-based).",
        parameters=[
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of recommendations to return',
                default=20
            ),
            OpenApiParameter(
                'collaborative_weight',
                OpenApiTypes.FLOAT,
                description='Weight for collaborative filtering (0.0-1.0)',
                default=0.6
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        limit = int(request.query_params.get('limit', 20))
        collaborative_weight = float(request.query_params.get('collaborative_weight', 0.6))
        recommendation_service = RecommendationService()
        
        try:
            recommendations = recommendation_service.get_hybrid_recommendations(
                user=request.user,
                limit=limit,
                collaborative_weight=collaborative_weight
            )
            
            # Get movie details for recommendations
            movie_ids = [rec['movie_id'] for rec in recommendations]
            movies = MovieCache.objects.filter(tmdb_id__in=movie_ids)
            
            # Create a mapping for ordering
            movie_dict = {movie.tmdb_id: movie for movie in movies}
            ordered_movies = [movie_dict[movie_id] for movie_id in movie_ids if movie_id in movie_dict]
            
            serializer = self.get_serializer(ordered_movies, many=True)
            return Response({
                'results': serializer.data,
                'algorithm': 'hybrid',
                'collaborative_weight': collaborative_weight,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            return Response(
                {'error': 'Failed to generate hybrid recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PersonalizedRecommendationView(generics.ListAPIView):
    """
    Get personalized recommendations based on user's complete profile.
    """
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    @extend_schema(
        summary="Get personalized recommendations",
        description="Get personalized movie recommendations based on user's complete profile and behavior.",
        parameters=[
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                description='Number of recommendations to return',
                default=20
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        limit = int(request.query_params.get('limit', 20))
        recommendation_service = RecommendationService()
        
        try:
            recommendations = recommendation_service.get_personalized_recommendations(
                user=request.user,
                limit=limit
            )
            
            # Get movie details for recommendations
            movie_ids = [rec['movie_id'] for rec in recommendations]
            movies = MovieCache.objects.filter(tmdb_id__in=movie_ids)
            
            # Create a mapping for ordering
            movie_dict = {movie.tmdb_id: movie for movie in movies}
            ordered_movies = [movie_dict[movie_id] for movie_id in movie_ids if movie_id in movie_dict]
            
            serializer = self.get_serializer(ordered_movies, many=True)
            return Response({
                'results': serializer.data,
                'algorithm': 'personalized',
                'count': len(serializer.data)
            })
            
        except Exception as e:
            return Response(
                {'error': 'Failed to generate personalized recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserInteractionView(generics.CreateAPIView):
    """
    Track user interactions with movies.
    """
    serializer_class = UserInteractionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Track user interaction",
        description="Track user interaction with a movie (view, rating, watchlist)."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserInteractionHistoryView(generics.ListAPIView):
    """
    Get user's interaction history.
    """
    serializer_class = UserInteractionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    def get_queryset(self):
        return UserInteraction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @extend_schema(
        summary="Get user interaction history",
        description="Retrieve user's interaction history with movies.",
        parameters=[
            OpenApiParameter(
                'interaction_type',
                OpenApiTypes.STR,
                description='Filter by interaction type',
                enum=['view', 'rating', 'watchlist']
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        interaction_type = request.query_params.get('interaction_type')
        queryset = self.get_queryset()
        
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecommendationFeedbackView(generics.CreateAPIView):
    """
    Submit feedback on recommendations.
    """
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Submit recommendation feedback",
        description="Submit feedback on a movie recommendation (like/dislike)."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecommendationFeedbackHistoryView(generics.ListAPIView):
    """
    Get user's recommendation feedback history.
    """
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecommendationPagination

    def get_queryset(self):
        return RecommendationFeedback.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @extend_schema(
        summary="Get recommendation feedback history",
        description="Retrieve user's feedback history on recommendations.",
        parameters=[
            OpenApiParameter(
                'feedback_type',
                OpenApiTypes.STR,
                description='Filter by feedback type',
                enum=['like', 'dislike']
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        feedback_type = request.query_params.get('feedback_type')
        queryset = self.get_queryset()
        
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)