from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserInteraction,
    RecommendationFeedback,
    RecommendationCache,
    UserSimilarity,
    MovieSimilarity
)
from movies.models import MovieCache
from movies.serializers import MovieSerializer

User = get_user_model()


class UserInteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for user interactions with movies.
    """
    movie_details = MovieSerializer(source='movie', read_only=True)
    
    class Meta:
        model = UserInteraction
        fields = [
            'id',
            'movie_id',
            'movie_details',
            'interaction_type',
            'rating',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'movie_details']
    
    def validate_movie_id(self, value):
        """
        Validate that the movie exists in our cache or can be fetched from TMDb.
        """
        try:
            # Check if movie exists in cache
            MovieCache.objects.get(tmdb_id=value)
        except MovieCache.DoesNotExist:
            # If not in cache, we could fetch from TMDb here
            # For now, we'll allow it and let the view handle fetching
            pass
        return value
    
    def validate_rating(self, value):
        """
        Validate rating value when interaction type is 'rating'.
        """
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError(
                "Rating must be between 1 and 10."
            )
        return value
    
    def validate(self, data):
        """
        Validate that rating is provided when interaction type is 'rating'.
        """
        interaction_type = data.get('interaction_type')
        rating = data.get('rating')
        
        if interaction_type == 'rating' and rating is None:
            raise serializers.ValidationError(
                "Rating is required when interaction type is 'rating'."
            )
        
        if interaction_type != 'rating' and rating is not None:
            raise serializers.ValidationError(
                "Rating should only be provided when interaction type is 'rating'."
            )
        
        return data


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for recommendation feedback.
    """
    movie_details = MovieSerializer(source='movie', read_only=True)
    
    class Meta:
        model = RecommendationFeedback
        fields = [
            'id',
            'movie_id',
            'movie_details',
            'feedback_type',
            'algorithm_used',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'movie_details']
    
    def validate_movie_id(self, value):
        """
        Validate that the movie exists.
        """
        try:
            MovieCache.objects.get(tmdb_id=value)
        except MovieCache.DoesNotExist:
            # Allow feedback even if movie is not in cache
            pass
        return value


class RecommendationSerializer(serializers.Serializer):
    """
    Serializer for recommendation results.
    """
    movie_id = serializers.IntegerField()
    score = serializers.FloatField()
    algorithm = serializers.CharField(max_length=50)
    reason = serializers.CharField(max_length=255, required=False)
    movie_details = MovieSerializer(read_only=True)
    
    class Meta:
        fields = [
            'movie_id',
            'score',
            'algorithm',
            'reason',
            'movie_details'
        ]


class RecommendationCacheSerializer(serializers.ModelSerializer):
    """
    Serializer for recommendation cache.
    """
    class Meta:
        model = RecommendationCache
        fields = [
            'id',
            'user',
            'algorithm',
            'movie_ids',
            'scores',
            'parameters',
            'created_at',
            'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserSimilaritySerializer(serializers.ModelSerializer):
    """
    Serializer for user similarity data.
    """
    user1_username = serializers.CharField(source='user1.username', read_only=True)
    user2_username = serializers.CharField(source='user2.username', read_only=True)
    
    class Meta:
        model = UserSimilarity
        fields = [
            'id',
            'user1',
            'user1_username',
            'user2',
            'user2_username',
            'similarity_score',
            'algorithm',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user1_username', 'user2_username']


class MovieSimilaritySerializer(serializers.ModelSerializer):
    """
    Serializer for movie similarity data.
    """
    movie1_details = MovieSerializer(source='movie1', read_only=True)
    movie2_details = MovieSerializer(source='movie2', read_only=True)
    
    class Meta:
        model = MovieSimilarity
        fields = [
            'id',
            'movie1_id',
            'movie1_details',
            'movie2_id',
            'movie2_details',
            'similarity_score',
            'algorithm',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'movie1_details', 'movie2_details']


class RecommendationStatsSerializer(serializers.Serializer):
    """
    Serializer for recommendation statistics.
    """
    total_interactions = serializers.IntegerField()
    total_ratings = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_feedback = serializers.IntegerField()
    positive_feedback_ratio = serializers.FloatField()
    favorite_genres = serializers.ListField(
        child=serializers.CharField(max_length=100)
    )
    recommendation_accuracy = serializers.FloatField()
    
    class Meta:
        fields = [
            'total_interactions',
            'total_ratings',
            'average_rating',
            'total_feedback',
            'positive_feedback_ratio',
            'favorite_genres',
            'recommendation_accuracy'
        ]