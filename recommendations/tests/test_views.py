import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from recommendations.models import (
    RecommendationEngine,
    UserInteraction,
    RecommendationFeedback,
    RecommendationCache
)
from movies.models import MovieCache, Genre, UserFavorite
from authentication.models import UserPreference
from datetime import datetime, timezone, timedelta
from django.utils import timezone as django_timezone
import json

User = get_user_model()


class RecommendationViewTest(APITestCase):
    """Test cases for movie recommendation endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test genres
        self.action_genre = Genre.objects.create(id=28, name='Action')
        self.comedy_genre = Genre.objects.create(id=35, name='Comedy')
        self.drama_genre = Genre.objects.create(id=18, name='Drama')
        
        # Create test movies
        self.movie1 = MovieCache.objects.create(
            tmdb_id=12345,
            title='Action Movie 1',
            overview='An exciting action movie',
            release_date='2023-01-15',
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5,
            poster_path='/action1_poster.jpg',
            backdrop_path='/action1_backdrop.jpg',
            original_language='en',
            genre_ids=[28],
            adult=False
        )
        
        self.movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Comedy Movie 1',
            overview='A hilarious comedy',
            release_date='2023-02-20',
            vote_average=8.2,
            vote_count=1500,
            popularity=92.3,
            poster_path='/comedy1_poster.jpg',
            backdrop_path='/comedy1_backdrop.jpg',
            original_language='en',
            genre_ids=[35],
            adult=False
        )
        
        self.movie3 = MovieCache.objects.create(
            tmdb_id=11111,
            title='Drama Movie 1',
            overview='A compelling drama',
            release_date='2023-03-10',
            vote_average=8.8,
            vote_count=2000,
            popularity=78.9,
            poster_path='/drama1_poster.jpg',
            backdrop_path='/drama1_backdrop.jpg',
            original_language='en',
            genre_ids=[18],
            adult=False
        )
        
        # Create recommendation engines
        self.collaborative_engine = RecommendationEngine.objects.create(
            name='Collaborative Filtering',
            algorithm_type='collaborative',
            parameters={'n_neighbors': 20, 'min_ratings': 5},
            is_active=True
        )
        
        self.content_engine = RecommendationEngine.objects.create(
            name='Content-Based Filtering',
            algorithm_type='content_based',
            parameters={'similarity_threshold': 0.7},
            is_active=True
        )
        
        # Create user preferences
        self.user_preference = UserPreference.objects.create(
            user=self.user,
            min_rating=7.0,
            language='en'
        )
        self.user_preference.preferred_genres.add(self.action_genre, self.drama_genre)
        
        # Create some user interactions
        UserInteraction.objects.create(
            user=self.user,
            movie=self.movie1,
            interaction_type='rating',
            value=8.5
        )
        
        UserInteraction.objects.create(
            user=self.user,
            movie=self.movie3,
            interaction_type='rating',
            value=9.0
        )
        
        # Add a favorite
        UserFavorite.objects.create(user=self.user, movie=self.movie1)
    
    @patch('recommendations.services.RecommendationService.get_collaborative_recommendations')
    def test_get_collaborative_recommendations(self, mock_collaborative):
        """Test getting collaborative filtering recommendations"""
        mock_collaborative.return_value = [
            {'movie_id': 67890, 'score': 0.85, 'reason': 'Users with similar taste liked this'},
            {'movie_id': 11111, 'score': 0.78, 'reason': 'Highly rated by similar users'}
        ]
        
        url = reverse('recommendations:collaborative')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertEqual(len(response.data['recommendations']), 2)
        self.assertEqual(response.data['recommendations'][0]['movie']['tmdb_id'], 67890)
        mock_collaborative.assert_called_once_with(self.user, limit=10)
    
    @patch('recommendations.services.RecommendationService.get_content_based_recommendations')
    def test_get_content_based_recommendations(self, mock_content):
        """Test getting content-based recommendations"""
        mock_content.return_value = [
            {'movie_id': 67890, 'score': 0.92, 'reason': 'Similar to your favorite Action movies'},
            {'movie_id': 11111, 'score': 0.88, 'reason': 'Matches your preferred genres'}
        ]
        
        url = reverse('recommendations:content_based')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertEqual(len(response.data['recommendations']), 2)
        self.assertEqual(response.data['recommendations'][0]['movie']['tmdb_id'], 67890)
        mock_content.assert_called_once_with(self.user, limit=10)
    
    @patch('recommendations.services.RecommendationService.get_hybrid_recommendations')
    def test_get_hybrid_recommendations(self, mock_hybrid):
        """Test getting hybrid recommendations"""
        mock_hybrid.return_value = [
            {'movie_id': 67890, 'score': 0.89, 'reason': 'Combined collaborative and content-based score'},
            {'movie_id': 11111, 'score': 0.83, 'reason': 'High similarity and user preference match'}
        ]
        
        url = reverse('recommendations:hybrid')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertEqual(len(response.data['recommendations']), 2)
        self.assertEqual(response.data['recommendations'][0]['movie']['tmdb_id'], 67890)
        mock_hybrid.assert_called_once_with(self.user, limit=10)
    
    def test_get_recommendations_with_custom_limit(self):
        """Test getting recommendations with custom limit"""
        url = reverse('recommendations:collaborative')
        response = self.client.get(url, {'limit': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The actual limit testing would depend on the service implementation
    
    def test_get_recommendations_with_invalid_limit(self):
        """Test getting recommendations with invalid limit"""
        url = reverse('recommendations:collaborative')
        response = self.client.get(url, {'limit': 'invalid'})
        
        # Should use default limit and not fail
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_personalized_recommendations(self):
        """Test getting personalized recommendations based on user preferences"""
        url = reverse('recommendations:personalized')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertIn('algorithm_used', response.data)
    
    def test_recommendations_require_authentication(self):
        """Test that recommendation endpoints require authentication"""
        self.client.force_authenticate(user=None)
        
        endpoints = [
            reverse('recommendations:collaborative'),
            reverse('recommendations:content_based'),
            reverse('recommendations:hybrid'),
            reverse('recommendations:personalized')
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_recommendations_with_no_user_data(self):
        """Test recommendations for user with no interaction data"""
        # Create a new user with no interactions
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=new_user)
        
        url = reverse('recommendations:collaborative')
        response = self.client.get(url)
        
        # Should still return 200 but might have empty or fallback recommendations
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)


class RecommendationFeedbackViewTest(APITestCase):
    """Test cases for recommendation feedback endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test movie
        self.movie = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie',
            overview='A test movie',
            release_date='2023-01-15',
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5,
            poster_path='/test_poster.jpg',
            backdrop_path='/test_backdrop.jpg',
            original_language='en',
            genre_ids=[28],
            adult=False
        )
    
    def test_submit_positive_feedback(self):
        """Test submitting positive feedback for a recommendation"""
        url = reverse('recommendations:feedback')
        feedback_data = {
            'movie_id': 12345,
            'recommendation_type': 'collaborative',
            'feedback_type': 'like',
            'feedback_score': 1.0
        }
        
        response = self.client.post(url, feedback_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created
        feedback = RecommendationFeedback.objects.get(
            user=self.user,
            movie=self.movie
        )
        self.assertEqual(feedback.feedback_type, 'like')
        self.assertEqual(feedback.recommendation_type, 'collaborative')
        self.assertEqual(feedback.feedback_score, 1.0)
    
    def test_submit_negative_feedback(self):
        """Test submitting negative feedback for a recommendation"""
        url = reverse('recommendations:feedback')
        feedback_data = {
            'movie_id': 12345,
            'recommendation_type': 'content_based',
            'feedback_type': 'dislike',
            'feedback_score': -1.0
        }
        
        response = self.client.post(url, feedback_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created
        feedback = RecommendationFeedback.objects.get(
            user=self.user,
            movie=self.movie
        )
        self.assertEqual(feedback.feedback_type, 'dislike')
        self.assertEqual(feedback.recommendation_type, 'content_based')
        self.assertEqual(feedback.feedback_score, -1.0)
    
    def test_submit_not_interested_feedback(self):
        """Test submitting 'not interested' feedback"""
        url = reverse('recommendations:feedback')
        feedback_data = {
            'movie_id': 12345,
            'recommendation_type': 'hybrid',
            'feedback_type': 'not_interested'
        }
        
        response = self.client.post(url, feedback_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify feedback was created
        feedback = RecommendationFeedback.objects.get(
            user=self.user,
            movie=self.movie
        )
        self.assertEqual(feedback.feedback_type, 'not_interested')
        self.assertEqual(feedback.recommendation_type, 'hybrid')
    
    def test_update_existing_feedback(self):
        """Test updating existing feedback for the same movie"""
        # Create initial feedback
        RecommendationFeedback.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_type='collaborative',
            feedback_type='like',
            feedback_score=1.0
        )
        
        url = reverse('recommendations:feedback')
        feedback_data = {
            'movie_id': 12345,
            'recommendation_type': 'collaborative',
            'feedback_type': 'dislike',
            'feedback_score': -1.0
        }
        
        response = self.client.post(url, feedback_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify feedback was updated
        feedback = RecommendationFeedback.objects.get(
            user=self.user,
            movie=self.movie
        )
        self.assertEqual(feedback.feedback_type, 'dislike')
        self.assertEqual(feedback.feedback_score, -1.0)
        
        # Should still have only one feedback record
        self.assertEqual(
            RecommendationFeedback.objects.filter(
                user=self.user,
                movie=self.movie
            ).count(),
            1
        )
    
    def test_submit_feedback_for_nonexistent_movie(self):
        """Test submitting feedback for a non-existent movie"""
        url = reverse('recommendations:feedback')
        feedback_data = {
            'movie_id': 99999,
            'recommendation_type': 'collaborative',
            'feedback_type': 'like'
        }
        
        response = self.client.post(url, feedback_data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_submit_feedback_with_invalid_data(self):
        """Test submitting feedback with invalid data"""
        url = reverse('recommendations:feedback')
        
        # Missing required fields
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid feedback type
        invalid_data = {
            'movie_id': 12345,
            'recommendation_type': 'collaborative',
            'feedback_type': 'invalid_type'
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid recommendation type
        invalid_data = {
            'movie_id': 12345,
            'recommendation_type': 'invalid_algorithm',
            'feedback_type': 'like'
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_user_feedback_history(self):
        """Test retrieving user's feedback history"""
        # Create some feedback
        RecommendationFeedback.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_type='collaborative',
            feedback_type='like',
            feedback_score=1.0
        )
        
        url = reverse('recommendations:feedback_history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['feedback_type'], 'like')
    
    def test_feedback_requires_authentication(self):
        """Test that feedback endpoints require authentication"""
        self.client.force_authenticate(user=None)
        
        # Test feedback submission
        url = reverse('recommendations:feedback')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test feedback history
        url = reverse('recommendations:feedback_history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserInteractionViewTest(APITestCase):
    """Test cases for user interaction tracking endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test movie
        self.movie = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie',
            overview='A test movie',
            release_date='2023-01-15',
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5,
            poster_path='/test_poster.jpg',
            backdrop_path='/test_backdrop.jpg',
            original_language='en',
            genre_ids=[28],
            adult=False
        )
    
    def test_track_movie_view(self):
        """Test tracking a movie view interaction"""
        url = reverse('recommendations:track_interaction')
        interaction_data = {
            'movie_id': 12345,
            'interaction_type': 'view',
            'value': 1.0
        }
        
        response = self.client.post(url, interaction_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify interaction was created
        interaction = UserInteraction.objects.get(
            user=self.user,
            movie=self.movie,
            interaction_type='view'
        )
        self.assertEqual(interaction.value, 1.0)
    
    def test_track_movie_rating(self):
        """Test tracking a movie rating interaction"""
        url = reverse('recommendations:track_interaction')
        interaction_data = {
            'movie_id': 12345,
            'interaction_type': 'rating',
            'value': 8.5
        }
        
        response = self.client.post(url, interaction_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify interaction was created
        interaction = UserInteraction.objects.get(
            user=self.user,
            movie=self.movie,
            interaction_type='rating'
        )
        self.assertEqual(interaction.value, 8.5)
    
    def test_track_watchlist_interaction(self):
        """Test tracking a watchlist interaction"""
        url = reverse('recommendations:track_interaction')
        interaction_data = {
            'movie_id': 12345,
            'interaction_type': 'watchlist',
            'value': 1.0
        }
        
        response = self.client.post(url, interaction_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify interaction was created
        interaction = UserInteraction.objects.get(
            user=self.user,
            movie=self.movie,
            interaction_type='watchlist'
        )
        self.assertEqual(interaction.value, 1.0)
    
    def test_update_existing_interaction(self):
        """Test updating an existing interaction"""
        # Create initial interaction
        UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='rating',
            value=7.0
        )
        
        url = reverse('recommendations:track_interaction')
        interaction_data = {
            'movie_id': 12345,
            'interaction_type': 'rating',
            'value': 8.5
        }
        
        response = self.client.post(url, interaction_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify interaction was updated
        interaction = UserInteraction.objects.get(
            user=self.user,
            movie=self.movie,
            interaction_type='rating'
        )
        self.assertEqual(interaction.value, 8.5)
        
        # Should still have only one interaction record
        self.assertEqual(
            UserInteraction.objects.filter(
                user=self.user,
                movie=self.movie,
                interaction_type='rating'
            ).count(),
            1
        )
    
    def test_track_interaction_for_nonexistent_movie(self):
        """Test tracking interaction for a non-existent movie"""
        url = reverse('recommendations:track_interaction')
        interaction_data = {
            'movie_id': 99999,
            'interaction_type': 'view',
            'value': 1.0
        }
        
        response = self.client.post(url, interaction_data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_track_interaction_with_invalid_data(self):
        """Test tracking interaction with invalid data"""
        url = reverse('recommendations:track_interaction')
        
        # Missing required fields
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid interaction type
        invalid_data = {
            'movie_id': 12345,
            'interaction_type': 'invalid_type',
            'value': 1.0
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid value for rating
        invalid_data = {
            'movie_id': 12345,
            'interaction_type': 'rating',
            'value': 15.0  # Rating should be 0-10
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_user_interactions(self):
        """Test retrieving user's interaction history"""
        # Create some interactions
        UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='view',
            value=1.0
        )
        
        UserInteraction.objects.create(
            user=self.user,
            movie=self.movie,
            interaction_type='rating',
            value=8.0
        )
        
        url = reverse('recommendations:user_interactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_interaction_tracking_requires_authentication(self):
        """Test that interaction tracking requires authentication"""
        self.client.force_authenticate(user=None)
        
        # Test interaction tracking
        url = reverse('recommendations:track_interaction')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test interaction history
        url = reverse('recommendations:user_interactions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)