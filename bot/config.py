from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки приложения берутся из окружения / .env файла."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Добавьте эту строку, чтобы игнорировать лишние поля
    )

    bot_token: str
    db_path: str = "data/tasks.db"
    log_level: str = "INFO"
    tz: str = "Europe/Moscow"  # Добавьте эту строку


# Единственный экземпляр — импортируется везде
settings = Settings()