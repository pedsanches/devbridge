"""Tests for Exception Handlers and Error Response Format."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.errors import (
    AuthenticationError,
    DevBridgeError,
    ErrorCategory,
    NotFoundError,
    ValidationError,
)
from app.main import app


class TestTraceIdPropagation:
    """Test that trace_id is properly propagated."""

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """Create async client without DB dependency."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_trace_id_in_response_header(self, client: AsyncClient) -> None:
        """Test that X-Trace-ID is returned in response headers."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_trace_id_propagated_from_request(self, client: AsyncClient) -> None:
        """Test that trace_id from request header is used in response."""
        custom_trace_id = "test-trace-12345"

        response = await client.get("/health", headers={"X-Trace-ID": custom_trace_id})

        assert response.status_code == 200
        assert response.headers.get("X-Trace-ID") == custom_trace_id

    @pytest.mark.asyncio
    async def test_request_id_propagated_from_request(self, client: AsyncClient) -> None:
        """Test that request_id from header is used in response."""
        custom_request_id = "req-test-67890"

        response = await client.get("/health", headers={"X-Request-ID": custom_request_id})

        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_request_id


class TestDevBridgeExceptions:
    """Test custom DevBridge exception classes."""

    def test_devbridge_error_base(self) -> None:
        """Test base DevBridgeError exception."""
        error = DevBridgeError(
            message="Test error",
            error_code=ErrorCategory.INTERNAL_ERROR,
            status_code=500,
            details={"key": "value"},
        )

        assert error.message == "Test error"
        assert error.error_code == "INT_001"
        assert error.status_code == 500
        assert error.details == {"key": "value"}

    def test_devbridge_error_with_string_code(self) -> None:
        """Test DevBridgeError with string error code."""
        error = DevBridgeError(
            message="Custom error",
            error_code="CUSTOM_001",
            status_code=400,
        )

        assert error.error_code == "CUSTOM_001"
        assert error.status_code == 400

    def test_not_found_error(self) -> None:
        """Test NotFoundError exception."""
        error = NotFoundError(message="User not found", resource_type="User", resource_id="123")

        assert error.message == "User not found"
        assert error.error_code == "RES_001"
        assert error.status_code == 404
        assert error.details is not None
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "123"

    def test_not_found_error_default_message(self) -> None:
        """Test NotFoundError with default message."""
        error = NotFoundError()

        assert error.message == "Resource not found"
        assert error.error_code == "RES_001"
        assert error.status_code == 404

    def test_validation_error(self) -> None:
        """Test ValidationError exception."""
        error = ValidationError(message="Email is required", field="email")

        assert error.message == "Email is required"
        assert error.error_code == "VAL_001"
        assert error.status_code == 422
        assert error.details is not None
        assert error.details["field"] == "email"

    def test_validation_error_with_details(self) -> None:
        """Test ValidationError with custom details."""
        error = ValidationError(
            message="Invalid format", details={"expected": "email", "got": "not-an-email"}
        )

        assert error.error_code == "VAL_001"
        assert error.details is not None
        assert error.details["expected"] == "email"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError exception."""
        error = AuthenticationError(message="Token expired")

        assert error.message == "Token expired"
        assert error.error_code == "AUTH_003"
        assert error.status_code == 401

    def test_authentication_error_with_custom_code(self) -> None:
        """Test AuthenticationError with specific error code."""
        error = AuthenticationError(
            message="Invalid token", error_code=ErrorCategory.AUTH_INVALID_TOKEN
        )

        assert error.error_code == "AUTH_001"
        assert error.status_code == 401


class TestErrorCodes:
    """Test error code constants."""

    def test_auth_error_codes(self) -> None:
        """Test authentication error codes."""
        assert ErrorCategory.AUTH_INVALID_TOKEN.value == "AUTH_001"
        assert ErrorCategory.AUTH_EXPIRED_TOKEN.value == "AUTH_002"
        assert ErrorCategory.AUTH_UNAUTHORIZED.value == "AUTH_003"
        assert ErrorCategory.AUTH_FORBIDDEN.value == "AUTH_004"

    def test_validation_error_codes(self) -> None:
        """Test validation error codes."""
        assert ErrorCategory.VALIDATION_FAILED.value == "VAL_001"
        assert ErrorCategory.VALIDATION_MISSING_FIELD.value == "VAL_002"
        assert ErrorCategory.VALIDATION_INVALID_FORMAT.value == "VAL_003"

    def test_resource_error_codes(self) -> None:
        """Test resource error codes."""
        assert ErrorCategory.RESOURCE_NOT_FOUND.value == "RES_001"
        assert ErrorCategory.RESOURCE_ALREADY_EXISTS.value == "RES_002"
        assert ErrorCategory.RESOURCE_CONFLICT.value == "RES_003"

    def test_external_error_codes(self) -> None:
        """Test external service error codes."""
        assert ErrorCategory.EXTERNAL_GITHUB_ERROR.value == "EXT_001"
        assert ErrorCategory.EXTERNAL_LLM_ERROR.value == "EXT_002"
        assert ErrorCategory.EXTERNAL_DB_ERROR.value == "EXT_003"
        assert ErrorCategory.EXTERNAL_REDIS_ERROR.value == "EXT_004"

    def test_rate_limit_error_codes(self) -> None:
        """Test rate limit error codes."""
        assert ErrorCategory.RATE_LIMIT_EXCEEDED.value == "RATE_001"

    def test_internal_error_codes(self) -> None:
        """Test internal error codes."""
        assert ErrorCategory.INTERNAL_ERROR.value == "INT_001"
        assert ErrorCategory.INTERNAL_TIMEOUT.value == "INT_002"


class TestErrorResponseModel:
    """Test ErrorResponse Pydantic model."""

    def test_error_response_serialization(self) -> None:
        """Test that ErrorResponse can be serialized to JSON."""
        from app.core.errors import ErrorResponse

        response = ErrorResponse(
            error_id="test-error-id",
            trace_id="test-trace-id",
            error_code="AUTH_001",
            message="Test message",
            path="/api/test",
        )

        data = response.model_dump(mode="json")

        assert data["error_id"] == "test-error-id"
        assert data["trace_id"] == "test-trace-id"
        assert data["error_code"] == "AUTH_001"
        assert data["message"] == "Test message"
        assert data["path"] == "/api/test"
        assert "timestamp" in data

    def test_error_response_with_details(self) -> None:
        """Test ErrorResponse with details."""
        from app.core.errors import ErrorResponse

        response = ErrorResponse(
            error_id="test-id",
            trace_id="test-trace",
            error_code="VAL_001",
            message="Validation failed",
            path="/api/test",
            details={"field": "email", "reason": "invalid format"},
        )

        data = response.model_dump(mode="json")

        assert data["details"] is not None
        assert data["details"]["field"] == "email"
        assert data["details"]["reason"] == "invalid format"
