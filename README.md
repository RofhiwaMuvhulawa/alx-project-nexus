# Movie Recommendation API

A comprehensive Django REST API for movie recommendations using The Movie Database (TMDb) API. This system provides personalized movie recommendations using various algorithms including collaborative filtering, content-based filtering, and hybrid approaches.

## Features

- **User Authentication**: JWT-based authentication with custom user model
- **Movie Data Integration**: Real-time movie data from TMDb API
- **Personalized Recommendations**: Multiple recommendation algorithms
- **User Favorites**: Manage favorite movies
- **Caching**: Redis-based caching for improved performance
- **Background Tasks**: Celery for asynchronous processing
- **API Documentation**: Swagger/OpenAPI documentation
- **Admin Interface**: Django admin for data management

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Authentication**: JWT (Simple JWT)
- **External API**: TMDb API
- **Documentation**: drf-yasg (Swagger)

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- TMDb API Key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MovieAPI
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=movie_api
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# TMDb API
TMDB_API_KEY=your-tmdb-api-key

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7
```

### 5. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE movie_api;
\q

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Start Services

#### Start Redis (if not running)

```bash
# On Windows (if installed via installer)
redis-server

# On macOS (via Homebrew)
brew services start redis

# On Linux
sudo systemctl start redis
```

#### Start Celery Worker (in separate terminal)

```bash
celery -A movie_api worker --loglevel=info
```

#### Start Celery Beat (in separate terminal)

```bash
celery -A movie_api beat --loglevel=info
```

#### Start Django Development Server

```bash
python manage.py runserver
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **JSON Schema**: http://localhost:8000/swagger.json
- **Admin Interface**: http://localhost:8000/admin/

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/` - Update user profile

### Movies
- `GET /api/movies/genres/` - Get movie genres
- `GET /api/movies/trending/` - Get trending movies
- `GET /api/movies/popular/` - Get popular movies
- `GET /api/movies/top-rated/` - Get top-rated movies
- `GET /api/movies/search/` - Search movies
- `GET /api/movies/discover/` - Discover movies with filters
- `GET /api/movies/{id}/` - Get movie details
- `GET /api/movies/{id}/recommendations/` - Get movie recommendations
- `GET /api/movies/{id}/similar/` - Get similar movies

### User Favorites
- `GET /api/auth/favorites/` - Get user favorites
- `POST /api/auth/favorites/` - Add movie to favorites
- `DELETE /api/auth/favorites/{movie_id}/` - Remove from favorites

### User Preferences
- `GET /api/auth/preferences/` - Get user preferences
- `PUT /api/auth/preferences/` - Update user preferences

### Recommendations
- `GET /api/recommendations/personalized/` - Get personalized recommendations
- `GET /api/recommendations/similar/{movie_id}/` - Get similar movies
- `POST /api/recommendations/interactions/` - Track user interaction
- `POST /api/recommendations/feedback/` - Submit recommendation feedback
- `GET /api/recommendations/history/` - Get recommendation history
- `GET /api/recommendations/stats/` - Get recommendation statistics

## Configuration

### TMDb API Setup

1. Create an account at [TMDb](https://www.themoviedb.org/)
2. Go to Settings > API
3. Request an API key
4. Add your API key to the `.env` file

### Recommendation Algorithms

The system supports multiple recommendation algorithms:

1. **Collaborative Filtering**: Based on user behavior similarity
2. **Content-Based**: Based on movie features and user preferences
3. **Genre-Based**: Based on user's preferred genres
4. **Popularity-Based**: Based on movie popularity and ratings
5. **Hybrid**: Combines multiple algorithms

### Caching Strategy

- **Movie Data**: Cached for 1 hour
- **Recommendations**: Cached for 24 hours
- **User Similarities**: Computed daily via Celery tasks
- **Movie Similarities**: Computed daily via Celery tasks

## Background Tasks

Celery tasks handle:

- Updating movie cache from TMDb
- Computing user and movie similarities
- Generating personalized recommendations
- Cleaning up old cache entries
- Updating recommendation statistics

## Development

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## Production Deployment

### Environment Variables

For production, update these settings in `.env`:

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn movie_api.wsgi:application --bind 0.0.0.0:8000
```

### Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: movie_api
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  redis:
    image: redis:6-alpine

  web:
    build: .
    command: gunicorn movie_api.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False

  celery:
    build: .
    command: celery -A movie_api worker --loglevel=info
    volumes:
      - .:/code
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A movie_api beat --loglevel=info
    volumes:
      - .:/code
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## Monitoring and Logging

- Logs are stored in `logs/django.log`
- Celery tasks can be monitored via Flower:
  ```bash
  pip install flower
  celery -A movie_api flower
  ```
- Access Flower at http://localhost:5555

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`

2. **Redis Connection Error**
   - Ensure Redis is running
   - Check Redis configuration in `.env`

3. **TMDb API Errors**
   - Verify API key is correct
   - Check API rate limits

4. **Celery Tasks Not Running**
   - Ensure Celery worker is running
   - Check Redis connection
   - Verify task registration

### Performance Optimization

1. **Database Indexing**: Ensure proper indexes are in place
2. **Caching**: Tune cache timeouts based on usage patterns
3. **Celery**: Scale workers based on task load
4. **Database**: Use connection pooling for high traffic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.