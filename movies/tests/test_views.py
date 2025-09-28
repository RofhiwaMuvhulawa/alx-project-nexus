import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from movies.models import Genre, MovieCache, UserFavorite
from movies.services import TMDbService
import json
from datetime import datetime, timezone

User = get_user_model()


class MovieDiscoveryViewTest(APITestCase):
    """Test cases for movie discovery endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test genres
        self.action_genre = Genre.objects.create(id=28, name='Action')
        self.comedy_genre = Genre.objects.create(id=35, name='Comedy')
        
        # Create test movie cache entries
        self.movie1 = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Action Movie',
            overview='An exciting action movie',
            release_date='2023-01-15',
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5,
            poster_path='/test_poster1.jpg',
            backdrop_path='/test_backdrop1.jpg',
            original_language='en',
            genre_ids=[28],
            adult=False
        )
        
        self.movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Test Comedy Movie',
            overview='A hilarious comedy',
            release_date='2023-02-20',
            vote_average=8.2,
            vote_count=1500,
            popularity=92.3,
            poster_path='/test_poster2.jpg',
            backdrop_path='/test_backdrop2.jpg',
            original_language='en',
            genre_ids=[35],
            adult=False
        )
    
    def test_get_trending_movies(self):
        """Test retrieving trending movies"""
        url = reverse('movies:trending')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('page', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('total_results', response.data)
    
    @patch('movies.services.TMDbService.get_trending_movies')
    def test_trending_movies_with_tmdb_service(self, mock_trending):
        """Test trending movies endpoint with mocked TMDb service"""
        mock_trending.return_value = {
            'page': 1,
            'results': [
                {
                    'id': 12345,
                    'title': 'Trending Movie',
                    'overview': 'A trending movie',
                    'release_date': '2023-01-15',
                    'vote_average': 8.5,
                    'vote_count': 2000,
                    'popularity': 95.0,
                    'poster_path': '/trending_poster.jpg',
                    'backdrop_path': '/trending_backdrop.jpg',
                    'original_language': 'en',
                    'genre_ids': [28, 12],
                    'adult': False
                }
            ],
            'total_pages': 1,
            'total_results': 1
        }
        
        url = reverse('movies:trending')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Trending Movie')
        mock_trending.assert_called_once()
    
    def test_get_popular_movies(self):
        """Test retrieving popular movies"""
        url = reverse('movies:popular')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_get_top_rated_movies(self):
        """Test retrieving top rated movies"""
        url = reverse('movies:top_rated')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_get_upcoming_movies(self):
        """Test retrieving upcoming movies"""
        url = reverse('movies:upcoming')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_search_movies(self):
        """Test searching movies"""
        url = reverse('movies:search')
        response = self.client.get(url, {'query': 'action'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_search_movies_without_query(self):
        """Test searching movies without query parameter"""
        url = reverse('movies:search')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('movies.services.TMDbService.search_movies')
    def test_search_movies_with_tmdb_service(self, mock_search):
        """Test search movies endpoint with mocked TMDb service"""
        mock_search.return_value = {
            'page': 1,
            'results': [
                {
                    'id': 12345,
                    'title': 'Search Result Movie',
                    'overview': 'A movie from search',
                    'release_date': '2023-01-15',
                    'vote_average': 7.8,
                    'vote_count': 800,
                    'popularity': 75.0,
                    'poster_path': '/search_poster.jpg',
                    'backdrop_path': '/search_backdrop.jpg',
                    'original_language': 'en',
                    'genre_ids': [28],
                    'adult': False
                }
            ],
            'total_pages': 1,
            'total_results': 1
        }
        
        url = reverse('movies:search')
        response = self.client.get(url, {'query': 'test movie'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Search Result Movie')
        mock_search.assert_called_once_with('test movie', page=1)
    
    def test_get_movie_details(self):
        """Test retrieving movie details"""
        url = reverse('movies:detail', kwargs={'movie_id': 12345})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tmdb_id'], 12345)
        self.assertEqual(response.data['title'], 'Test Action Movie')
    
    @patch('movies.services.TMDbService.get_movie_details')
    def test_get_movie_details_not_cached(self, mock_details):
        """Test retrieving movie details not in cache"""
        mock_details.return_value = {
            'id': 99999,
            'title': 'New Movie',
            'overview': 'A new movie not in cache',
            'release_date': '2023-03-01',
            'vote_average': 8.0,
            'vote_count': 500,
            'popularity': 80.0,
            'poster_path': '/new_poster.jpg',
            'backdrop_path': '/new_backdrop.jpg',
            'original_language': 'en',
            'genres': [{'id': 28, 'name': 'Action'}],
            'adult': False,
            'runtime': 120,
            'budget': 50000000,
            'revenue': 150000000
        }
        
        url = reverse('movies:detail', kwargs={'movie_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Movie')
        mock_details.assert_called_once_with(99999)
    
    def test_get_movie_details_invalid_id(self):
        """Test retrieving movie details with invalid ID"""
        url = reverse('movies:detail', kwargs={'movie_id': 'invalid'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_discover_movies_by_genre(self):
        """Test discovering movies by genre"""
        url = reverse('movies:discover')
        response = self.client.get(url, {'with_genres': '28'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_discover_movies_with_filters(self):
        """Test discovering movies with multiple filters"""
        url = reverse('movies:discover')
        params = {
            'with_genres': '28,35',
            'primary_release_year': '2023',
            'vote_average.gte': '7.0',
            'sort_by': 'popularity.desc'
        }
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_endpoints_require_authentication(self):
        """Test that movie endpoints require authentication"""
        self.client.force_authenticate(user=None)
        
        endpoints = [
            reverse('movies:trending'),
            reverse('movies:popular'),
            reverse('movies:top_rated'),
            reverse('movies:upcoming'),
            reverse('movies:search'),
            reverse('movies:discover'),
            reverse('movies:detail', kwargs={'movie_id': 12345})
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserFavoritesViewTest(APITestCase):
    """Test cases for user favorites endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
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
        
        # Create a favorite for testing
        self.favorite = UserFavorite.objects.create(
            user=self.user,
            movie=self.movie
        )
    
    def test_get_user_favorites(self):
        """Test retrieving user's favorite movies"""
        url = reverse('movies:favorites')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tmdb_id'], 12345)
    
    def test_add_movie_to_favorites(self):
        """Test adding a movie to favorites"""
        # Create another movie
        movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Another Movie',
            overview='Another test movie',
            release_date='2023-02-20',
            vote_average=8.0,
            vote_count=1200,
            popularity=90.0,
            poster_path='/another_poster.jpg',
            backdrop_path='/another_backdrop.jpg',
            original_language='en',
            genre_ids=[35],
            adult=False
        )
        
        url = reverse('movies:add_favorite', kwargs={'movie_id': 67890})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserFavorite.objects.filter(user=self.user, movie=movie2).exists()
        )
    
    def test_add_already_favorited_movie(self):
        """Test adding a movie that's already in favorites"""
        url = reverse('movies:add_favorite', kwargs={'movie_id': 12345})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should still have only one favorite
        self.assertEqual(
            UserFavorite.objects.filter(user=self.user, movie=self.movie).count(),
            1
        )
    
    @patch('movies.services.TMDbService.get_movie_details')
    def test_add_non_cached_movie_to_favorites(self, mock_details):
        """Test adding a movie not in cache to favorites"""
        mock_details.return_value = {
            'id': 99999,
            'title': 'New Favorite Movie',
            'overview': 'A new movie to favorite',
            'release_date': '2023-03-01',
            'vote_average': 8.5,
            'vote_count': 800,
            'popularity': 88.0,
            'poster_path': '/new_favorite_poster.jpg',
            'backdrop_path': '/new_favorite_backdrop.jpg',
            'original_language': 'en',
            'genres': [{'id': 28, 'name': 'Action'}],
            'adult': False,
            'runtime': 120,
            'budget': 40000000,
            'revenue': 120000000
        }
        
        url = reverse('movies:add_favorite', kwargs={'movie_id': 99999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that movie was cached and favorited
        cached_movie = MovieCache.objects.get(tmdb_id=99999)
        self.assertEqual(cached_movie.title, 'New Favorite Movie')
        self.assertTrue(
            UserFavorite.objects.filter(user=self.user, movie=cached_movie).exists()
        )
        mock_details.assert_called_once_with(99999)
    
    def test_remove_movie_from_favorites(self):
        """Test removing a movie from favorites"""
        url = reverse('movies:remove_favorite', kwargs={'movie_id': 12345})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            UserFavorite.objects.filter(user=self.user, movie=self.movie).exists()
        )
    
    def test_remove_non_favorited_movie(self):
        """Test removing a movie that's not in favorites"""
        # Create another movie not in favorites
        movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Not Favorited Movie',
            overview='A movie not in favorites',
            release_date='2023-02-20',
            vote_average=6.5,
            vote_count=500,
            popularity=60.0,
            poster_path='/not_fav_poster.jpg',
            backdrop_path='/not_fav_backdrop.jpg',
            original_language='en',
            genre_ids=[18],
            adult=False
        )
        
        url = reverse('movies:remove_favorite', kwargs={'movie_id': 67890})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_check_if_movie_is_favorited(self):
        """Test checking if a movie is in user's favorites"""
        url = reverse('movies:is_favorite', kwargs={'movie_id': 12345})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_favorite'])
        
        # Test with non-favorited movie
        url = reverse('movies:is_favorite', kwargs={'movie_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_favorite'])
    
    def test_favorites_are_user_specific(self):
        """Test that favorites are specific to each user"""
        # Switch to other user
        self.client.force_authenticate(user=self.other_user)
        
        # Other user should have no favorites
        url = reverse('movies:favorites')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Check if movie is favorited by other user
        url = reverse('movies:is_favorite', kwargs={'movie_id': 12345})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_favorite'])
    
    def test_favorites_endpoints_require_authentication(self):
        """Test that favorites endpoints require authentication"""
        self.client.force_authenticate(user=None)
        
        endpoints = [
            (reverse('movies:favorites'), 'get'),
            (reverse('movies:add_favorite', kwargs={'movie_id': 12345}), 'post'),
            (reverse('movies:remove_favorite', kwargs={'movie_id': 12345}), 'delete'),
            (reverse('movies:is_favorite', kwargs={'movie_id': 12345}), 'get')
        ]
        
        for url, method in endpoints:
            if method == 'get':
                response = self.client.get(url)
            elif method == 'post':
                response = self.client.post(url)
            elif method == 'delete':
                response = self.client.delete(url)
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GenreViewTest(APITestCase):
    """Test cases for genre endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test genres
        Genre.objects.create(id=28, name='Action')
        Genre.objects.create(id=35, name='Comedy')
        Genre.objects.create(id=18, name='Drama')
    
    def test_get_all_genres(self):
        """Test retrieving all movie genres"""
        url = reverse('movies:genres')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        genre_names = [genre['name'] for genre in response.data]
        self.assertIn('Action', genre_names)
        self.assertIn('Comedy', genre_names)
        self.assertIn('Drama', genre_names)
    
    def test_genres_are_ordered_by_name(self):
        """Test that genres are returned in alphabetical order"""
        url = reverse('movies:genres')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        genre_names = [genre['name'] for genre in response.data]
        self.assertEqual(genre_names, ['Action', 'Comedy', 'Drama'])
    
    def test_genres_endpoint_requires_authentication(self):
        """Test that genres endpoint requires authentication"""
        self.client.force_authenticate(user=None)
        
        url = reverse('movies:genres')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)