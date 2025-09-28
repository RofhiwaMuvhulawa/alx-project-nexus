from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from .models import MovieCache, Genre
from .services import TMDbService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_movie_cache(self):
    """
    Update movie cache with latest data from TMDb
    """
    try:
        tmdb_service = TMDbService()
        updated_count = 0
        
        # Update trending movies
        trending = tmdb_service.get_trending_movies()
        for movie in trending.get('results', []):
            movie_cache, created = MovieCache.objects.update_or_create(
                tmdb_id=movie['id'],
                defaults={
                    'data': movie,
                    'cache_type': 'trending',
                    'updated_at': timezone.now()
                }
            )
            if created or movie_cache.updated_at < timezone.now() - timezone.timedelta(hours=6):
                updated_count += 1
        
        # Update popular movies
        popular = tmdb_service.get_popular_movies()
        for movie in popular.get('results', []):
            movie_cache, created = MovieCache.objects.update_or_create(
                tmdb_id=movie['id'],
                defaults={
                    'data': movie,
                    'cache_type': 'popular',
                    'updated_at': timezone.now()
                }
            )
            if created or movie_cache.updated_at < timezone.now() - timezone.timedelta(hours=6):
                updated_count += 1
        
        # Update top rated movies
        top_rated = tmdb_service.get_top_rated_movies()
        for movie in top_rated.get('results', []):
            movie_cache, created = MovieCache.objects.update_or_create(
                tmdb_id=movie['id'],
                defaults={
                    'data': movie,
                    'cache_type': 'top_rated',
                    'updated_at': timezone.now()
                }
            )
            if created or movie_cache.updated_at < timezone.now() - timezone.timedelta(hours=6):
                updated_count += 1
        
        logger.info(f"Updated {updated_count} movie cache entries")
        return f"Successfully updated {updated_count} movie cache entries"
        
    except Exception as exc:
        logger.error(f"Error updating movie cache: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def update_genres_cache(self):
    """
    Update genres cache with latest data from TMDb
    """
    try:
        tmdb_service = TMDbService()
        genres_data = tmdb_service.get_genres()
        
        updated_count = 0
        for genre_data in genres_data.get('genres', []):
            genre, created = Genre.objects.update_or_create(
                tmdb_id=genre_data['id'],
                defaults={
                    'name': genre_data['name'],
                    'updated_at': timezone.now()
                }
            )
            if created:
                updated_count += 1
        
        logger.info(f"Updated {updated_count} genre entries")
        return f"Successfully updated {updated_count} genre entries"
        
    except Exception as exc:
        logger.error(f"Error updating genres cache: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def fetch_movie_details(self, movie_id: int):
    """
    Fetch and cache detailed movie information
    """
    try:
        tmdb_service = TMDbService()
        movie_details = tmdb_service.get_movie_details(movie_id)
        
        if movie_details:
            movie_cache, created = MovieCache.objects.update_or_create(
                tmdb_id=movie_id,
                defaults={
                    'data': movie_details,
                    'cache_type': 'details',
                    'updated_at': timezone.now()
                }
            )
            
            # Cache in Redis for faster access
            cache_key = f"movie_details_{movie_id}"
            cache.set(cache_key, movie_details, timeout=3600)  # 1 hour
            
            logger.info(f"Cached details for movie {movie_id}")
            return f"Successfully cached details for movie {movie_id}"
        else:
            logger.warning(f"No details found for movie {movie_id}")
            return f"No details found for movie {movie_id}"
            
    except Exception as exc:
        logger.error(f"Error fetching movie details for {movie_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def cleanup_old_movie_cache(self):
    """
    Clean up old movie cache entries
    """
    try:
        # Remove cache entries older than 7 days
        cutoff_date = timezone.now() - timezone.timedelta(days=7)
        deleted_count = MovieCache.objects.filter(
            updated_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old movie cache entries")
        return f"Successfully cleaned up {deleted_count} old movie cache entries"
        
    except Exception as exc:
        logger.error(f"Error cleaning up movie cache: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def warm_movie_cache(self, movie_ids: list):
    """
    Pre-warm cache for a list of movies
    """
    try:
        tmdb_service = TMDbService()
        cached_count = 0
        
        for movie_id in movie_ids:
            try:
                # Check if already cached recently
                cache_key = f"movie_details_{movie_id}"
                if cache.get(cache_key):
                    continue
                
                # Fetch and cache movie details
                movie_details = tmdb_service.get_movie_details(movie_id)
                if movie_details:
                    cache.set(cache_key, movie_details, timeout=3600)
                    cached_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to cache movie {movie_id}: {str(e)}")
                continue
        
        logger.info(f"Warmed cache for {cached_count} movies")
        return f"Successfully warmed cache for {cached_count} movies"
        
    except Exception as exc:
        logger.error(f"Error warming movie cache: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def update_movie_recommendations(self, movie_id: int):
    """
    Update recommendations for a specific movie
    """
    try:
        tmdb_service = TMDbService()
        
        # Get similar movies from TMDb
        similar_movies = tmdb_service.get_similar_movies(movie_id)
        recommendations = tmdb_service.get_movie_recommendations(movie_id)
        
        # Cache the recommendations
        cache_key_similar = f"similar_movies_{movie_id}"
        cache_key_recommendations = f"movie_recommendations_{movie_id}"
        
        cache.set(cache_key_similar, similar_movies, timeout=7200)  # 2 hours
        cache.set(cache_key_recommendations, recommendations, timeout=7200)
        
        logger.info(f"Updated recommendations for movie {movie_id}")
        return f"Successfully updated recommendations for movie {movie_id}"
        
    except Exception as exc:
        logger.error(f"Error updating recommendations for movie {movie_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def batch_update_movie_cache(self, movie_ids: list, cache_type: str = 'batch'):
    """
    Batch update movie cache for multiple movies
    """
    try:
        tmdb_service = TMDbService()
        updated_count = 0
        failed_count = 0
        
        for movie_id in movie_ids:
            try:
                movie_details = tmdb_service.get_movie_details(movie_id)
                if movie_details:
                    MovieCache.objects.update_or_create(
                        tmdb_id=movie_id,
                        defaults={
                            'data': movie_details,
                            'cache_type': cache_type,
                            'updated_at': timezone.now()
                        }
                    )
                    updated_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to update cache for movie {movie_id}: {str(e)}")
                failed_count += 1
                continue
        
        logger.info(f"Batch update completed: {updated_count} updated, {failed_count} failed")
        return f"Batch update completed: {updated_count} updated, {failed_count} failed"
        
    except Exception as exc:
        logger.error(f"Error in batch movie cache update: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))