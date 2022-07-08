from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    KAFKA_BROKERS: str
    KAFKA_TOPIC: str
    KAFKA_USERNAME: Optional[str] = None
    KAFKA_PASSWORD: Optional[str] = None
    KAFKA_SASL_MECHANISM: Optional[str] = None
    KAFKA_SECURITY_PROTOCOL: Optional[str] = None
    KAFKA_GROUP: Optional[str] = None
    KAFKA_TIMEOUT_MS: Optional[int] = 1000
    KAFKA_MAX_RECORDS: Optional[int] = 10

    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_NAME: str
    DATABASE_PORT: Optional[int] = 5432


settings = Settings()
