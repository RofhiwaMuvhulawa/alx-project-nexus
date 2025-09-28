import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from movies.models import Genre, MovieCache, MovieGenre, RecommendationHistory
from datetime import timedelta
import json

User = get_user_model()


class GenreModelTest(TestCase):
    """Test cases for the Genre model"""
    
    def test_create_genre(self):
        """Test creating a genre"""
        genre = Genre.objects.create(name='Action')
        
        self.assertEqual(genre.name, 'Action')
        self.assertIsNotNone(genre.id)
    
    def test_genre_string_representation(self):
        """Test the string representation of genre"""
        genre = Genre.objects.create(name='Comedy')
        self.assertEqual(str(genre), 'Comedy')
    
    def test_genre_unique_name(self):
        """Test that genre names are unique"""
        Genre.objects.create(name='Drama')
        
        with self.assertRaises(Exception):  # IntegrityError
            Genre.objects.create(name='Drama')
    
    def test_genre_ordering(self):
        """Test that genres are ordered by name"""
        Genre.objects.create(name='Thriller')
        Genre.objects.create(name='Action')
        Genre.objects.create(name='Comedy')
        
        genres = list(Genre.objects.all())
        genre_names = [genre.name for genre in genres]
        
        self.assertEqual(genre_names, ['Action', 'Comedy', 'Thriller'])


class MovieCacheModelTest(TestCase):
    """Test cases for the MovieCache model"""
    
    def setUp(self):
        self.movie_data = {
            'tmdb_id': 12345,
            'title': 'Test Movie',
            'overview': 'A test movie for testing purposes',
            'release_date': '2023-01-01',
            'vote_average': 7.5,
            'vote_count': 1000,
            'popularity': 85.5,
            'poster_path': '/test_poster.jpg',
            'backdrop_path': '/test_backdrop.jpg',
            'original_language': 'en',
            'original_title': 'Test Movie Original',
            'adult': False,
            'video': False,
            'genre_ids': [28, 35]  # Action, Comedy
        }
    
    def test_create_movie_cache(self):
        """Test creating a movie cache entry"""
        movie = MovieCache.objects.create(**self.movie_data)
        
        self.assertEqual(movie.tmdb_id, self.movie_data['tmdb_id'])
        self.assertEqual(movie.title, self.movie_data['title'])
        self.assertEqual(movie.vote_average, self.movie_data['vote_average'])
        self.assertIsNotNone(movie.cached_at)
    
    def test_movie_cache_string_representation(self):
        """Test the string representation of movie cache"""
        movie = MovieCache.objects.create(**self.movie_data)
        expected_str = f"{self.movie_data['title']} ({self.movie_data['tmdb_id']})"
        self.assertEqual(str(movie), expected_str)
    
    def test_movie_cache_unique_tmdb_id(self):
        """Test that tmdb_id is unique"""
        MovieCache.objects.create(**self.movie_data)
        
        with self.assertRaises(Exception):  # IntegrityError
            MovieCache.objects.create(**self.movie_data)
    
    def test_movie_cache_ordering(self):
        """Test that movies are ordered by cached_at descending"""
        movie1 = MovieCache.objects.create(
            tmdb_id=1,
            title='Movie 1',
            vote_average=7.0
        )
        movie2 = MovieCache.objects.create(
            tmdb_id=2,
            title='Movie 2',
            vote_average=8.0
        )
        
        movies = list(MovieCache.objects.all())
        # Most recently cached should be first
        self.assertEqual(movies[0].tmdb_id, 2)
        self.assertEqual(movies[1].tmdb_id, 1)
    
    def test_movie_cache_json_fields(self):
        """Test JSON fields in movie cache"""
        movie = MovieCache.objects.create(**self.movie_data)
        
        self.assertEqual(movie.genre_ids, [28, 35])
        self.assertIsInstance(movie.genre_ids, list)
    
    def test_movie_cache_auto_cached_at(self):
        """Test that cached_at is automatically set"""
        before_creation = timezone.now()
        movie = MovieCache.objects.create(**self.movie_data)
        after_creation = timezone.now()
        
        self.assertGreaterEqual(movie.cached_at, before_creation)
        self.assertLessEqual(movie.cached_at, after_creation)


class MovieGenreModelTest(TestCase):
    """Test cases for the MovieGenre model"""
    
    def setUp(self):
        self.genre = Genre.objects.create(name='Action')
        self.movie = MovieCache.objects.create(
            tmdb_id=12345,
            title='Test Movie',
            vote_average=7.5
        )
    
    def test_create_movie_genre(self):
        """Test creating a movie-genre relationship"""
        movie_genre = MovieGenre.objects.create(
            movie=self.movie,
            genre=self.genre
        )
        
        self.assertEqual(movie_genre.movie, self.movie)
        self.assertEqual(movie_genre.genre, self.genre)
    
    def test_movie_genre_string_representation(self):
        """Test the string representation of movie-genre"""
        movie_genre = MovieGenre.objects.create(
            movie=self.movie,
            genre=self.genre
        )
        expected_str = f"{self.movie.title} - {self.genre.name}"
        self.assertEqual(str(movie_genre), expected_str)
    
    def test_movie_genre_unique_together(self):
        """Test that movie-genre combination is unique"""
        MovieGenre.objects.create(
            movie=self.movie,
            genre=self.genre
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            MovieGenre.objects.create(
                movie=self.movie,
                genre=self.genre
            )


class RecommendationHistoryModelTest(TestCase):
    """Test cases for the RecommendationHistory model"""
    
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
    
    def test_create_recommendation_history(self):
        """Test creating a recommendation history entry"""
        history = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=0.85,
            algorithm_used='collaborative'
        )
        
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.movie, self.movie)
        self.assertEqual(history.recommendation_score, 0.85)
        self.assertEqual(history.algorithm_used, 'collaborative')
        self.assertIsNotNone(history.recommended_at)
    
    def test_recommendation_history_string_representation(self):
        """Test the string representation of recommendation history"""
        history = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=0.75
        )
        expected_str = f"{self.user.email} - {self.movie.title} (0.75)"
        self.assertEqual(str(history), expected_str)
    
    def test_recommendation_history_ordering(self):
        """Test that recommendations are ordered by recommended_at descending"""
        history1 = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=0.8
        )
        
        # Create another movie for second recommendation
        movie2 = MovieCache.objects.create(
            tmdb_id=67890,
            title='Test Movie 2',
            vote_average=8.0
        )
        
        history2 = RecommendationHistory.objects.create(
            user=self.user,
            movie=movie2,
            recommendation_score=0.9
        )
        
        histories = list(RecommendationHistory.objects.all())
        # Most recent recommendation should be first
        self.assertEqual(histories[0].movie.tmdb_id, 67890)
        self.assertEqual(histories[1].movie.tmdb_id, 12345)
    
    def test_recommendation_score_validation(self):
        """Test recommendation score validation"""
        # Valid score
        history = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=0.5
        )
        self.assertEqual(history.recommendation_score, 0.5)
        
        # Test that scores outside 0-1 range can be stored
        # (validation might be handled at the application level)
        history2 = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=1.5
        )
        self.assertEqual(history2.recommendation_score, 1.5)
    
    def test_recommendation_history_auto_timestamp(self):
        """Test that recommended_at is automatically set"""
        before_creation = timezone.now()
        history = RecommendationHistory.objects.create(
            user=self.user,
            movie=self.movie,
            recommendation_score=0.8
        )
        after_creation = timezone.now()
        
        self.assertGreaterEqual(history.recommended_at, before_creation)
        self.assertLessEqual(history.recommended_at, after_creation)