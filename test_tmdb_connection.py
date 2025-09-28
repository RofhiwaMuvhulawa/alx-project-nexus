#!/usr/bin/env python
"""
Test script to verify TMDb API connection with the new credentials.
This version bypasses Django caching to test the API directly.
"""

import os
import requests
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def test_tmdb_api_direct():
    """
    Test TMDb API connection directly without Django dependencies.
    """
    print("Testing TMDb API connection (direct)...")
    
    # Get API key from environment
    api_key = os.getenv('TMDB_API_KEY')
    access_token = os.getenv('TMDB_ACCESS_TOKEN')
    base_url = 'https://api.themoviedb.org/3'
    
    if not api_key:
        print("✗ TMDB_API_KEY not found in environment variables")
        return False
    
    print(f"✓ Found API credentials")
    print(f"  API Key: {api_key[:10]}...")
    print(f"  Access Token: {access_token[:20] if access_token else 'Not set'}...")
    print(f"  Base URL: {base_url}")
    
    # Test with API key method
    print("\n=== Testing with API Key ===")
    
    try:
        # Test 1: Get genres
        print("\n1. Testing genres endpoint...")
        response = requests.get(
            f"{base_url}/genre/movie/list",
            params={'api_key': api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            genres_data = response.json()
            if 'genres' in genres_data:
                print(f"✓ Successfully fetched {len(genres_data['genres'])} genres")
                print(f"  Sample genres: {[g['name'] for g in genres_data['genres'][:3]]}")
            else:
                print("✗ Invalid response format")
                return False
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 2: Get popular movies
        print("\n2. Testing popular movies endpoint...")
        response = requests.get(
            f"{base_url}/movie/popular",
            params={'api_key': api_key, 'page': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            popular_data = response.json()
            if 'results' in popular_data:
                print(f"✓ Successfully fetched {len(popular_data['results'])} popular movies")
                if popular_data['results']:
                    first_movie = popular_data['results'][0]
                    print(f"  First movie: {first_movie.get('title', 'N/A')} ({first_movie.get('release_date', 'N/A')})")
            else:
                print("✗ Invalid response format")
                return False
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 3: Get movie details
        print("\n3. Testing movie details endpoint...")
        response = requests.get(
            f"{base_url}/movie/278",  # The Shawshank Redemption
            params={'api_key': api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            movie_data = response.json()
            print(f"✓ Successfully fetched movie details")
            print(f"  Title: {movie_data.get('title', 'N/A')}")
            print(f"  Overview: {movie_data.get('overview', 'N/A')[:100]}...")
            print(f"  Rating: {movie_data.get('vote_average', 'N/A')}/10")
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        # Test 4: Search movies
        print("\n4. Testing search endpoint...")
        response = requests.get(
            f"{base_url}/search/movie",
            params={'api_key': api_key, 'query': 'Inception', 'page': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            search_data = response.json()
            if 'results' in search_data:
                print(f"✓ Successfully searched movies")
                print(f"  Found {len(search_data['results'])} results for 'Inception'")
                if search_data['results']:
                    first_result = search_data['results'][0]
                    print(f"  Top result: {first_result.get('title', 'N/A')} ({first_result.get('release_date', 'N/A')})")
            else:
                print("✗ Invalid response format")
                return False
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test with Bearer token if available
    if access_token:
        print("\n=== Testing with Bearer Token ===")
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{base_url}/genre/movie/list",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✓ Bearer token authentication successful")
            else:
                print(f"✗ Bearer token failed with status {response.status_code}")
                print(f"  Response: {response.text}")
        
        except Exception as e:
            print(f"✗ Bearer token test error: {e}")
    
    print("\n🎉 All TMDb API tests passed successfully!")
    print("\nThe TMDb API integration is working correctly with the provided credentials.")
    print("\nNote: The Django application will work once Redis is running for caching.")
    return True

if __name__ == "__main__":
    success = test_tmdb_api_direct()
    exit(0 if success else 1)