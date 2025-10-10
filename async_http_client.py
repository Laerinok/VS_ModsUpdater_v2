#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024  Laerinok
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Legacy Module for Synchronous HTTP Requests.

This module defines the HTTPClient class, a synchronous wrapper around the 'requests' library.
It provides persistence, automatic retries, and proper session management.

It is currently used for sequential HTTP operations (e.g., file downloads, single API calls
outside of the mod update check). This module is considered **legacy** and is pending
full refactoring to an asynchronous pattern in a future release to enhance overall performance
and I/O efficiency.

The module encapsulates:
- Session management for persistent connections.
- Robust error handling with retry logic.
- Configuration for request timeouts.
"""


__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-10-03"  # Last update


# async_http_client.py

import logging
import asyncio
import random
from typing import Optional, Dict, Any

import aiohttp
import global_cache  # To access the timeout setting


# The 'random' import is required for the random delay in retries.

class AsyncHTTPClient:
    """
    Asynchronous HTTP client using aiohttp for non-blocking network requests.

    Manages the aiohttp ClientSession and implements a robust GET method
    with retries and asynchronous delays.
    """

    def __init__(self):
        # Retrieve the timeout from the global cache (default is 10 seconds)
        self.timeout: int = global_cache.config_cache.get("Options", {}).get("timeout",
                                                                             10)
        self.session: Optional[aiohttp.ClientSession] = None
        self.retry_attempts = 3
        self.delay = 1.0  # Base delay for retries

    async def __aenter__(self):
        """
        Asynchronous context manager entry method. Creates the aiohttp session.
        """
        # Use ClientTimeout to correctly apply the timeout setting to the session
        aio_timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=aio_timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit method. Closes the session safely.
        """
        if self.session:
            # Ensure session is closed asynchronously
            await self.session.close()

    async def _get_with_retries(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Performs an asynchronous GET request for JSON data with retries.

        Args:
            url: The URL to request.
            **kwargs: Additional parameters for the aiohttp GET request.

        Returns:
            The parsed JSON response as a dictionary, or None if all attempts fail.
        """
        for attempt in range(self.retry_attempts):
            try:
                # The session 'timeout' handles the overall request duration
                async with self.session.get(url, **kwargs) as response:
                    # Raises ClientResponseError for 4xx or 5xx responses
                    response.raise_for_status()

                    # aiohttp.ClientResponse.json() is a coroutine, must be awaited
                    return await response.json()
            except aiohttp.ClientError as e:
                # Catch network errors, timeouts, and HTTP status errors
                logging.error(
                    f"Async request failed (attempt {attempt + 1}/{self.retry_attempts}) for {url}: {e}")

                if attempt < self.retry_attempts - 1:
                    # Calculate a randomized backoff delay
                    random_delay = random.uniform(self.delay, self.delay * 2)
                    logging.debug(f"Waiting {random_delay:.2f}s before retrying...")
                    # Use asyncio.sleep() to wait without blocking the event loop
                    await asyncio.sleep(random_delay)
                else:
                    logging.error(
                        f"Max retry attempts reached for {url}. Request failed definitively.")
                    break
            except Exception as e:
                # Catch unexpected errors (e.g., JSON decoding failure)
                logging.error(
                    f"An unexpected error occurred during async request for {url}: {e}")
                break  # Do not retry on non-network/HTTP errors

        return None

    async def get(self, url: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """
        Public method to perform an asynchronous GET request, relying on _get_with_retries.
        """
        return await self._get_with_retries(url, **kwargs)
