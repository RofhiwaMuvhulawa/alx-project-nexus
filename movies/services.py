import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import MovieCache, Genre

logger = logging.getLogger(__name__)


class TMDbService:
    """
    Service class for interacting with The Movie Database (TMDb) API.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'TMDB_API_KEY', None)
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/'
        
        if not self.api_key:
            raise ValueError("TMDb API key not configured")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Make a request to the TMDb API.
        """
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            return None
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Get detailed information about a movie.
        """
        cache_key = f"tmdb_movie_{movie_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request(f"movie/{movie_id}")
        
        if data:
            # Cache for 1 hour
            cache.set(cache_key, data, 3600)
        
        return data
    
    def search_movies(self, query: str, page: int = 1) -> Optional[Dict]:
        """
        Search for movies by title.
        """
        params = {
            'query': query,
            'page': page,
            'include_adult': False
        }
        
        return self._make_request("search/movie", params)
    
    def get_trending_movies(self, time_window: str = 'week', page: int = 1) -> Optional[Dict]:
        """
        Get trending movies.
        """
        params = {'page': page}
        return self._make_request(f"trending/movie/{time_window}", params)
    
    def get_popular_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get popular movies.
        """
        params = {'page': page}
        return self._make_request("movie/popular", params)
    
    def get_top_rated_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get top-rated movies.
        """
        params = {'page': page}
        return self._make_request("movie/top_rated", params)
    
    def get_upcoming_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get upcoming movies.
        """
        params = {'page': page}
        return self._make_request("movie/upcoming", params)
    
    def discover_movies(self, **filters) -> Optional[Dict]:
        """
        Discover movies with filters.
        """
        return self._make_request("discover/movie", filters)
    
    def get_genres(self) -> Optional[Dict]:
        """
        Get list of movie genres.
        """
        cache_key = "tmdb_genres"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request("genre/movie/list")
        
        if data:
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
        
        return data
    
    def cache_movie(self, movie_data: Dict) -> MovieCache:
        """
        Cache movie data in the database.
        """
        # Extract genres and create/get them
        genres_data = movie_data.get('genres', [])
        genre_objects = []
        
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
            genre_objects.append(genre)
        
        # Create or update movie cache
        movie, created = MovieCache.objects.update_or_create(
            tmdb_id=movie_data['id'],
            defaults={
                'title': movie_data.get('title', ''),
                'overview': movie_data.get('overview', ''),
                'poster_path': movie_data.get('poster_path'),
                'backdrop_path': movie_data.get('backdrop_path'),
                'release_date': movie_data.get('release_date'),
                'vote_average': movie_data.get('vote_average', 0),
                'vote_count': movie_data.get('vote_count', 0),
                'popularity': movie_data.get('popularity', 0),
                'adult': movie_data.get('adult', False),
                'original_language': movie_data.get('original_language', ''),
                'original_title': movie_data.get('original_title', ''),
                'runtime': movie_data.get('runtime'),
                'budget': movie_data.get('budget', 0),
                'revenue': movie_data.get('revenue', 0),
                'status': movie_data.get('status', ''),
                'tagline': movie_data.get('tagline', ''),
                'homepage': movie_data.get('homepage', ''),
                'imdb_id': movie_data.get('imdb_id'),
                'production_companies': movie_data.get('production_companies', []),
                'production_countries': movie_data.get('production_countries', []),
                'spoken_languages': movie_data.get('spoken_languages', []),
            }
        )
        
        # Set genres
        movie.genres.set(genre_objects)
        
        return movie
    
    def sync_genres(self):
        """
        Sync genres from TMDb API to local database.
        """
        genres_data = self.get_genres()
        
        if not genres_data:
            logger.error("Failed to fetch genres from TMDb")
            return
        
        for genre_data in genres_data.get('genres', []):
            Genre.objects.update_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
        
        logger.info(f"Synced {len(genres_data.get('genres', []))} genres")
    
    def get_image_url(self, path: str, size: str = 'w500') -> str:
        """
        Get full URL for TMDb image.
        """
        if not path:
            return ''
        
        return f"{self.image_base_url}{size}{path}"
    
    def get_movie_credits(self, movie_id: int) -> Optional[Dict]:
        """
        Get movie credits (cast and crew).
        """
        return self._make_request(f"movie/{movie_id}/credits")
    
    def get_movie_videos(self, movie_id: int) -> Optional[Dict]:
        """
        Get movie videos (trailers, teasers, etc.).
        """
        return self._make_request(f"movie/{movie_id}/videos")
    
    def get_movie_recommendations(self, movie_id: int, page: int = 1) -> Optional[Dict]:
        """
        Get movie recommendations based on a movie.
        """
        params = {'page': page}
        return self._make_request(f"movie/{movie_id}/recommendations", params)
    
    def get_similar_movies(self, movie_id: int, page: int = 1) -> Optional[Dict]:
        """
        Get similar movies.
        """
        params = {'page': page}
        return self._make_request(f"movie/{movie_id}/similar", params)


# Create a singleton instance
tmdb_service = TMDbService()