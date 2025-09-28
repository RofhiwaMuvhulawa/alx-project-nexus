import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import UserPreference
from movies.models import Genre
import json

User = get_user_model()


class UserRegistrationViewTest(APITestCase):
    """Test cases for user registration endpoint"""
    
    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_successful_user_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Check user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
    
    def test_registration_with_existing_email(self):
        """Test registration with already existing email"""
        User.objects.create_user(
            email='test@example.com',
            password='existingpass'
        )
        
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_mismatched_passwords(self):
        """Test registration with mismatched passwords"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_invalid_email(self):
        """Test registration with invalid email format"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_weak_password(self):
        """Test registration with weak password"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = '123'
        invalid_data['password_confirm'] = '123'
        
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginViewTest(APITestCase):
    """Test cases for user login endpoint"""
    
    def setUp(self):
        self.login_url = reverse('authentication:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_successful_login(self):
        """Test successful user login"""
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_with_missing_fields(self):
        """Test login with missing required fields"""
        # Missing password
        response = self.client.post(self.login_url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email
        response = self.client.post(self.login_url, {'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshViewTest(APITestCase):
    """Test cases for token refresh endpoint"""
    
    def setUp(self):
        self.refresh_url = reverse('authentication:token_refresh')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.refresh_token = RefreshToken.for_user(self.user)
    
    def test_successful_token_refresh(self):
        """Test successful token refresh"""
        refresh_data = {
            'refresh': str(self.refresh_token)
        }
        
        response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid refresh token"""
        refresh_data = {
            'refresh': 'invalid_token'
        }
        
        response = self.client.post(self.refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_with_missing_token(self):
        """Test token refresh with missing refresh token"""
        response = self.client.post(self.refresh_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileViewTest(APITestCase):
    """Test cases for user profile endpoint"""
    
    def setUp(self):
        self.profile_url = reverse('authentication:profile')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_profile(self):
        """Test retrieving user profile"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_profile_access_without_authentication(self):
        """Test accessing profile without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPreferencesViewTest(APITestCase):
    """Test cases for user preferences endpoint"""
    
    def setUp(self):
        self.preferences_url = reverse('authentication:preferences')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some genres for testing
        self.action_genre = Genre.objects.create(id=28, name='Action')
        self.comedy_genre = Genre.objects.create(id=35, name='Comedy')
        self.drama_genre = Genre.objects.create(id=18, name='Drama')
    
    def test_get_user_preferences_default(self):
        """Test retrieving default user preferences"""
        response = self.client.get(self.preferences_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['min_rating'], 0.0)
        self.assertEqual(response.data['language'], 'en')
        self.assertEqual(len(response.data['preferred_genres']), 0)
    
    def test_create_user_preferences(self):
        """Test creating user preferences"""
        preferences_data = {
            'preferred_genres': [28, 35],  # Action, Comedy
            'min_rating': 7.0,
            'language': 'es'
        }
        
        response = self.client.post(self.preferences_url, preferences_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['min_rating'], 7.0)
        self.assertEqual(response.data['language'], 'es')
        self.assertEqual(len(response.data['preferred_genres']), 2)
        
        # Verify in database
        preference = UserPreference.objects.get(user=self.user)
        self.assertEqual(preference.min_rating, 7.0)
        self.assertEqual(preference.language, 'es')
        self.assertEqual(preference.preferred_genres.count(), 2)
    
    def test_update_user_preferences(self):
        """Test updating existing user preferences"""
        # Create initial preferences
        preference = UserPreference.objects.create(
            user=self.user,
            min_rating=6.0,
            language='en'
        )
        preference.preferred_genres.add(self.action_genre)
        
        # Update preferences
        update_data = {
            'preferred_genres': [35, 18],  # Comedy, Drama
            'min_rating': 8.0,
            'language': 'fr'
        }
        
        response = self.client.put(self.preferences_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['min_rating'], 8.0)
        self.assertEqual(response.data['language'], 'fr')
        self.assertEqual(len(response.data['preferred_genres']), 2)
        
        # Verify in database
        preference.refresh_from_db()
        self.assertEqual(preference.min_rating, 8.0)
        self.assertEqual(preference.language, 'fr')
        self.assertEqual(preference.preferred_genres.count(), 2)
        self.assertIn(self.comedy_genre, preference.preferred_genres.all())
        self.assertIn(self.drama_genre, preference.preferred_genres.all())
    
    def test_partial_update_user_preferences(self):
        """Test partially updating user preferences"""
        # Create initial preferences
        preference = UserPreference.objects.create(
            user=self.user,
            min_rating=6.0,
            language='en'
        )
        preference.preferred_genres.add(self.action_genre)
        
        # Partial update - only min_rating
        update_data = {
            'min_rating': 7.5
        }
        
        response = self.client.patch(self.preferences_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['min_rating'], 7.5)
        self.assertEqual(response.data['language'], 'en')  # Should remain unchanged
        
        # Verify in database
        preference.refresh_from_db()
        self.assertEqual(preference.min_rating, 7.5)
        self.assertEqual(preference.language, 'en')
        self.assertEqual(preference.preferred_genres.count(), 1)
    
    def test_preferences_access_without_authentication(self):
        """Test accessing preferences without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.preferences_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_genre_in_preferences(self):
        """Test creating preferences with invalid genre ID"""
        preferences_data = {
            'preferred_genres': [999],  # Non-existent genre
            'min_rating': 7.0
        }
        
        response = self.client.post(self.preferences_url, preferences_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_min_rating(self):
        """Test creating preferences with invalid min_rating"""
        preferences_data = {
            'min_rating': 15.0  # Invalid rating (should be 0-10)
        }
        
        response = self.client.post(self.preferences_url, preferences_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordChangeViewTest(APITestCase):
    """Test cases for password change endpoint"""
    
    def setUp(self):
        self.password_change_url = reverse('authentication:change_password')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpassword123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_successful_password_change(self):
        """Test successful password change"""
        change_data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456'
        }
        
        response = self.client.post(self.password_change_url, change_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword456'))
        self.assertFalse(self.user.check_password('oldpassword123'))
    
    def test_password_change_with_wrong_old_password(self):
        """Test password change with incorrect old password"""
        change_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456'
        }
        
        response = self.client.post(self.password_change_url, change_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_change_with_mismatched_new_passwords(self):
        """Test password change with mismatched new passwords"""
        change_data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword456',
            'new_password_confirm': 'differentpassword'
        }
        
        response = self.client.post(self.password_change_url, change_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_change_without_authentication(self):
        """Test password change without authentication"""
        self.client.force_authenticate(user=None)
        
        change_data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456'
        }
        
        response = self.client.post(self.password_change_url, change_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)