import uuid
from django.db import models
from django.conf import settings


class Genre(models.Model):
    """
    Movie genres from TMDb
    """
    id = models.IntegerField(primary_key=True, help_text="TMDb genre ID")
    name = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'genres'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MovieCache(models.Model):
    """
    Cached movie data from TMDb API
    """
    id = models.IntegerField(primary_key=True, help_text="TMDb movie ID")
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=500, blank=True, null=True)
    backdrop_path = models.CharField(max_length=500, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    vote_average = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    vote_count = models.IntegerField(default=0)
    genres = models.JSONField(default=list, blank=True)
    runtime = models.IntegerField(blank=True, null=True, help_text="Runtime in minutes")
    original_language = models.CharField(max_length=10, blank=True)
    popularity = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    cached_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'movies_cache'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['-release_date']),
            models.Index(fields=['-vote_average']),
            models.Index(fields=['-popularity']),
            models.Index(fields=['-cached_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.release_date.year if self.release_date else 'Unknown'})"
    
    @property
    def full_poster_url(self):
        if self.poster_path:
            return f"{settings.TMDB_IMAGE_BASE_URL}{self.poster_path}"
        return None
    
    @property
    def full_backdrop_url(self):
        if self.backdrop_path:
            return f"{settings.TMDB_IMAGE_BASE_URL}{self.backdrop_path}"
        return None


class MovieGenre(models.Model):
    """
    Many-to-many relationship between movies and genres
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(MovieCache, on_delete=models.CASCADE, related_name='movie_genres')
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='movie_genres')
    
    class Meta:
        db_table = 'movie_genres'
        unique_together = ['movie', 'genre']
        indexes = [
            models.Index(fields=['movie']),
            models.Index(fields=['genre']),
        ]
    
    def __str__(self):
        return f"{self.movie.title} - {self.genre.name}"


class UserFavorite(models.Model):
    """
    User favorite movies
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='movie_favorites')
    movie_id = models.IntegerField(help_text="TMDb movie ID")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_favorites'
        unique_together = ['user', 'movie_id']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['movie_id']),
            models.Index(fields=['-added_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Movie {self.movie_id}"


class RecommendationHistory(models.Model):
    """
    Track recommendation history for users
    """
    RECOMMENDATION_TYPES = [
        ('collaborative', 'Collaborative Filtering'),
        ('content_based', 'Content-Based'),
        ('genre_based', 'Genre-Based'),
        ('popularity', 'Popularity-Based'),
        ('hybrid', 'Hybrid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendation_history')
    movie_id = models.IntegerField(help_text="TMDb movie ID")
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_history'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['movie_id']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['-confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Movie {self.movie_id} ({self.recommendation_type})"
