"""
Extensions and Config Unit Tests
Covers app/Extensions.py and app/Config.py
"""
import pytest
from unittest.mock import MagicMock, patch


class TestInitRedis:
    """Tests for app/Extensions.py init_redis() – lines 43-45"""

    def test_init_redis_creates_client(self):
        from app.extensions import init_redis
        mock_app = MagicMock()
        mock_app.config.get.return_value = 'redis://localhost:6379/0'

        with patch('app.extensions.Redis') as MockRedis:
            mock_client = MagicMock()
            MockRedis.from_url.return_value = mock_client
            result = init_redis(mock_app)

        assert result == mock_client
        MockRedis.from_url.assert_called_once_with('redis://localhost:6379/0', decode_responses=True)

    def test_init_redis_sets_global(self):
        import app.extensions as ext
        from app.extensions import init_redis
        mock_app = MagicMock()
        mock_app.config.get.return_value = 'redis://test:6379/1'

        with patch('app.extensions.Redis') as MockRedis:
            mock_client = MagicMock()
            MockRedis.from_url.return_value = mock_client
            init_redis(mock_app)

        assert ext.redis_client == mock_client


class TestProductionConfigValidate:
    """Tests for app/Config.py ProductionConfig.validate() – lines 124-127"""

    def test_validate_raises_if_no_secret_key(self):
        from app.config import ProductionConfig
        original = ProductionConfig.SECRET_KEY
        try:
            ProductionConfig.SECRET_KEY = ''
            with pytest.raises(ValueError, match='SECRET_KEY'):
                ProductionConfig.validate()
        finally:
            ProductionConfig.SECRET_KEY = original

    def test_validate_raises_if_no_jwt_secret_key(self):
        from app.config import ProductionConfig
        original_sk = ProductionConfig.SECRET_KEY
        original_jwt = ProductionConfig.JWT_SECRET_KEY
        try:
            ProductionConfig.SECRET_KEY = 'set'
            ProductionConfig.JWT_SECRET_KEY = ''
            with pytest.raises(ValueError, match='JWT_SECRET_KEY'):
                ProductionConfig.validate()
        finally:
            ProductionConfig.SECRET_KEY = original_sk
            ProductionConfig.JWT_SECRET_KEY = original_jwt

    def test_validate_passes_with_keys_set(self):
        from app.config import ProductionConfig
        original_sk = ProductionConfig.SECRET_KEY
        original_jwt = ProductionConfig.JWT_SECRET_KEY
        try:
            ProductionConfig.SECRET_KEY = 'prod-secret'
            ProductionConfig.JWT_SECRET_KEY = 'jwt-secret'
            ProductionConfig.validate()  # should not raise
        finally:
            ProductionConfig.SECRET_KEY = original_sk
            ProductionConfig.JWT_SECRET_KEY = original_jwt


class TestGetConfig:
    """Tests for app/Config.py get_config() – line 149"""

    def test_get_config_development(self):
        from app.config import get_config, DevelopmentConfig
        result = get_config('development')
        assert result is DevelopmentConfig

    def test_get_config_testing(self):
        from app.config import get_config, TestingConfig
        result = get_config('testing')
        assert result is TestingConfig

    def test_get_config_production(self):
        from app.config import get_config, ProductionConfig
        result = get_config('production')
        assert result is ProductionConfig

    def test_get_config_unknown_returns_default(self):
        from app.config import get_config, DevelopmentConfig
        result = get_config('nonexistent')
        assert result is DevelopmentConfig
