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
Module for handling HTTP requests with persistence, retries, and proper session management.

This module defines an HTTPClient class that manages requests and retries, improves error handling,
and ensures that session cookies and headers are maintained throughout requests. It can be used for
API calls, downloading files, and any HTTP requests requiring a persistent session.
"""


__author__ = "Laerinok"
__date__ = "2025-08-24"  # Last update


import logging
import random
import time

import requests

import cli
import global_cache


class HTTPClient:
    """
    A class that encapsulates HTTP requests with support for retries, session persistence, and improved error handling.

    Attributes:
        session (requests.Session): The HTTP session used for making requests.
        retry_attempts (int): The number of retry attempts in case of failure.
        delay (float): The delay between retries.
        timeout (int): The timeout for requests in seconds.
    """

    def __init__(self, retry_attempts=3, delay=1.5):
        """
        Initializes the HTTPClient with default retry attempts and delay between retries.

        Args:
            retry_attempts (int): The number of retry attempts in case of failure (default is 3).
            delay (float): The delay in seconds between retries (default is 1.5 seconds).
        """
        self.session = requests.Session()
        self.retry_attempts = retry_attempts
        self.delay = delay

        args = cli.parse_args()
        self.timeout = args.timeout or int(global_cache.config_cache["Options"]["timeout"])
        if self.timeout <= 0:
            logging.error("Timeout must be a positive integer.")
            raise ValueError("Timeout must be a positive integer.")

    @staticmethod
    def _get_random_headers():
        """
        Generate random headers to avoid blocking by the server.

        Returns:
            dict: A dictionary of random headers to be used for the request.
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:70.0) Gecko/20100101 Firefox/70.0",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        ]
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        return headers

    def _get_with_retries(self, url, **kwargs):
        """
        Perform a GET request with retries.

        Args:
            url (str): The URL for the GET request.
            **kwargs: Additional parameters for the GET request (headers, params, etc.).

        Returns:
            requests.Response: The response object from the GET request, or None if the request failed.
        """
        for attempt in range(self.retry_attempts):
            try:
                # Add random headers to the request
                headers = kwargs.get('headers', {})
                headers.update(self._get_random_headers())
                kwargs['headers'] = headers

                # Supprimer 'timeout' de kwargs si présent
                kwargs.pop('timeout', None)

                response = self.session.get(url, timeout=int(self.timeout), **kwargs)
                response.raise_for_status()  # Raise an exception for HTTP error codes
                return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.delay)  # Wait before retrying
                else:
                    logging.error("Max retry attempts reached. Request failed.")
            finally:
                # Wait for a random time between 0.5 and 1.5 seconds (this is always applied)
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
        return None

    def get(self, url, **kwargs):
        """
        Perform a GET request using the session, with retries if necessary.

        Args:
            url (str): The URL for the GET request.
            **kwargs: Additional parameters for the GET request.

        Returns:
            requests.Response: The response object if the request succeeds, None if it fails after retries.
        """
        return self._get_with_retries(url, **kwargs)

    def close(self):
        """
        Closes the HTTP session.
        """
        self.session.close()
