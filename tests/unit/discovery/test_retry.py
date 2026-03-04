"""Unit tests for async retry utility."""

from unittest.mock import AsyncMock, patch

import pytest


class TestRetryAsync:
    """Tests for retry_async function."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        """Function that succeeds immediately is called once."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(return_value="ok")
        result = await retry_async(fn)
        assert result == "ok"
        assert fn.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self):
        """Function that fails then succeeds is retried."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=[OSError("transient"), "recovered"])
        result = await retry_async(fn, max_retries=3, base_delay=0.0)
        assert result == "recovered"
        assert fn.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausts_max_retries(self):
        """After max_retries failures, the last exception is re-raised."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=OSError("persistent"))
        with pytest.raises(OSError, match="persistent"):
            await retry_async(fn, max_retries=3, base_delay=0.0)
        # 1 initial + 3 retries = 4
        assert fn.call_count == 4

    @pytest.mark.asyncio
    async def test_non_retryable_exception_propagates_immediately(self):
        """Non-retryable exceptions are not retried."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            await retry_async(
                fn,
                max_retries=3,
                base_delay=0.0,
                retryable_exceptions=(OSError,),
            )
        assert fn.call_count == 1

    @pytest.mark.asyncio
    async def test_custom_retryable_exceptions(self):
        """Only specified exception types trigger retries."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=[RuntimeError("retry me"), "ok"])
        result = await retry_async(
            fn,
            max_retries=2,
            base_delay=0.0,
            retryable_exceptions=(RuntimeError,),
        )
        assert result == "ok"
        assert fn.call_count == 2

    @pytest.mark.asyncio
    async def test_delay_is_applied(self):
        """Verify that asyncio.sleep is called with backoff delays."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=[OSError("fail"), "ok"])

        with patch(
            "lookout.discovery.search.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await retry_async(fn, max_retries=2, base_delay=1.0, max_delay=30.0)
            mock_sleep.assert_called_once()
            # Delay should be between 0 and 2*base_delay (jitter)
            delay = mock_sleep.call_args[0][0]
            assert 0 <= delay <= 2.0

    @pytest.mark.asyncio
    async def test_delay_capped_at_max(self):
        """Delay does not exceed max_delay."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(side_effect=[OSError("1"), OSError("2"), OSError("3"), "ok"])

        with patch(
            "lookout.discovery.search.retry.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await retry_async(fn, max_retries=3, base_delay=100.0, max_delay=5.0)
            for call in mock_sleep.call_args_list:
                delay = call[0][0]
                assert delay <= 5.0

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        """Arguments and keyword arguments are forwarded to the function."""
        from lookout.discovery.search.retry import retry_async

        fn = AsyncMock(return_value="result")
        await retry_async(fn, "arg1", kwarg1="val1", max_retries=1, base_delay=0.0)
        fn.assert_called_once_with("arg1", kwarg1="val1")
