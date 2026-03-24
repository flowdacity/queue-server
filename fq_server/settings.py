# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

from collections.abc import Mapping
from typing import Literal, TypedDict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FQSectionConfig(TypedDict):
    job_expire_interval: int
    job_requeue_interval: int
    default_job_requeue_limit: int
    enable_requeue_script: bool


class RedisSectionConfig(TypedDict):
    db: int
    key_prefix: str
    conn_type: Literal["tcp_sock", "unix_sock"]
    host: str
    port: int
    password: str
    clustered: bool
    unix_socket_path: str


class FQConfig(TypedDict):
    fq: FQSectionConfig
    redis: RedisSectionConfig


class QueueServerSettings(BaseSettings):
    """Environment-backed settings for Flowdacity Queue Server."""

    model_config = SettingsConfigDict(extra="ignore")

    job_expire_interval: int = Field(
        default=1000, ge=1, validation_alias="FQ_JOB_EXPIRE_INTERVAL"
    )
    job_requeue_interval: int = Field(
        default=1000, ge=1, validation_alias="FQ_JOB_REQUEUE_INTERVAL"
    )
    default_job_requeue_limit: int = Field(
        default=-1, ge=-1, validation_alias="FQ_DEFAULT_JOB_REQUEUE_LIMIT"
    )
    enable_requeue_script: bool = Field(
        default=True, validation_alias="FQ_ENABLE_REQUEUE_SCRIPT"
    )

    redis_db: int = Field(default=0, ge=0, validation_alias="FQ_REDIS_DB")
    redis_key_prefix: str = Field(
        default="fq_server", min_length=1, validation_alias="FQ_REDIS_KEY_PREFIX"
    )
    redis_conn_type: Literal["tcp_sock", "unix_sock"] = Field(
        default="tcp_sock", validation_alias="FQ_REDIS_CONN_TYPE"
    )
    redis_host: str = Field(
        default="127.0.0.1", min_length=1, validation_alias="FQ_REDIS_HOST"
    )
    redis_port: int = Field(
        default=6379, ge=1, le=65535, validation_alias="FQ_REDIS_PORT"
    )
    redis_password: str = Field(default="", validation_alias="FQ_REDIS_PASSWORD")
    redis_clustered: bool = Field(
        default=False, validation_alias="FQ_REDIS_CLUSTERED"
    )
    redis_unix_socket_path: str = Field(
        default="/tmp/redis.sock",
        min_length=1,
        validation_alias="FQ_REDIS_UNIX_SOCKET_PATH",
    )

    @field_validator("enable_requeue_script", "redis_clustered", mode="before")
    @classmethod
    def validate_boolean_env(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "true":
                return True
            if normalized == "false":
                return False

        raise ValueError("Use either 'true' or 'false'.")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "QueueServerSettings":
        if env is None:
            return cls()
        return cls.model_validate(env)

    def to_fq_config(self) -> FQConfig:
        return {
            "fq": {
                "job_expire_interval": self.job_expire_interval,
                "job_requeue_interval": self.job_requeue_interval,
                "default_job_requeue_limit": self.default_job_requeue_limit,
                "enable_requeue_script": self.enable_requeue_script,
            },
            "redis": {
                "db": self.redis_db,
                "key_prefix": self.redis_key_prefix,
                "conn_type": self.redis_conn_type,
                "host": self.redis_host,
                "port": self.redis_port,
                "password": self.redis_password,
                "clustered": self.redis_clustered,
                "unix_socket_path": self.redis_unix_socket_path,
            },
        }
