"""
Configuration settings for Document Ingestion Agent v2.0
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application settings
    app_name: str = "Document Ingestion Agent v2.0"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Mistral OCR API settings
    mistral_api_key: Optional[str] = Field(default=None, env="MISTRAL_API_KEY")
    mistral_ocr_model: str = Field(default="mistral-ocr-latest", env="MISTRAL_OCR_MODEL")
    mistral_rate_limit: int = Field(default=60, env="MISTRAL_RATE_LIMIT")  # requests per minute
    
    # File processing settings
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    supported_file_types: str = Field(
        default=".pdf,.png,.jpg,.jpeg,.tiff,.bmp", 
        env="SUPPORTED_FILE_TYPES"
    )
    upload_directory: str = Field(default="/tmp/document-uploads", env="UPLOAD_DIRECTORY")
    
    # Processing settings
    max_concurrent_documents: int = Field(default=5, env="MAX_CONCURRENT_DOCUMENTS")
    processing_timeout: int = Field(default=300, env="PROCESSING_TIMEOUT")  # seconds
    
    # Database settings (optional for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Security settings
    api_key_required: bool = Field(default=False, env="API_KEY_REQUIRED")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    # Webhook settings
    webhook_timeout: int = Field(default=10, env="WEBHOOK_TIMEOUT")  # seconds
    webhook_retry_attempts: int = Field(default=3, env="WEBHOOK_RETRY_ATTEMPTS")
    webhook_secret: Optional[str] = Field(default=None, env="WEBHOOK_SECRET")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Cost optimization settings
    enable_native_pdf_detection: bool = Field(default=True, env="ENABLE_NATIVE_PDF_DETECTION")
    ocr_confidence_threshold: float = Field(default=0.7, env="OCR_CONFIDENCE_THRESHOLD")
    
    @property
    def supported_file_types_list(self) -> list:
        """Convert comma-separated file types to list"""
        return self.supported_file_types.split(",")
    
    @property
    def allowed_origins_list(self) -> list:
        """Convert comma-separated origins to list"""
        if self.allowed_origins == "*":
            return ["*"]
        return self.allowed_origins.split(",")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()