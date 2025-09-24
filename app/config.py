"""
Application Configuration

Centralized configuration for the document processing pipeline.
Uses environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Document Ingestion Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    # Mistral OCR Configuration
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    mistral_api_url: str = "https://api.mistral.ai/v1/ocr"
    mistral_rate_limit_delay: float = 0.1  # seconds between requests
    
    # File Upload Configuration
    max_upload_size_mb: int = 10
    allowed_extensions: list = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
    upload_directory: str = "./uploads"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # PostgreSQL Configuration
    database_url: str = "postgresql://user:password@localhost/document_agent"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_time_limit: int = 300  # 5 minutes
    celery_task_soft_time_limit: int = 270
    
    # Processing Configuration
    ocr_confidence_threshold: float = 0.7
    extraction_confidence_threshold: float = 0.6
    validation_strict_mode: bool = True
    max_pages_per_document: int = 10
    
    # Webhook Configuration
    webhook_timeout_seconds: int = 30
    webhook_max_retries: int = 3
    webhook_retry_delay_seconds: int = 5
    
    # Security Configuration
    api_key_header: str = "X-API-Key"
    enable_api_key_auth: bool = True
    api_keys: list = []  # Load from environment or secrets manager
    
    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    # Storage Configuration
    storage_backend: str = "local"  # local, s3, gcs
    storage_bucket: Optional[str] = None
    storage_region: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_upload_path(self) -> str:
        """Get full upload directory path"""
        return os.path.abspath(self.upload_directory)
    
    def validate_mistral_config(self) -> bool:
        """Validate Mistral API configuration"""
        if not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        return True

# Create settings instance
settings = Settings()

# Validate critical configurations on import
if settings.environment == "production":
    settings.validate_mistral_config()