"""Browser-based X poster. Uses real Chromium with auth cookies, fills compose
form, clicks Post. Avoids 226 by using real TLS + DOM interactions."""
import time

import config


def _build_cookies():
    cookies = []
    if config.X_AUTH_TOKEN:
        for d in (".x.com", ".twitter.com"):
            cookies.append({"name": "auth_token", "value": config.X_AUTH_TOKEN, "domain": d, "path": "/", "httpOnly": True, "secure": True})
    if config.CT0:
        for d in (".x.com", ".twitter.com"):
            cookies.append({"name": "ct0", "value": config.CT0, "domain": d, "path": "/", "secure": True})
    return cookies


def post_via_browser(text, reply_to_url=None, headless=True):
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import stealth
    except ImportError as exc:
        raise RuntimeError("playwright not installed") from exc

    text = text.strip()
    if len(text) > 280 or not text:
        raise ValueError(f"tweet length invalid: {len(text)}")

    launch_kwargs = {"headless": headless, "args": [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ]}
    if hasattr(config, "CHROME_PATH") and getattr(config, "CHROME_PATH", ""):
        launch_kwargs["executable_path"] = config.CHROME_PATH

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"),
            locale="en-US",
            timezone_id="America/Los_Angeles",
        )
        ctx.add_cookies(_build_cookies())
        page = ctx.new_page()
        stealth(page)

        warmup_url = "https://x.com/home"
        page.goto(warmup_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)
        try:
            page.mouse.move(640, 400)
            page.wait_for_timeout(600)
            page.mouse.wheel(0, 200)
            page.wait_for_timeout(800)
        except Exception:
            pass

        if reply_to_url:
            page.goto(reply_to_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3500)
            try:
                page.locator('[data-testid="reply"]').first.click(timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
        else:
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3500)

        editor = page.locator('[data-testid="tweetTextarea_0"]').first
        editor.wait_for(state="visible", timeout=15000)
        editor.click()
        page.wait_for_timeout(700)
        page.keyboard.type(text, delay=random_delay(20, 50))
        page.wait_for_timeout(700)

        for selector in ['[data-testid="tweetButtonInline"]', '[data-testid="tweetButton"]']:
            try:
                btn = page.locator(selector).first
                btn.wait_for(state="visible", timeout=10000)
                btn.click()
                break
            except Exception:
                continue

        page.wait_for_timeout(5000)
        result_url = page.url
        new_tweet_id = None
        if "/status/" in result_url:
            new_tweet_id = result_url.split("/status/")[-1].split("?")[0].split("/")[0]

        browser.close()
        return new_tweet_id or result_url


def random_delay(lo, hi):
    import random
    return random.randint(lo, hi) / 1000.0
