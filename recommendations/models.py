from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class RecommendationEngine(models.Model):
    """
    Model to store recommendation engine configurations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    algorithm_type = models.CharField(
        max_length=50,
        choices=[
            ('collaborative', 'Collaborative Filtering'),
            ('content_based', 'Content-Based'),
            ('hybrid', 'Hybrid'),
            ('popularity', 'Popularity-Based'),
            ('genre_based', 'Genre-Based'),
        ],
        default='hybrid'
    )
    is_active = models.BooleanField(default=True)
    weight = models.FloatField(default=1.0, help_text="Weight for hybrid recommendations")
    parameters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-weight', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.algorithm_type})"


class UserInteraction(models.Model):
    """
    Model to track user interactions with movies for recommendation algorithms
    """
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('favorite', 'Favorite'),
        ('unfavorite', 'Unfavorite'),
        ('rating', 'Rating'),
        ('search', 'Search'),
        ('click', 'Click'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    movie_id = models.IntegerField(help_text="TMDb movie ID")
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    value = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Interaction value (e.g., rating score, duration)"
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'movie_id']),
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['movie_id', 'interaction_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.interaction_type} - Movie {self.movie_id}"


class RecommendationFeedback(models.Model):
    """
    Model to store user feedback on recommendations for improving algorithms
    """
    FEEDBACK_TYPES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('not_interested', 'Not Interested'),
        ('already_watched', 'Already Watched'),
        ('irrelevant', 'Irrelevant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_feedback')
    movie_id = models.IntegerField(help_text="TMDb movie ID")
    recommendation_type = models.CharField(max_length=50)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    confidence_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Original confidence score of the recommendation"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'movie_id', 'recommendation_type']
        indexes = [
            models.Index(fields=['user', 'feedback_type']),
            models.Index(fields=['movie_id', 'feedback_type']),
            models.Index(fields=['recommendation_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.feedback_type} - Movie {self.movie_id}"


class UserSimilarity(models.Model):
    """
    Model to store precomputed user similarity scores for collaborative filtering
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user2')
    similarity_score = models.FloatField(
        help_text="Similarity score between 0 and 1"
    )
    algorithm = models.CharField(
        max_length=50,
        default='cosine',
        choices=[
            ('cosine', 'Cosine Similarity'),
            ('pearson', 'Pearson Correlation'),
            ('jaccard', 'Jaccard Similarity'),
        ]
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2', 'algorithm']
        indexes = [
            models.Index(fields=['user1', 'similarity_score']),
            models.Index(fields=['user2', 'similarity_score']),
            models.Index(fields=['similarity_score']),
        ]
    
    def __str__(self):
        return f"{self.user1.email} <-> {self.user2.email}: {self.similarity_score:.3f}"


class MovieSimilarity(models.Model):
    """
    Model to store precomputed movie similarity scores for content-based filtering
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie1_id = models.IntegerField(help_text="TMDb movie ID")
    movie2_id = models.IntegerField(help_text="TMDb movie ID")
    similarity_score = models.FloatField(
        help_text="Similarity score between 0 and 1"
    )
    algorithm = models.CharField(
        max_length=50,
        default='cosine',
        choices=[
            ('cosine', 'Cosine Similarity'),
            ('genre', 'Genre Similarity'),
            ('cast', 'Cast Similarity'),
            ('director', 'Director Similarity'),
            ('combined', 'Combined Features'),
        ]
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['movie1_id', 'movie2_id', 'algorithm']
        indexes = [
            models.Index(fields=['movie1_id', 'similarity_score']),
            models.Index(fields=['movie2_id', 'similarity_score']),
            models.Index(fields=['similarity_score']),
        ]
    
    def __str__(self):
        return f"Movie {self.movie1_id} <-> Movie {self.movie2_id}: {self.similarity_score:.3f}"


class RecommendationCache(models.Model):
    """
    Model to cache recommendation results for performance
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_cache')
    cache_key = models.CharField(max_length=255, help_text="Unique cache key")
    recommendation_type = models.CharField(max_length=50)
    recommendations = models.JSONField(help_text="Cached recommendation results")
    parameters = models.JSONField(default=dict, help_text="Parameters used for recommendations")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Cache expiration time")
    
    class Meta:
        unique_together = ['user', 'cache_key']
        indexes = [
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['cache_key']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.recommendation_type} - {self.cache_key}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
