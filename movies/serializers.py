from rest_framework import serializers
from .models import MovieCache, Genre, UserFavorite


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for movie genres.
    """
    class Meta:
        model = Genre
        fields = ('id', 'name', 'tmdb_id')


class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for basic movie information.
    """
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = MovieCache
        fields = (
            'id', 'tmdb_id', 'title', 'overview', 'poster_path',
            'backdrop_path', 'release_date', 'vote_average', 'vote_count',
            'popularity', 'adult', 'original_language', 'original_title',
            'genres'
        )


class MovieDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed movie information.
    """
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = MovieCache
        fields = (
            'id', 'tmdb_id', 'title', 'overview', 'poster_path',
            'backdrop_path', 'release_date', 'vote_average', 'vote_count',
            'popularity', 'adult', 'original_language', 'original_title',
            'runtime', 'budget', 'revenue', 'status', 'tagline',
            'homepage', 'imdb_id', 'production_companies',
            'production_countries', 'spoken_languages', 'genres',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class UserFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for user favorite movies.
    """
    movie = MovieSerializer(source='get_movie', read_only=True)
    
    class Meta:
        model = UserFavorite
        fields = ('id', 'movie_id', 'movie', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def validate_movie_id(self, value):
        """
        Validate that the movie exists.
        """
        from .services import TMDbService
        
        tmdb_service = TMDbService()
        movie_data = tmdb_service.get_movie_details(value)
        
        if not movie_data:
            raise serializers.ValidationError("Movie not found.")
        
        return value