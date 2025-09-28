from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache
from .models import (
    UserSimilarity, MovieSimilarity, RecommendationCache,
    UserInteraction, RecommendationFeedback
)
from .services import RecommendationService
from movies.models import MovieCache
from authentication.models import Favorite
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def compute_user_similarities(self):
    """
    Compute user similarities based on their interactions and preferences
    """
    try:
        users = User.objects.filter(is_active=True)
        updated_count = 0
        
        # Get user interaction data
        user_movie_matrix = {}
        
        for user in users:
            user_movies = set()
            
            # Add favorites
            favorites = Favorite.objects.filter(user=user).values_list('movie_id', flat=True)
            user_movies.update(favorites)
            
            # Add interactions
            interactions = UserInteraction.objects.filter(
                user=user,
                interaction_type__in=['view', 'like', 'rating']
            ).values_list('movie_id', flat=True)
            user_movies.update(interactions)
            
            user_movie_matrix[user.id] = user_movies
        
        # Compute similarities between users
        user_ids = list(user_movie_matrix.keys())
        
        for i, user1_id in enumerate(user_ids):
            for user2_id in user_ids[i+1:]:
                try:
                    user1_movies = user_movie_matrix[user1_id]
                    user2_movies = user_movie_matrix[user2_id]
                    
                    # Calculate Jaccard similarity
                    intersection = len(user1_movies.intersection(user2_movies))
                    union = len(user1_movies.union(user2_movies))
                    
                    if union > 0:
                        similarity = intersection / union
                        
                        # Only store significant similarities
                        if similarity > 0.1:
                            UserSimilarity.objects.update_or_create(
                                user1_id=user1_id,
                                user2_id=user2_id,
                                defaults={
                                    'similarity_score': similarity,
                                    'algorithm': 'jaccard',
                                    'updated_at': timezone.now()
                                }
                            )
                            updated_count += 1
                            
                except Exception as e:
                    logger.warning(f"Error computing similarity between users {user1_id} and {user2_id}: {str(e)}")
                    continue
        
        logger.info(f"Computed {updated_count} user similarities")
        return f"Successfully computed {updated_count} user similarities"
        
    except Exception as exc:
        logger.error(f"Error computing user similarities: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def compute_movie_similarities(self):
    """
    Compute movie similarities based on content features
    """
    try:
        movies = MovieCache.objects.all()[:1000]  # Limit to prevent memory issues
        updated_count = 0
        
        # Prepare movie features for similarity computation
        movie_features = []
        movie_ids = []
        
        for movie in movies:
            movie_data = movie.data
            
            # Create feature string from genres, overview, and keywords
            features = []
            
            # Add genres
            genres = movie_data.get('genres', [])
            for genre in genres:
                features.append(genre.get('name', ''))
            
            # Add overview
            overview = movie_data.get('overview', '')
            if overview:
                features.append(overview)
            
            # Add production companies
            companies = movie_data.get('production_companies', [])
            for company in companies:
                features.append(company.get('name', ''))
            
            movie_features.append(' '.join(features))
            movie_ids.append(movie.tmdb_id)
        
        if len(movie_features) < 2:
            logger.warning("Not enough movies to compute similarities")
            return "Not enough movies to compute similarities"
        
        # Compute TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(movie_features)
        
        # Compute cosine similarities
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Store similarities
        for i, movie1_id in enumerate(movie_ids):
            for j, movie2_id in enumerate(movie_ids[i+1:], i+1):
                similarity_score = similarity_matrix[i][j]
                
                # Only store significant similarities
                if similarity_score > 0.1:
                    MovieSimilarity.objects.update_or_create(
                        movie1_id=movie1_id,
                        movie2_id=movie2_id,
                        defaults={
                            'similarity_score': similarity_score,
                            'algorithm': 'content_based',
                            'updated_at': timezone.now()
                        }
                    )
                    updated_count += 1
        
        logger.info(f"Computed {updated_count} movie similarities")
        return f"Successfully computed {updated_count} movie similarities"
        
    except Exception as exc:
        logger.error(f"Error computing movie similarities: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def generate_user_recommendations(self, user_id: int, recommendation_type: str = 'hybrid'):
    """
    Generate and cache recommendations for a specific user
    """
    try:
        user = User.objects.get(id=user_id)
        recommendation_service = RecommendationService()
        
        # Generate recommendations
        recommendations = recommendation_service.get_personalized_recommendations(
            user=user,
            limit=50,
            recommendation_type=recommendation_type
        )
        
        # Cache the recommendations
        cache_key = f"user_recommendations_{user_id}_{recommendation_type}"
        cache.set(cache_key, recommendations, timeout=3600)  # 1 hour
        
        # Store in database cache
        RecommendationCache.objects.update_or_create(
            user=user,
            recommendation_type=recommendation_type,
            defaults={
                'recommendations': recommendations,
                'updated_at': timezone.now()
            }
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return f"Successfully generated {len(recommendations)} recommendations for user {user_id}"
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} does not exist")
        return f"User {user_id} does not exist"
    except Exception as exc:
        logger.error(f"Error generating recommendations for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def batch_generate_recommendations(self, user_ids: list = None, recommendation_type: str = 'hybrid'):
    """
    Generate recommendations for multiple users
    """
    try:
        if user_ids is None:
            # Get active users who have some interactions
            user_ids = User.objects.filter(
                is_active=True
            ).annotate(
                interaction_count=Count('userinteraction')
            ).filter(
                interaction_count__gt=0
            ).values_list('id', flat=True)[:100]  # Limit to 100 users
        
        successful_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                generate_user_recommendations.delay(user_id, recommendation_type)
                successful_count += 1
            except Exception as e:
                logger.warning(f"Failed to queue recommendations for user {user_id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Queued recommendations for {successful_count} users, {failed_count} failed")
        return f"Queued recommendations for {successful_count} users, {failed_count} failed"
        
    except Exception as exc:
        logger.error(f"Error in batch recommendation generation: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def cleanup_old_cache(self):
    """
    Clean up old recommendation cache entries
    """
    try:
        # Remove cache entries older than 24 hours
        cutoff_date = timezone.now() - timezone.timedelta(hours=24)
        
        deleted_recommendation_cache = RecommendationCache.objects.filter(
            updated_at__lt=cutoff_date
        ).delete()[0]
        
        # Remove old user similarities (older than 7 days)
        similarity_cutoff = timezone.now() - timezone.timedelta(days=7)
        deleted_user_similarities = UserSimilarity.objects.filter(
            updated_at__lt=similarity_cutoff
        ).delete()[0]
        
        # Remove old movie similarities (older than 30 days)
        movie_similarity_cutoff = timezone.now() - timezone.timedelta(days=30)
        deleted_movie_similarities = MovieSimilarity.objects.filter(
            updated_at__lt=movie_similarity_cutoff
        ).delete()[0]
        
        total_deleted = deleted_recommendation_cache + deleted_user_similarities + deleted_movie_similarities
        
        logger.info(f"Cleaned up {total_deleted} old cache entries")
        return f"Successfully cleaned up {total_deleted} old cache entries"
        
    except Exception as exc:
        logger.error(f"Error cleaning up old cache: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def update_recommendation_feedback_stats(self):
    """
    Update recommendation feedback statistics
    """
    try:
        # Calculate feedback statistics for each recommendation type
        feedback_stats = {}
        
        recommendation_types = ['hybrid', 'collaborative', 'content_based', 'popularity']
        
        for rec_type in recommendation_types:
            total_feedback = RecommendationFeedback.objects.filter(
                recommendation_type=rec_type
            ).count()
            
            positive_feedback = RecommendationFeedback.objects.filter(
                recommendation_type=rec_type,
                feedback_type='like'
            ).count()
            
            accuracy = positive_feedback / total_feedback if total_feedback > 0 else 0.0
            
            feedback_stats[rec_type] = {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'accuracy': accuracy
            }
        
        # Cache the statistics
        cache.set('recommendation_feedback_stats', feedback_stats, timeout=3600)
        
        logger.info("Updated recommendation feedback statistics")
        return "Successfully updated recommendation feedback statistics"
        
    except Exception as exc:
        logger.error(f"Error updating feedback stats: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def warm_user_recommendations(self, user_id: int):
    """
    Pre-warm recommendations cache for a specific user
    """
    try:
        user = User.objects.get(id=user_id)
        recommendation_service = RecommendationService()
        
        # Generate different types of recommendations
        recommendation_types = ['hybrid', 'collaborative', 'content_based', 'popularity']
        
        for rec_type in recommendation_types:
            try:
                recommendations = recommendation_service.get_personalized_recommendations(
                    user=user,
                    limit=20,
                    recommendation_type=rec_type
                )
                
                # Cache the recommendations
                cache_key = f"user_recommendations_{user_id}_{rec_type}"
                cache.set(cache_key, recommendations, timeout=3600)
                
            except Exception as e:
                logger.warning(f"Failed to warm {rec_type} recommendations for user {user_id}: {str(e)}")
                continue
        
        logger.info(f"Warmed recommendation cache for user {user_id}")
        return f"Successfully warmed recommendation cache for user {user_id}"
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} does not exist")
        return f"User {user_id} does not exist"
    except Exception as exc:
        logger.error(f"Error warming recommendations for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))