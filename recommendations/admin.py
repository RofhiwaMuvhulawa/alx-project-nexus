from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import (
    RecommendationEngine, UserInteraction, RecommendationFeedback,
    UserSimilarity, MovieSimilarity, RecommendationCache
)


@admin.register(RecommendationEngine)
class RecommendationEngineAdmin(admin.ModelAdmin):
    """
    Recommendation engine admin configuration
    """
    list_display = ('name', 'algorithm_type', 'is_active', 'weight', 'updated_at')
    list_filter = ('algorithm_type', 'is_active', 'updated_at')
    search_fields = ('name', 'algorithm_type')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-weight', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'algorithm_type', 'is_active', 'weight')
        }),
        ('Configuration', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    """
    User interaction admin configuration
    """
    list_display = ('user', 'movie_id', 'interaction_type', 'value', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__email', 'movie_id')
    readonly_fields = ('timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Custom actions
    actions = ['delete_old_interactions']
    
    def delete_old_interactions(self, request, queryset):
        """
        Delete interactions older than 90 days
        """
        cutoff_date = timezone.now() - timedelta(days=90)
        old_interactions = queryset.filter(timestamp__lt=cutoff_date)
        count = old_interactions.count()
        old_interactions.delete()
        
        self.message_user(
            request,
            f"Successfully deleted {count} old interactions."
        )
    delete_old_interactions.short_description = "Delete interactions older than 90 days"


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    """
    Recommendation feedback admin configuration
    """
    list_display = ('user', 'movie_id', 'feedback_type', 'recommendation_type', 'created_at')
    list_filter = ('feedback_type', 'recommendation_type', 'created_at')
    search_fields = ('user__email', 'movie_id')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserSimilarity)
class UserSimilarityAdmin(admin.ModelAdmin):
    """
    User similarity admin configuration
    """
    list_display = ('user1', 'user2', 'get_similarity_score', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('user1__email', 'user2__email')
    readonly_fields = ('last_updated',)
    
    def get_similarity_score(self, obj):
        return f"{obj.similarity_score:.4f}"
    get_similarity_score.short_description = 'Similarity Score'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user1', 'user2')
    
    # Custom actions
    actions = ['recalculate_similarities']
    
    def recalculate_similarities(self, request, queryset):
        """
        Trigger recalculation of user similarities
        """
        from .tasks import compute_user_similarities
        
        # Get unique users from the queryset
        user_ids = set()
        for similarity in queryset:
            user_ids.add(similarity.user1.id)
            user_ids.add(similarity.user2.id)
        
        # Trigger background task
        compute_user_similarities.delay(list(user_ids))
        
        self.message_user(
            request,
            f"Triggered similarity recalculation for {len(user_ids)} users."
        )
    recalculate_similarities.short_description = "Recalculate user similarities"


@admin.register(MovieSimilarity)
class MovieSimilarityAdmin(admin.ModelAdmin):
    """
    Movie similarity admin configuration
    """
    list_display = ('movie1_id', 'movie2_id', 'get_similarity_score', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('movie1_id', 'movie2_id')
    readonly_fields = ('last_updated',)
    
    def get_similarity_score(self, obj):
        return f"{obj.similarity_score:.4f}"
    get_similarity_score.short_description = 'Similarity Score'
    
    # Custom actions
    actions = ['recalculate_movie_similarities']
    
    def recalculate_movie_similarities(self, request, queryset):
        """
        Trigger recalculation of movie similarities
        """
        from .tasks import compute_movie_similarities
        
        # Get unique movie IDs from the queryset
        movie_ids = set()
        for similarity in queryset:
            movie_ids.add(similarity.movie1_id)
            movie_ids.add(similarity.movie2_id)
        
        # Trigger background task
        compute_movie_similarities.delay(list(movie_ids))
        
        self.message_user(
            request,
            f"Triggered similarity recalculation for {len(movie_ids)} movies."
        )
    recalculate_movie_similarities.short_description = "Recalculate movie similarities"


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    """
    Recommendation cache admin configuration
    """
    list_display = ('user', 'recommendation_type', 'get_recommendations_count', 'created_at')
    list_filter = ('recommendation_type', 'created_at')
    search_fields = ('user__email', 'recommendation_type')
    readonly_fields = ('created_at', 'expires_at', 'get_recommendation_details')
    
    def get_recommendations_count(self, obj):
        if obj.recommendations and isinstance(obj.recommendations, list):
            return len(obj.recommendations)
        return 0
    get_recommendations_count.short_description = 'Recommendations Count'
    
    def get_recommendation_details(self, obj):
        if not obj.recommendations:
            return 'No recommendations available'
        
        if not isinstance(obj.recommendations, list):
            return 'Invalid recommendation data'
        
        details = []
        for i, rec in enumerate(obj.recommendations[:5]):  # Show first 5
            movie_id = rec.get('movie_id', 'N/A')
            score = rec.get('score', 0)
            title = rec.get('title', 'Unknown')
            details.append(f"{i+1}. {title} (ID: {movie_id}) - Score: {score:.3f}")
        
        if len(obj.recommendations) > 5:
            details.append(f"... and {len(obj.recommendations) - 5} more")
        
        return format_html('<br>'.join(details))
    get_recommendation_details.short_description = 'Recommendation Details'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Custom actions
    actions = ['clear_cache', 'regenerate_recommendations']
    
    def clear_cache(self, request, queryset):
        """
        Clear selected recommendation caches
        """
        count = queryset.count()
        queryset.delete()
        
        self.message_user(
            request,
            f"Successfully cleared {count} recommendation caches."
        )
    clear_cache.short_description = "Clear selected recommendation caches"
    
    def regenerate_recommendations(self, request, queryset):
        """
        Regenerate recommendations for selected users
        """
        from .tasks import generate_user_recommendations
        
        user_ids = [cache.user.id for cache in queryset]
        
        for user_id in user_ids:
            generate_user_recommendations.delay(user_id)
        
        self.message_user(
            request,
            f"Triggered recommendation regeneration for {len(user_ids)} users."
        )
    regenerate_recommendations.short_description = "Regenerate recommendations for selected users"
