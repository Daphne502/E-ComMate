import json
import logging
from typing import List, Optional

import redis

import config

logger = logging.getLogger("ecommate.cache")

_redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    懒加载 Redis 客户端。
    连接失败或未配置 REDIS_URL 时返回 None，业务层自动降级。
    """
    global _redis_client

    if not config.REDIS_URL:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        client = redis.from_url(
            config.REDIS_URL,
            decode_responses=True,  # 返回 str 而非 bytes
            socket_connect_timeout=2,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis 连接成功: %s", config.REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning("Redis 不可用，将降级为无缓存: %s", e)
        _redis_client = None
        return None


def _cache_key(style: str, k: int) -> str:
    return f"ecommate:v1:style:{style}:k{k}"


def get_cached_examples(style: str, k: int = 3) -> Optional[List[str]]:
    client = get_redis_client()
    if client is None:
        return None

    key = _cache_key(style, k)
    try:
        cached = client.get(key)
        if cached:
            logger.info("Redis 缓存命中: %s", key)
            return json.loads(cached)
        logger.info("Redis 缓存未命中: %s", key)
        return None
    except Exception as e:
        logger.warning("Redis 读取失败: %s", e)
        return None


def set_cached_examples(style: str, examples: List[str], k: int = 3) -> None:
    client = get_redis_client()
    if client is None:
        return

    key = _cache_key(style, k)
    try:
        client.setex(
            key,
            config.CACHE_TTL,
            json.dumps(examples, ensure_ascii=False),
        )
        logger.info("Redis 缓存写入: %s (TTL=%ss)", key, config.CACHE_TTL)
    except Exception as e:
        logger.warning("Redis 写入失败: %s", e)