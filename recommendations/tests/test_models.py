import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from recommendations.models import (
    RecommendationEngine,
    UserInteraction,
    RecommendationFeedback,
    UserSimilarity,
    MovieSimilarity,
    RecommendationCache
)
from movies.models import MovieCache
from datetime import timedelta
import json

User = get_user_model()


class RecommendationEngineModelTest(TestCase):
    """Test cases for the RecommendationEngine model"""
    
    def test_create_recommendation_engine(self):
        """Test creating a recommendation engine"""
        engine = RecommendationEngine.objects.create(
            name='Collaborative Filtering',
            algorithm_type='collaborative',
            parameters={'n_neighbors': 20, 'min_ratings': 5},
            is_active=True
        )
        
        self.assertEqual(engine.name, 'Collaborative Filtering')
        self.assertEqual(engine.algorithm_type, 'collaborative')
        self.assertEqual(engine.parameters['n_neighbors'], 20)
        self.assertTrue(engine.is_active)
        self.assertIsNotNone(engine.created_at)
    
    def test_recommendation_engine_string_representation(self):
        """Test the string representation of recommendation engine"""
        engine = RecommendationEngine.objects.create(
            name='Content-Based',
            algorithm_type='content_based'
        )
        self.assertEqual(str(engine), 'Content-Based')
    
    def test_recommendation_engine_defaults(self):
        """Test default values for recommendation engine"""
        engine = RecommendationEngine.objects.create(
            name='Test Engine',
            algorithm_type='hybrid'
        )
        
        self.assertEqual(engine.parameters, {})
        self.assertTrue(engine.is_active)
    
    def test_recommendation_engine_ordering(self):
        """Test that engines are ordered by name"""
        RecommendationEngine.objects.create(name='Z Engine', algorithm_type='collaborative')
        RecommendationEngine.objects.create(name='A Engine', algorithm_type='content_based')
        
        engines = list(RecommendationEngine.objects.all())
        self.assertEqual(engines[0].name, 'A Engine')
        self.assertEqual(engines[1].name, 'Z Engine')


class UserInteractionModelTest(TestCase):
    """Test cases for the UserInteraction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.movie = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie',
            vote_average=7.5
        )
    
    def test_create_user_interaction(self):
        """Test creating a user interaction"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='rating',
            value=8.5
        )
        
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.movie, self.movie)
        self.assertEqual(interaction.interaction_type, 'rating')
        self.assertEqual(interaction.value, 8.5)
        self.assertIsNotNone(interaction.timestamp)
    
    def test_user_interaction_string_representation(self):
        """Test the string representation of user interaction"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='view',
            value=1.0
        )
        expected_str = f"{self.user.email} - {self.movie.title} (view)"
        self.assertEqual(str(interaction), expected_str)
    
    def test_user_interaction_choices(self):
        """Test interaction type choices"""
        valid_types = ['view', 'rating', 'favorite', 'watchlist']
        
        for interaction_type in valid_types:
            interaction = UserInteraction.objects.create(
                user=self.user,
                movie=self.movie,
                interaction_type=interaction_type,
                value=1.0
            )
            self.assertEqual(interaction.interaction_type, interaction_type)
    
    def test_user_interaction_ordering(self):
        """Test that interactions are ordered by timestamp descending"""
        interaction1 = UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='view',
            value=1.0
        )
        
        interaction2 = UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='rating',
            value=8.0
        )
        
        interactions = list(UserInteraction.objects.all())
        # Most recent interaction should be first
        self.assertEqual(interactions[0].interaction_type, 'rating')
        self.assertEqual(interactions[1].interaction_type, 'view')


class RecommendationFeedbackModelTest(TestCase):
    """Test cases for the RecommendationFeedback model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.movie = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie',
            vote_average=7.5
        )
    
    def test_create_recommendation_feedback(self):
        """Test creating recommendation feedback"""
        feedback = RecommendationFeedback.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_type='collaborative',
            feedback_type='like',
            feedback_score=1.0
        )
        
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.movie, self.movie)
        self.assertEqual(feedback.recommendation_type, 'collaborative')
        self.assertEqual(feedback.feedback_type, 'like')
        self.assertEqual(feedback.feedback_score, 1.0)
    
    def test_recommendation_feedback_string_representation(self):
        """Test the string representation of recommendation feedback"""
        feedback = RecommendationFeedback.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_type='content_based',
            feedback_type='dislike'
        )
        expected_str = f"{self.user.email} - {self.movie.title} (dislike)"
        self.assertEqual(str(feedback), expected_str)
    
    def test_feedback_type_choices(self):
        """Test feedback type choices"""
        valid_types = ['like', 'dislike', 'not_interested']
        
        for feedback_type in valid_types:
            feedback = RecommendationFeedback.objects.create(
                user=self.user,
                movie=self.movie,
                recommendation_type='hybrid',
                feedback_type=feedback_type
            )
            self.assertEqual(feedback.feedback_type, feedback_type)


class UserSimilarityModelTest(TestCase):
    """Test cases for the UserSimilarity model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_create_user_similarity(self):
        """Test creating user similarity"""
        similarity = UserSimilarity.objects.create(
            user1=self.user1,
            user2=self.user2,
            similarity_score=0.85,
            algorithm_used='cosine'
        )
        
        self.assertEqual(similarity.user1, self.user1)
        self.assertEqual(similarity.user2, self.user2)
        self.assertEqual(similarity.similarity_score, 0.85)
        self.assertEqual(similarity.algorithm_used, 'cosine')
        self.assertIsNotNone(similarity.last_updated)
    
    def test_user_similarity_string_representation(self):
        """Test the string representation of user similarity"""
        similarity = UserSimilarity.objects.create(
            user1=self.user1,
            user2=self.user2,
            similarity_score=0.75
        )
        expected_str = f"{self.user1.email} - {self.user2.email} (0.75)"
        self.assertEqual(str(similarity), expected_str)
    
    def test_user_similarity_unique_together(self):
        """Test that user1-user2 combination is unique"""
        UserSimilarity.objects.create(
            user1=self.user1,
            user2=self.user2,
            similarity_score=0.8
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            UserSimilarity.objects.create(
                user1=self.user1,
                user2=self.user2,
                similarity_score=0.9
            )


class MovieSimilarityModelTest(TestCase):
    """Test cases for the MovieSimilarity model"""
    
    def setUp(self):
        self.movie1 = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie 1',
            vote_average=7.5
        )
        self.movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Test Movie 2',
            vote_average=8.0
        )
    
    def test_create_movie_similarity(self):
        """Test creating movie similarity"""
        similarity = MovieSimilarity.objects.create(
            movie1=self.movie1,
            movie2=self.movie2,
            similarity_score=0.92,
            algorithm_used='content_based'
        )
        
        self.assertEqual(similarity.movie1, self.movie1)
        self.assertEqual(similarity.movie2, self.movie2)
        self.assertEqual(similarity.similarity_score, 0.92)
        self.assertEqual(similarity.algorithm_used, 'content_based')
    
    def test_movie_similarity_string_representation(self):
        """Test the string representation of movie similarity"""
        similarity = MovieSimilarity.objects.create(
            movie1=self.movie1,
            movie2=self.movie2,
            similarity_score=0.88
        )
        expected_str = f"{self.movie1.title} - {self.movie2.title} (0.88)"
        self.assertEqual(str(similarity), expected_str)


class RecommendationCacheModelTest(TestCase):
    """Test cases for the RecommendationCache model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.movie1 = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie 1',
            vote_average=7.5
        )
        self.movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Test Movie 2',
            vote_average=8.0
        )
    
    def test_create_recommendation_cache(self):
        """Test creating recommendation cache"""
        cache = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='collaborative',
            recommendations=[12345, 67890],
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertEqual(cache.user, self.user)
        self.assertEqual(cache.recommendation_type, 'collaborative')
        self.assertEqual(cache.recommendations, [12345, 67890])
        self.assertIsNotNone(cache.created_at)
        self.assertIsNotNone(cache.expires_at)
    
    def test_recommendation_cache_string_representation(self):
        """Test the string representation of recommendation cache"""
        cache = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='content_based',
            recommendations=[12345]
        )
        expected_str = f"{self.user.email} - content_based (1 recommendations)"
        self.assertEqual(str(cache), expected_str)
    
    def test_recommendation_cache_is_expired(self):
        """Test the is_expired method"""
        # Create expired cache
        expired_cache = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='collaborative',
            recommendations=[12345],
            expires_at=timezone.now() - timedelta(hours=1)
        )
        self.assertTrue(expired_cache.is_expired())
        
        # Create valid cache
        valid_cache = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='content_based',
            recommendations=[67890],
            expires_at=timezone.now() + timedelta(hours=1)
        )
        self.assertFalse(valid_cache.is_expired())
    
    def test_recommendation_cache_ordering(self):
        """Test that cache entries are ordered by created_at descending"""
        cache1 = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='collaborative',
            recommendations=[12345]
        )
        
        cache2 = RecommendationCache.objects.create(
            user=self.user,
            recommendation_type='content_based',
            recommendations=[67890]
        )
        
        caches = list(RecommendationCache.objects.all())
        # Most recent cache should be first
        self.assertEqual(caches[0].recommendation_type, 'content_based')
        self.assertEqual(caches[1].recommendation_type, 'collaborative')