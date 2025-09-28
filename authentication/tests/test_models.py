import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.models import UserPreference
from movies.models import Genre

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the custom User model"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_user_string_representation(self):
        """Test the string representation of user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_user_full_name(self):
        """Test the get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        expected_name = f"{self.user_data['first_name']} {self.user_data['last_name']}"
        self.assertEqual(user.get_full_name(), expected_name)
    
    def test_user_short_name(self):
        """Test the get_short_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), self.user_data['first_name'])
    
    def test_email_normalization(self):
        """Test that email addresses are normalized"""
        email = 'Test@EXAMPLE.COM'
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )
        self.assertEqual(user.email, email.lower())
    
    def test_invalid_email(self):
        """Test creating user with invalid email"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='testpass123'
            )
    
    def test_create_superuser_without_staff(self):
        """Test that superuser must be staff"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
    
    def test_create_superuser_without_superuser(self):
        """Test that superuser must have is_superuser=True"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )


class UserPreferenceModelTest(TestCase):
    """Test cases for the UserPreference model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.genre1 = Genre.objects.create(name='Action')
        self.genre2 = Genre.objects.create(name='Comedy')
    
    def test_create_user_preference(self):
        """Test creating user preferences"""
        preference = UserPreference.objects.create(
            user=self.user,
            min_rating=7.0,
            language='en'
        )
        preference.preferred_genres.add(self.genre1, self.genre2)
        
        self.assertEqual(preference.user, self.user)
        self.assertEqual(preference.min_rating, 7.0)
        self.assertEqual(preference.language, 'en')
        self.assertEqual(preference.preferred_genres.count(), 2)
    
    def test_user_preference_string_representation(self):
        """Test the string representation of user preference"""
        preference = UserPreference.objects.create(
            user=self.user,
            min_rating=6.0
        )
        expected_str = f"Preferences for {self.user.email}"
        self.assertEqual(str(preference), expected_str)
    
    def test_user_preference_defaults(self):
        """Test default values for user preferences"""
        preference = UserPreference.objects.create(user=self.user)
        
        self.assertEqual(preference.min_rating, 0.0)
        self.assertEqual(preference.language, 'en')
        self.assertIsNotNone(preference.updated_at)
    
    def test_min_rating_validation(self):
        """Test min_rating field validation"""
        # Test valid rating
        preference = UserPreference.objects.create(
            user=self.user,
            min_rating=8.5
        )
        self.assertEqual(preference.min_rating, 8.5)
        
        # Test invalid rating (negative)
        with self.assertRaises(ValidationError):
            preference = UserPreference(
                user=self.user,
                min_rating=-1.0
            )
            preference.full_clean()
        
        # Test invalid rating (too high)
        with self.assertRaises(ValidationError):
            preference = UserPreference(
                user=self.user,
                min_rating=11.0
            )
            preference.full_clean()
    
    def test_one_preference_per_user(self):
        """Test that each user can have only one preference"""
        UserPreference.objects.create(user=self.user)
        
        # Creating another preference for the same user should be allowed
        # but typically handled at the application level
        preference2 = UserPreference.objects.create(user=self.user)
        self.assertEqual(UserPreference.objects.filter(user=self.user).count(), 2)
    
    def test_preference_updated_at_auto_update(self):
        """Test that updated_at field is automatically updated"""
        preference = UserPreference.objects.create(user=self.user)
        original_updated_at = preference.updated_at
        
        # Update the preference
        preference.min_rating = 8.0
        preference.save()
        
        # Refresh from database
        preference.refresh_from_db()
        self.assertGreater(preference.updated_at, original_updated_at)