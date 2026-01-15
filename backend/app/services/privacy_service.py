"""
Privacy Service.

Sanitizes text using Microsoft Presidio before AI processing.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PrivacyServiceError(RuntimeError):
    """Raised when PII sanitization fails."""


class PrivacyService:
    """Service for PII sanitization via Presidio."""

    def __init__(self, analyzer_url: str | None = None, anonymizer_url: str | None = None):
        self.analyzer_url = analyzer_url or settings.PRESIDIO_ANALYZER_URL
        self.anonymizer_url = anonymizer_url or settings.PRESIDIO_ANONYMIZER_URL
        self._timeout = 10.0
        self._preferred_language: str | None = None

    def sanitize(self, text: str, language: str | None = None) -> str:
        """
        Sanitize text synchronously.

        Args:
            text: Input text.
            language: Optional language override.

        Returns:
            Sanitized text.
        """
        if not text:
            return text

        self._validate_config()
        languages = self._get_languages_to_try(language)

        try:
            with httpx.Client(timeout=self._timeout) as client:
                results: list[dict[str, Any]] | None = None
                last_status_error: httpx.HTTPStatusError | None = None

                for lang in languages:
                    try:
                        results = self._analyze_sync(client, text, lang)
                        if language is None:
                            self._preferred_language = lang
                        break
                    except httpx.HTTPStatusError as exc:
                        last_status_error = exc
                        logger.warning(
                            "Presidio analyzer failed",
                            language=lang,
                            status_code=exc.response.status_code,
                        )

                if results is None:
                    if last_status_error is not None:
                        raise last_status_error
                    raise PrivacyServiceError("Presidio sanitization failed")

                if not results:
                    return text

                self._log_entities(results)
                return self._anonymize_sync(client, text, results)
        except httpx.RequestError as exc:
            logger.error(
                "Presidio service unavailable",
                analyzer_url=self.analyzer_url,
                anonymizer_url=self.anonymizer_url,
                error=str(exc),
            )
            raise PrivacyServiceError(
                "Presidio sanitization failed: service unavailable. "
                "Start Presidio with: docker compose --profile ai up -d presidio-analyzer presidio-anonymizer"
            ) from exc
        except (httpx.HTTPStatusError, ValueError) as exc:
            logger.error("Presidio sanitization failed", error=str(exc))
            raise PrivacyServiceError(
                "Presidio sanitization failed. "
                'If you are using the default Presidio docker image, set PRESIDIO_LANGUAGES=["en"].'
            ) from exc

    async def sanitize_async(self, text: str, language: str | None = None) -> str:
        """
        Sanitize text asynchronously.

        Args:
            text: Input text.
            language: Optional language override.

        Returns:
            Sanitized text.
        """
        if not text:
            return text

        self._validate_config()
        languages = self._get_languages_to_try(language)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                results: list[dict[str, Any]] | None = None
                last_status_error: httpx.HTTPStatusError | None = None

                for lang in languages:
                    try:
                        results = await self._analyze_async(client, text, lang)
                        if language is None:
                            self._preferred_language = lang
                        break
                    except httpx.HTTPStatusError as exc:
                        last_status_error = exc
                        logger.warning(
                            "Presidio analyzer failed",
                            language=lang,
                            status_code=exc.response.status_code,
                        )

                if results is None:
                    if last_status_error is not None:
                        raise last_status_error
                    raise PrivacyServiceError("Presidio sanitization failed")

                if not results:
                    return text

                self._log_entities(results)
                return await self._anonymize_async(client, text, results)
        except httpx.RequestError as exc:
            logger.error(
                "Presidio service unavailable",
                analyzer_url=self.analyzer_url,
                anonymizer_url=self.anonymizer_url,
                error=str(exc),
            )
            raise PrivacyServiceError(
                "Presidio sanitization failed: service unavailable. "
                "Start Presidio with: docker compose --profile ai up -d presidio-analyzer presidio-anonymizer"
            ) from exc
        except (httpx.HTTPStatusError, ValueError) as exc:
            logger.error("Presidio sanitization failed", error=str(exc))
            raise PrivacyServiceError(
                "Presidio sanitization failed. "
                'If you are using the default Presidio docker image, set PRESIDIO_LANGUAGES=["en"].'
            ) from exc

    def _validate_config(self) -> None:
        if not self.analyzer_url or not self.anonymizer_url:
            raise PrivacyServiceError("Presidio endpoints are not configured")

    def _get_languages_to_try(self, language: str | None) -> list[str]:
        if language:
            return [language]

        configured = list(settings.PRESIDIO_LANGUAGES or [])
        if not configured:
            configured = ["en"]

        languages: list[str] = []
        seen: set[str] = set()
        for lang in configured:
            if lang and lang not in seen:
                languages.append(lang)
                seen.add(lang)

        if "en" not in seen:
            languages.append("en")

        preferred = self._preferred_language
        if preferred and preferred in languages:
            languages.remove(preferred)
            languages.insert(0, preferred)

        return languages

    @staticmethod
    def _build_analyze_payload(text: str, language: str) -> dict[str, Any]:
        return {"text": text, "language": language}

    @staticmethod
    def _build_anonymize_payload(text: str, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {"text": text, "analyzer_results": results}

    def _analyze_sync(self, client: httpx.Client, text: str, language: str) -> list[dict[str, Any]]:
        response = client.post(
            f"{self.analyzer_url}/analyze",
            json=self._build_analyze_payload(text, language),
        )
        response.raise_for_status()
        results = response.json()
        if not isinstance(results, list):
            raise ValueError("Unexpected Presidio analyzer response")
        return results

    async def _analyze_async(
        self,
        client: httpx.AsyncClient,
        text: str,
        language: str,
    ) -> list[dict[str, Any]]:
        response = await client.post(
            f"{self.analyzer_url}/analyze",
            json=self._build_analyze_payload(text, language),
        )
        response.raise_for_status()
        results = response.json()
        if not isinstance(results, list):
            raise ValueError("Unexpected Presidio analyzer response")
        return results

    def _anonymize_sync(
        self,
        client: httpx.Client,
        text: str,
        results: list[dict[str, Any]],
    ) -> str:
        response = client.post(
            f"{self.anonymizer_url}/anonymize",
            json=self._build_anonymize_payload(text, results),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected Presidio anonymizer response")
        return str(payload.get("text", text))

    async def _anonymize_async(
        self,
        client: httpx.AsyncClient,
        text: str,
        results: list[dict[str, Any]],
    ) -> str:
        response = await client.post(
            f"{self.anonymizer_url}/anonymize",
            json=self._build_anonymize_payload(text, results),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected Presidio anonymizer response")
        return str(payload.get("text", text))

    @staticmethod
    def _log_entities(results: list[dict[str, Any]]) -> None:
        entities = [result.get("entity_type") for result in results if result.get("entity_type")]
        if entities:
            logger.info("PII entities detected", entities=entities)


privacy_service = PrivacyService()
