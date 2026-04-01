"""Shared Playwright browser session with stealth Firefox configuration."""

import atexit
import threading

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

_IDLE_TIMEOUT = 120  # seconds


class BrowserSession:
    """Lazy-initialized Firefox browser with stealth settings.

    Call get_page() from any tool to obtain a Page object.
    The browser launches on first use and shuts down after
    _IDLE_TIMEOUT seconds of inactivity.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._idle_timer: threading.Timer | None = None

    def get_page(self) -> Page:
        """Return the shared Page, launching the browser if needed."""
        with self._lock:
            self._cancel_idle_timer()
            if self._page is None or self._browser is None:
                self._launch()
            return self._page  # type: ignore[return-value]

    def release(self) -> None:
        """Signal that the current tool call is done. Starts idle timer."""
        with self._lock:
            self._start_idle_timer()

    def _launch(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.firefox.launch(
            headless=True,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "media.navigator.enabled": True,
                "privacy.resistFingerprinting": False,
            },
        )
        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            color_scheme="light",
            java_script_enabled=True,
        )
        self._page = self._context.new_page()

    def _shutdown(self) -> None:
        with self._lock:
            self._cancel_idle_timer()
            for resource in (self._page, self._context, self._browser):
                try:
                    if resource is not None:
                        resource.close()
                except Exception:
                    pass
            self._page = None
            self._context = None
            self._browser = None
            if self._playwright is not None:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

    def _start_idle_timer(self) -> None:
        self._idle_timer = threading.Timer(_IDLE_TIMEOUT, self._shutdown)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def _cancel_idle_timer(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None


browser_session = BrowserSession()
atexit.register(browser_session._shutdown)
