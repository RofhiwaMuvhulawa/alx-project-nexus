from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserPreference, Favorite


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin configuration
    """
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """
    User preference admin configuration
    """
    list_display = ('user', 'get_preferred_genres', 'min_rating', 'language', 'updated_at')
    list_filter = ('language', 'min_rating', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('updated_at',)
    ordering = ('-updated_at',)
    
    def get_preferred_genres(self, obj):
        return ', '.join([str(genre_id) for genre_id in obj.preferred_genres]) if obj.preferred_genres else 'None'
    get_preferred_genres.short_description = 'Preferred Genres'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    User favorites admin configuration
    """
    list_display = ('user', 'movie_id', 'movie_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'movie_id', 'movie_title')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
