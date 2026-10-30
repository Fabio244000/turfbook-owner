from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PEM of identity's public key: verifies the session token, cannot issue one.
    jwt_public_key: str
    # The algorithm always comes from here, never from the token.
    jwt_algorithm: str = 'RS256'
    jwt_issuer: str = 'turfbook-identity'
    database_url: str
    # A Lambda execution environment serves one request at a time, so one connection
    # is enough; it also caps connections to the shared RDS at one per environment.
    db_pool_size: int = 1
    db_max_overflow: int = 0
    # Replaces connections that went stale while the environment was idle.
    db_pool_pre_ping: bool = True
    api_prefix: str = '/api'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
