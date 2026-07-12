from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from mergenvision.infrastructure.security.national_id import AesGcmNationalIdProtector
from mergenvision.ports.national_id import NationalIdProtector


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MERGENVISION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    test_database_url: str | None = None
    national_id_encryption_key_b64: SecretStr | None = None
    national_id_hmac_key_b64: SecretStr | None = None

    def create_national_id_protector(self) -> NationalIdProtector:
        if self.national_id_encryption_key_b64 is None or self.national_id_hmac_key_b64 is None:
            raise RuntimeError("National ID encryption/HMAC keys are not configured")
        return AesGcmNationalIdProtector(
            encryption_key_b64=self.national_id_encryption_key_b64.get_secret_value(),
            hmac_key_b64=self.national_id_hmac_key_b64.get_secret_value(),
        )
