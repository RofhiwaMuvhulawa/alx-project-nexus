from django.contrib import admin
from django.utils.html import format_html
from .models import Genre, MovieCache, MovieGenre, RecommendationHistory

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """
    Genre admin configuration
    """
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(MovieCache)
class MovieCacheAdmin(admin.ModelAdmin):
    """
    Movie cache admin configuration
    """
    list_display = ('id', 'get_title', 'get_rating', 'cached_at')
    list_filter = ('original_language', 'cached_at')
    search_fields = ('title',)
    readonly_fields = ('cached_at',)
    ordering = ('-cached_at',)
    
    def get_title(self, obj):
        """
        Get movie title
        """
        return obj.title
    get_title.short_description = 'Title'
    
    def get_rating(self, obj):
        """
        Get movie rating
        """
        return obj.vote_average
    get_rating.short_description = 'Rating'


@admin.register(MovieGenre)
class MovieGenreAdmin(admin.ModelAdmin):
    """
    Movie-Genre relationship admin configuration
    """
    list_display = ('movie', 'genre')
    list_filter = ('genre',)
    search_fields = ('movie__tmdb_id', 'genre__name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('movie', 'genre')


@admin.register(RecommendationHistory)
class RecommendationHistoryAdmin(admin.ModelAdmin):
    """
    Recommendation history admin configuration
    """
    list_display = (
        'user', 'movie_id', 'get_movie_title', 'recommendation_type', 
        'confidence_score', 'created_at'
    )
    list_filter = ('recommendation_type', 'created_at')
    search_fields = ('user__email', 'movie_id', 'movie_title')
    readonly_fields = ('created_at',)
    
    def get_movie_title(self, obj):
        return obj.movie_title or f"Movie ID: {obj.movie_id}"
    get_movie_title.short_description = 'Movie Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Custom actions
    actions = ['delete_old_recommendations']
    
    def delete_old_recommendations(self, request, queryset):
        """
        Delete recommendations older than 30 days
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_recommendations = queryset.filter(created_at__lt=cutoff_date)
        count = old_recommendations.count()
        old_recommendations.delete()
        
        self.message_user(
            request,
            f"Successfully deleted {count} old recommendations."
        )
    delete_old_recommendations.short_description = "Delete recommendations older than 30 days"
