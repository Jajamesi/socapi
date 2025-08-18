from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from __init__ import SocAPIClient

import asyncio

from . import utils


class Constructor:
    """
    A class to handle creating and modifying poll questions from a socpanel API.

    Expects the main class to define:
    - self._headers: headers for requests.
    - self._login(): method to login in panel.
    - self._request(): method to send generic requests.

    Attributes:
    -----------
    headers : dict
        Headers for the API requests.

    Methods:
    --------

    """



