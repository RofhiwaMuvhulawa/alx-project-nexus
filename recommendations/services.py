import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg, Count, F
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix

from .models import (
    UserInteraction,
    RecommendationFeedback,
    RecommendationCache,
    UserSimilarity,
    MovieSimilarity
)
from movies.models import MovieCache
from authentication.models import UserPreference

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service class for generating movie recommendations using various algorithms.
    """
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
        self.min_interactions = 5  # Minimum interactions for collaborative filtering
        self.min_similarity = 0.1  # Minimum similarity threshold
    
    def get_collaborative_recommendations(
        self, 
        user: User, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate collaborative filtering recommendations.
        """
        cache_key = f"collaborative_rec_{user.id}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get user-item interaction matrix
            interactions_df = self._get_user_item_matrix()
            
            if interactions_df.empty or user.id not in interactions_df.index:
                # Fallback to popular movies for new users
                return self._get_popular_movies_fallback(limit)
            
            # Calculate user similarities
            user_similarities = self._calculate_user_similarities(interactions_df)
            
            # Get recommendations based on similar users
            recommendations = self._generate_collaborative_recommendations(
                user, interactions_df, user_similarities, limit
            )
            
            # Cache the results
            cache.set(cache_key, recommendations, self.cache_timeout)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {str(e)}")
            return self._get_popular_movies_fallback(limit)
    
    def get_content_based_recommendations(
        self, 
        movie_id: int, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate content-based recommendations for a specific movie.
        """
        cache_key = f"content_rec_{movie_id}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get movie features
            movie_features = self._get_movie_features()
            
            if movie_features.empty or movie_id not in movie_features.index:
                return []
            
            # Calculate movie similarities
            similarities = self._calculate_movie_similarities(movie_features)
            
            # Get similar movies
            recommendations = self._generate_content_recommendations(
                movie_id, similarities, limit
            )
            
            # Cache the results
            cache.set(cache_key, recommendations, self.cache_timeout)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in content-based filtering: {str(e)}")
            return []
    
    def get_content_based_recommendations_for_user(
        self, 
        user: User, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate content-based recommendations based on user's preferences.
        """
        cache_key = f"content_user_rec_{user.id}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get user's favorite movies and preferences
            user_movies = self._get_user_favorite_movies(user)
            user_preferences = self._get_user_preferences(user)
            
            if not user_movies:
                return self._get_popular_movies_by_preferences(user_preferences, limit)
            
            # Get content-based recommendations for each favorite movie
            all_recommendations = []
            for movie_id in user_movies[:5]:  # Limit to top 5 favorites
                movie_recs = self.get_content_based_recommendations(movie_id, limit // 2)
                all_recommendations.extend(movie_recs)
            
            # Remove duplicates and sort by score
            seen_movies = set()
            unique_recommendations = []
            
            for rec in sorted(all_recommendations, key=lambda x: x['score'], reverse=True):
                if rec['movie_id'] not in seen_movies and rec['movie_id'] not in user_movies:
                    seen_movies.add(rec['movie_id'])
                    unique_recommendations.append(rec)
                    
                    if len(unique_recommendations) >= limit:
                        break
            
            # Cache the results
            cache.set(cache_key, unique_recommendations, self.cache_timeout)
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Error in user content-based filtering: {str(e)}")
            return self._get_popular_movies_fallback(limit)
    
    def get_hybrid_recommendations(
        self, 
        user: User, 
        limit: int = 20, 
        collaborative_weight: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Generate hybrid recommendations combining collaborative and content-based.
        """
        cache_key = f"hybrid_rec_{user.id}_{limit}_{collaborative_weight}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Get collaborative recommendations
            collaborative_recs = self.get_collaborative_recommendations(user, limit * 2)
            
            # Get content-based recommendations
            content_recs = self.get_content_based_recommendations_for_user(user, limit * 2)
            
            # Combine recommendations with weights
            hybrid_recs = self._combine_recommendations(
                collaborative_recs, 
                content_recs, 
                collaborative_weight,
                limit
            )
            
            # Cache the results
            cache.set(cache_key, hybrid_recs, self.cache_timeout)
            
            return hybrid_recs
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendations: {str(e)}")
            return self._get_popular_movies_fallback(limit)
    
    def get_personalized_recommendations(
        self, 
        user: User, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on complete user profile.
        """
        cache_key = f"personalized_rec_{user.id}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Analyze user behavior to determine best algorithm mix
            user_profile = self._analyze_user_profile(user)
            
            # Adjust weights based on user profile
            if user_profile['interaction_count'] < self.min_interactions:
                # New user - rely more on content-based and popular movies
                collaborative_weight = 0.2
                content_weight = 0.5
                popular_weight = 0.3
            elif user_profile['diversity_score'] > 0.7:
                # Diverse user - balanced approach
                collaborative_weight = 0.5
                content_weight = 0.4
                popular_weight = 0.1
            else:
                # Focused user - more collaborative filtering
                collaborative_weight = 0.7
                content_weight = 0.3
                popular_weight = 0.0
            
            # Get recommendations from different algorithms
            collaborative_recs = self.get_collaborative_recommendations(user, limit)
            content_recs = self.get_content_based_recommendations_for_user(user, limit)
            popular_recs = self._get_popular_movies_fallback(limit) if popular_weight > 0 else []
            
            # Combine with personalized weights
            personalized_recs = self._combine_multiple_recommendations(
                [
                    (collaborative_recs, collaborative_weight),
                    (content_recs, content_weight),
                    (popular_recs, popular_weight)
                ],
                limit
            )
            
            # Apply user preferences filter
            filtered_recs = self._apply_user_preferences_filter(user, personalized_recs)
            
            # Cache the results
            cache.set(cache_key, filtered_recs, self.cache_timeout)
            
            return filtered_recs
            
        except Exception as e:
            logger.error(f"Error in personalized recommendations: {str(e)}")
            return self._get_popular_movies_fallback(limit)
    
    def _get_user_item_matrix(self) -> pd.DataFrame:
        """
        Create user-item interaction matrix from ratings.
        """
        interactions = UserInteraction.objects.filter(
            interaction_type='rating',
            rating__isnull=False
        ).values('user_id', 'movie_id', 'rating')
        
        if not interactions:
            return pd.DataFrame()
        
        df = pd.DataFrame(interactions)
        return df.pivot_table(
            index='user_id', 
            columns='movie_id', 
            values='rating', 
            fill_value=0
        )
    
    def _calculate_user_similarities(self, interactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate user-user similarities using cosine similarity.
        """
        # Use cosine similarity
        user_similarities = cosine_similarity(interactions_df.values)
        
        return pd.DataFrame(
            user_similarities,
            index=interactions_df.index,
            columns=interactions_df.index
        )
    
    def _generate_collaborative_recommendations(
        self, 
        user: User, 
        interactions_df: pd.DataFrame, 
        similarities: pd.DataFrame, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations using collaborative filtering.
        """
        user_id = user.id
        
        if user_id not in similarities.index:
            return []
        
        # Get similar users
        similar_users = similarities.loc[user_id].sort_values(ascending=False)[1:11]  # Top 10 similar users
        
        # Get movies rated by similar users but not by current user
        user_movies = set(interactions_df.loc[user_id][interactions_df.loc[user_id] > 0].index)
        
        recommendations = {}
        
        for similar_user_id, similarity_score in similar_users.items():
            if similarity_score < self.min_similarity:
                continue
            
            similar_user_movies = interactions_df.loc[similar_user_id]
            
            for movie_id, rating in similar_user_movies.items():
                if rating > 0 and movie_id not in user_movies:
                    if movie_id not in recommendations:
                        recommendations[movie_id] = 0
                    recommendations[movie_id] += similarity_score * rating
        
        # Sort and return top recommendations
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'movie_id': movie_id,
                'score': score,
                'algorithm': 'collaborative_filtering'
            }
            for movie_id, score in sorted_recs
        ]
    
    def _get_movie_features(self) -> pd.DataFrame:
        """
        Get movie features for content-based filtering.
        """
        movies = MovieCache.objects.all().values(
            'tmdb_id', 'genres', 'overview', 'vote_average', 'popularity'
        )
        
        if not movies:
            return pd.DataFrame()
        
        df = pd.DataFrame(movies)
        
        # Create feature vectors
        features = []
        for _, movie in df.iterrows():
            feature_text = f"{movie['genres']} {movie['overview']}"
            features.append(feature_text)
        
        # Use TF-IDF for text features
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(features)
        
        # Convert to DataFrame
        feature_df = pd.DataFrame(
            tfidf_matrix.toarray(),
            index=df['tmdb_id'].values
        )
        
        return feature_df
    
    def _calculate_movie_similarities(self, movie_features: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate movie-movie similarities using cosine similarity.
        """
        similarities = cosine_similarity(movie_features.values)
        
        return pd.DataFrame(
            similarities,
            index=movie_features.index,
            columns=movie_features.index
        )
    
    def _generate_content_recommendations(
        self, 
        movie_id: int, 
        similarities: pd.DataFrame, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Generate content-based recommendations for a movie.
        """
        if movie_id not in similarities.index:
            return []
        
        similar_movies = similarities.loc[movie_id].sort_values(ascending=False)[1:limit+1]
        
        return [
            {
                'movie_id': int(similar_movie_id),
                'score': float(similarity_score),
                'algorithm': 'content_based'
            }
            for similar_movie_id, similarity_score in similar_movies.items()
            if similarity_score > self.min_similarity
        ]
    
    def _get_user_favorite_movies(self, user: User) -> List[int]:
        """
        Get user's favorite movies based on high ratings and interactions.
        """
        favorites = UserInteraction.objects.filter(
            user=user
        ).filter(
            Q(interaction_type='rating', rating__gte=7) |
            Q(interaction_type='watchlist')
        ).values_list('movie_id', flat=True).distinct()
        
        return list(favorites)
    
    def _get_user_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get user preferences.
        """
        try:
            preferences = UserPreference.objects.get(user=user)
            return {
                'favorite_genres': preferences.favorite_genres,
                'min_rating': preferences.min_rating,
                'max_rating': preferences.max_rating,
                'min_year': preferences.min_year,
                'max_year': preferences.max_year
            }
        except UserPreference.DoesNotExist:
            return {}
    
    def _get_popular_movies_fallback(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get popular movies as fallback recommendations.
        """
        popular_movies = MovieCache.objects.filter(
            vote_average__gte=7.0
        ).order_by('-popularity')[:limit]
        
        return [
            {
                'movie_id': movie.tmdb_id,
                'score': movie.vote_average / 10.0,
                'algorithm': 'popular'
            }
            for movie in popular_movies
        ]
    
    def _get_popular_movies_by_preferences(
        self, 
        preferences: Dict[str, Any], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get popular movies filtered by user preferences.
        """
        queryset = MovieCache.objects.filter(vote_average__gte=7.0)
        
        if preferences.get('favorite_genres'):
            # Filter by genres (assuming genres is stored as JSON)
            for genre in preferences['favorite_genres']:
                queryset = queryset.filter(genres__icontains=genre)
        
        if preferences.get('min_year'):
            queryset = queryset.filter(release_date__year__gte=preferences['min_year'])
        
        if preferences.get('max_year'):
            queryset = queryset.filter(release_date__year__lte=preferences['max_year'])
        
        popular_movies = queryset.order_by('-popularity')[:limit]
        
        return [
            {
                'movie_id': movie.tmdb_id,
                'score': movie.vote_average / 10.0,
                'algorithm': 'popular_filtered'
            }
            for movie in popular_movies
        ]
    
    def _combine_recommendations(
        self, 
        collaborative_recs: List[Dict], 
        content_recs: List[Dict], 
        collaborative_weight: float, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Combine collaborative and content-based recommendations.
        """
        combined_scores = {}
        
        # Add collaborative recommendations
        for rec in collaborative_recs:
            movie_id = rec['movie_id']
            combined_scores[movie_id] = rec['score'] * collaborative_weight
        
        # Add content-based recommendations
        content_weight = 1.0 - collaborative_weight
        for rec in content_recs:
            movie_id = rec['movie_id']
            if movie_id in combined_scores:
                combined_scores[movie_id] += rec['score'] * content_weight
            else:
                combined_scores[movie_id] = rec['score'] * content_weight
        
        # Sort and return top recommendations
        sorted_recs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'movie_id': movie_id,
                'score': score,
                'algorithm': 'hybrid'
            }
            for movie_id, score in sorted_recs
        ]
    
    def _combine_multiple_recommendations(
        self, 
        recommendation_lists: List[Tuple[List[Dict], float]], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Combine multiple recommendation lists with weights.
        """
        combined_scores = {}
        
        for recommendations, weight in recommendation_lists:
            for rec in recommendations:
                movie_id = rec['movie_id']
                if movie_id in combined_scores:
                    combined_scores[movie_id] += rec['score'] * weight
                else:
                    combined_scores[movie_id] = rec['score'] * weight
        
        # Sort and return top recommendations
        sorted_recs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'movie_id': movie_id,
                'score': score,
                'algorithm': 'personalized'
            }
            for movie_id, score in sorted_recs
        ]
    
    def _analyze_user_profile(self, user: User) -> Dict[str, Any]:
        """
        Analyze user profile to determine recommendation strategy.
        """
        interactions = UserInteraction.objects.filter(user=user)
        
        interaction_count = interactions.count()
        
        # Calculate genre diversity
        rated_movies = interactions.filter(
            interaction_type='rating',
            rating__isnull=False
        ).values_list('movie_id', flat=True)
        
        if rated_movies:
            movies = MovieCache.objects.filter(tmdb_id__in=rated_movies)
            all_genres = []
            for movie in movies:
                if movie.genres:
                    all_genres.extend(movie.genres.split(', '))
            
            unique_genres = len(set(all_genres))
            total_genres = len(all_genres)
            diversity_score = unique_genres / max(total_genres, 1)
        else:
            diversity_score = 0
        
        return {
            'interaction_count': interaction_count,
            'diversity_score': diversity_score
        }
    
    def _apply_user_preferences_filter(
        self, 
        user: User, 
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter recommendations based on user preferences.
        """
        preferences = self._get_user_preferences(user)
        
        if not preferences:
            return recommendations
        
        filtered_recs = []
        movie_ids = [rec['movie_id'] for rec in recommendations]
        movies = MovieCache.objects.filter(tmdb_id__in=movie_ids)
        movie_dict = {movie.tmdb_id: movie for movie in movies}
        
        for rec in recommendations:
            movie = movie_dict.get(rec['movie_id'])
            if not movie:
                continue
            
            # Check rating preferences
            if preferences.get('min_rating') and movie.vote_average < preferences['min_rating']:
                continue
            
            if preferences.get('max_rating') and movie.vote_average > preferences['max_rating']:
                continue
            
            # Check year preferences
            if movie.release_date:
                movie_year = movie.release_date.year
                if preferences.get('min_year') and movie_year < preferences['min_year']:
                    continue
                
                if preferences.get('max_year') and movie_year > preferences['max_year']:
                    continue
            
            filtered_recs.append(rec)
        
        return filtered_recs