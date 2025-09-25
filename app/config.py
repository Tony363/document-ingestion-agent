"""
Application Configuration

Centralized configuration for the document processing pipeline.
Uses environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional, List, Any
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Document Ingestion Agent"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"  # development, staging, production
    
    # Server Configuration (mapped from HOST/PORT)
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="HOST")  # Backward compatibility
    api_port: int = Field(default=8000, alias="PORT")  # Backward compatibility
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(default=["*"])
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    
    # Mistral OCR Configuration
    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")
    mistral_ocr_model: str = Field(default="mistral-ocr-latest", alias="MISTRAL_OCR_MODEL")
    mistral_api_url: str = "https://api.mistral.ai/v1/ocr"
    mistral_rate_limit: int = Field(default=60, alias="MISTRAL_RATE_LIMIT")
    mistral_rate_limit_delay: float = 0.1  # seconds between requests
    
    # File Processing Configuration
    max_file_size: int = Field(default=52428800, alias="MAX_FILE_SIZE")  # bytes
    max_upload_size_mb: int = 50  # Backward compatibility, derived from max_file_size
    supported_file_types: str = Field(default=".pdf,.png,.jpg,.jpeg,.tiff,.bmp", alias="SUPPORTED_FILE_TYPES")
    allowed_extensions: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]  # Backward compatibility
    upload_directory: str = Field(default="/tmp/document-uploads", alias="UPLOAD_DIRECTORY")
    
    # Processing Settings
    max_concurrent_documents: int = Field(default=5, alias="MAX_CONCURRENT_DOCUMENTS")
    processing_timeout: int = Field(default=300, alias="PROCESSING_TIMEOUT")
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # PostgreSQL Configuration (Optional - defaults to Redis for state management)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_time_limit: int = 300  # 5 minutes
    celery_task_soft_time_limit: int = 270
    
    # Processing Configuration
    ocr_confidence_threshold: float = Field(default=0.7, alias="OCR_CONFIDENCE_THRESHOLD")
    extraction_confidence_threshold: float = 0.6
    validation_strict_mode: bool = True
    max_pages_per_document: int = 10
    enable_native_pdf_detection: bool = Field(default=True, alias="ENABLE_NATIVE_PDF_DETECTION")
    
    # Security Configuration
    api_key_header: str = "X-API-Key"
    api_key_required: bool = Field(default=False, alias="API_KEY_REQUIRED")
    enable_api_key_auth: bool = Field(default=False, alias="API_KEY_REQUIRED")  # Backward compatibility
    api_keys: List[str] = []  # Load from environment or secrets manager
    
    # Webhook Configuration
    webhook_timeout: int = Field(default=10, alias="WEBHOOK_TIMEOUT")
    webhook_timeout_seconds: int = 30  # Backward compatibility
    webhook_retry_attempts: int = Field(default=3, alias="WEBHOOK_RETRY_ATTEMPTS")
    webhook_max_retries: int = 3  # Backward compatibility
    webhook_retry_delay_seconds: int = 5
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    enable_tracing: bool = Field(default=False, alias="ENABLE_TRACING")
    metrics_port: int = 9090
    log_format: str = "json"  # json or text
    
    # Storage Configuration
    storage_backend: str = "local"  # local, s3, gcs
    storage_bucket: Optional[str] = None
    storage_region: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra fields in .env without validation errors
    }
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v
        
    @model_validator(mode='after')
    def sync_derived_fields(self):
        """Synchronize derived and backward compatibility fields"""
        
        # Parse supported_file_types into allowed_extensions
        if hasattr(self, 'supported_file_types') and self.supported_file_types:
            self.allowed_extensions = [ext.strip() for ext in self.supported_file_types.split(",")]
            
        # Parse allowed_origins into cors_origins  
        if hasattr(self, 'allowed_origins') and self.allowed_origins:
            if self.allowed_origins == "*":
                self.cors_origins = ["*"]
            else:
                self.cors_origins = [origin.strip() for origin in self.allowed_origins.split(",")]
            
        # Calculate max_upload_size_mb from max_file_size
        if hasattr(self, 'max_file_size'):
            self.max_upload_size_mb = self.max_file_size // (1024 * 1024)
            
        # Sync webhook settings
        if hasattr(self, 'webhook_timeout'):
            self.webhook_timeout_seconds = self.webhook_timeout
        if hasattr(self, 'webhook_retry_attempts'):
            self.webhook_max_retries = self.webhook_retry_attempts
            
        # Sync auth settings
        if hasattr(self, 'api_key_required'):
            self.enable_api_key_auth = self.api_key_required
            
        return self
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_upload_path(self) -> str:
        """Get full upload directory path with environment awareness"""
        # Detect if running in Docker (check for common Docker indicators)
        is_docker = (
            os.path.exists('/.dockerenv') or 
            os.environ.get('DOCKER_CONTAINER') == 'true' or
            os.environ.get('container') == 'docker'
        )
        
        if is_docker:
            # In Docker, use the mounted path
            return "/app/uploads"
        else:
            # Local development, use relative path that gets mounted to Docker
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_dir, "uploads")
    
    def validate_mistral_config(self) -> bool:
        """Validate Mistral API configuration"""
        if not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        return True
    
    def get_allowed_extensions(self) -> List[str]:
        """Get list of allowed file extensions"""
        return self.allowed_extensions
    
    def get_cors_origins(self) -> List[str]:  
        """Get list of CORS origins"""
        return self.cors_origins

# Create settings instance
settings = Settings()

# Validate critical configurations on import
if settings.environment == "production":
    settings.validate_mistral_config()