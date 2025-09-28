#!/usr/bin/env python
"""
Development setup script for Movie Recommendation API

This script helps set up the development environment by:
1. Creating a superuser
2. Loading initial data
3. Setting up recommendation engines
4. Creating sample data for testing
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.db import transaction

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_api.settings')
django.setup()

User = get_user_model()


def create_superuser():
    """Create a superuser if one doesn't exist"""
    if not User.objects.filter(is_superuser=True).exists():
        print("Creating superuser...")
        User.objects.create_superuser(
            email='admin@movieapi.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print("Superuser created: admin@movieapi.com / admin123")
    else:
        print("Superuser already exists")


def setup_recommendation_engines():
    """Set up default recommendation engines"""
    from recommendations.models import RecommendationEngine
    
    engines = [
        {
            'name': 'Collaborative Filtering',
            'algorithm_type': 'collaborative',
            'is_active': True,
            'parameters': {
                'n_neighbors': 20,
                'min_ratings': 5,
                'similarity_threshold': 0.1
            }
        },
        {
            'name': 'Content-Based Filtering',
            'algorithm_type': 'content_based',
            'is_active': True,
            'parameters': {
                'genre_weight': 0.4,
                'rating_weight': 0.3,
                'popularity_weight': 0.3
            }
        },
        {
            'name': 'Hybrid Recommendation',
            'algorithm_type': 'hybrid',
            'is_active': True,
            'parameters': {
                'collaborative_weight': 0.6,
                'content_weight': 0.4,
                'min_collaborative_ratings': 10
            }
        }
    ]
    
    for engine_data in engines:
        engine, created = RecommendationEngine.objects.get_or_create(
            name=engine_data['name'],
            defaults=engine_data
        )
        if created:
            print(f"Created recommendation engine: {engine.name}")
        else:
            print(f"Recommendation engine already exists: {engine.name}")


def create_sample_genres():
    """Create sample movie genres"""
    from movies.models import Genre
    
    genres = [
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
        'Documentary', 'Drama', 'Family', 'Fantasy', 'History',
        'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction',
        'TV Movie', 'Thriller', 'War', 'Western'
    ]
    
    for genre_name in genres:
        genre, created = Genre.objects.get_or_create(name=genre_name)
        if created:
            print(f"Created genre: {genre_name}")


def main():
    """Main setup function"""
    print("Setting up Movie Recommendation API development environment...")
    
    try:
        with transaction.atomic():
            create_superuser()
            setup_recommendation_engines()
            create_sample_genres()
            
        print("\n✅ Development setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Set your TMDb API key in the .env file")
        print("2. Start the development server: python manage.py runserver")
        print("3. Start Celery worker: celery -A movie_api worker --loglevel=info")
        print("4. Access admin panel: http://localhost:8000/admin/")
        print("5. Access API docs: http://localhost:8000/swagger/")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()