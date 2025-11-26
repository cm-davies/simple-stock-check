import asyncio
from playwright.sync_api import sync_playwright
import time
import smtplib
from email.mime.text import MIMEText
import random
from playwright_stealth import stealth_sync

"""
Works:
https://www.amazon.co.uk
https://www.bremnertcg.co.uk (They have an email when in stock system anyway)
https://cosmiccollectables.co.uk
https://dansolotcg.co.uk
https://www.doublesleeved.co.uk
https://endocollects.co.uk
https://www.firestormcards.co.uk
https://romulusgames.com

Sometimes works:
https://www.pokemoncenter.com (Captcha and blocks)

Does not work:
https://www.smythstoys.com/uk/en-gb/ (Captcha and blocks)
https://thecardvault.co.uk (loads home page instead of product page)
https://endgameldn.com (Sign up prompt)
https://www.hillscards.co.uk (Email me when in stock msg reads as in stock by program. In stock items aren't identified as in stock)
https://hmv.com (Verify you are human page)
https://magicmadhouse.co.uk (Out of stock items are identified as in stock))
"""

# --- CONFIG ---
URLS = [
    "website.com/product-page"
]
EMAIL_FROM = "example@email.com"
EMAIL_TO = "example@email.com"
EMAIL_PASS = "xxxx xxxx xxxx xxxx"  # Use an app password, not your real password

def get_playwright_browser():
    # Launch Playwright with persistent context for profile reuse
    import os
    profile_dir = os.path.abspath("chrome_profile_playwright")
    os.makedirs(profile_dir, exist_ok=True)
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        locale="en-GB",
        viewport={"width": random.randint(1200, 1920), "height": random.randint(700, 1080)},
        args=[
            "--disable-blink-features=AutomationControlled",
            f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ]
    )
    # Apply stealth to all pages in the context
    for page in browser.pages:
        stealth_sync(page)
    return playwright, browser

def random_human_pause(min_sec=0.5, max_sec=2.5):
    time.sleep(random.uniform(min_sec, max_sec))

def check_in_stock(url):
    """
    Checks if the item at the given URL is in stock.
    Returns True if in stock, False if out of stock, None if page not found or error.
    If a CAPTCHA is detected, waits for manual solving before continuing.
    """
    playwright, browser = get_playwright_browser()
    page = browser.new_page()
    try:
        print(f"Checking stock for: {url}")
        page.goto(url, timeout=60000)
        print("Page loaded.")
        time.sleep(random.uniform(8.5, 12.5))
        # Detect CAPTCHA only if a form or input is present with keywords, or if a visible element contains the keywords
        page_content = page.content().lower()
        print("Page content fetched.")
        captcha_keywords = [
            'captcha',
            'please verify',
            'not a robot',
            'verify you are human',
            'security check',
            'access denied',
        ]
        found_captcha = False
        for word in captcha_keywords:
            print(f"Checking for CAPTCHA keyword: {word}")
            if page.locator(f'body:has-text("{word}")').count() > 0:
                found_captcha = True
                print(f"CAPTCHA keyword '{word}' found!")
                break
        if found_captcha:
            print("CAPTCHA detected! Please solve it manually in the opened browser window.")
            print("Press Enter here to continue after solving the CAPTCHA...")
            input()
            page.reload()
            time.sleep(random.uniform(3, 5))
        print("Simulating human-like scrolling...")
        scroll_steps = random.randint(1, 2)  # Reduced for speed
        for _ in range(scroll_steps):
            page.mouse.wheel(0, random.randint(100, 200))
            random_human_pause(0.2, 0.5)  # Shorter pause
        print("Simulating random mouse movement...")
        elements = page.query_selector_all('button, a, input, div')
        if elements:
            for _ in range(random.randint(1, 2)):  # Fewer moves
                el = random.choice(elements)
                try:
                    el.scroll_into_view_if_needed()
                    random_human_pause(0.1, 0.3)  # Shorter pause
                except Exception:
                    continue
        print("Checking for in-stock buttons/links...")
        button_texts = [
            "add to cart", "add to basket", "add basket", "add cart", "buy now", "purchase", "order now", "in stock"
        ]
        def normalize(text):
            for word in ["to", "the", "a", "an"]:
                text = text.replace(word, "")
            return text.replace(" ", "").lower()
        found = False
        # --- Robust in-stock button detection ---
        # Check all visible button-like elements, including <a>
        button_like_selectors = [
            'button',
            'input[type=submit]',
            'div[role=button]',
            'span[role=button]',
            'div[tabindex]',
            'span[tabindex]',
            'a'
        ]
        checked_elements = set()
        def element_has_instock_text(el):
            try:
                texts = []
                try:
                    t1 = el.inner_text()
                    if t1: texts.append(t1)
                except Exception: pass
                try:
                    t2 = el.text_content()
                    if t2 and t2 not in texts: texts.append(t2)
                except Exception: pass
                # Check all child nodes for text
                for child in el.query_selector_all('*'):
                    try:
                        ct = child.inner_text()
                        if ct and ct not in texts: texts.append(ct)
                    except Exception: pass
                    try:
                        ctc = child.text_content()
                        if ctc and ctc not in texts: texts.append(ctc)
                    except Exception: pass
                for text in texts:
                    norm_el = normalize(text)
                    for ref in button_texts:
                        if normalize(ref) in norm_el:
                            return text
            except Exception:
                pass
            return None
        for selector in button_like_selectors:
            elements = [el for el in page.query_selector_all(selector) if el.is_visible()]
            for el in elements:
                if el in checked_elements:
                    continue
                checked_elements.add(el)
                match_text = element_has_instock_text(el)
                if match_text:
                    # Check for disabled state (try is_disabled, aria-disabled, and disabled attribute)
                    is_disabled = False
                    try:
                        is_disabled = el.is_disabled()
                    except Exception:
                        pass
                    aria_disabled = el.get_attribute('aria-disabled')
                    if aria_disabled and aria_disabled.lower() == 'true':
                        is_disabled = True
                    disabled_attr = el.get_attribute('disabled')
                    if disabled_attr is not None:
                        is_disabled = True
                    if not is_disabled:
                        found = True
                        # Only print for non-Amazon URLs
                        if not ("amazon.co.uk" in url or "amazon.com" in url):
                            # Only print if not a review/report element
                            if not (match_text.strip().lower().startswith('report') or match_text.strip().lower().startswith('helpful')):
                                print(f"In stock button found: <{el.evaluate('e => e.tagName').lower()}> class='{el.get_attribute('class')}' text='{match_text.strip()}'")
                        break
            if found:
                break
        # --- Out of stock detection (site-specific and generic, but only in main product container) ---
        out_of_stock_phrases = [
            "out of stock", "sold out", "currently unavailable", "notify me when available", "pre-order closed", "preorder closed", "no longer available"
        ]
        site = url.split("/")[2]
        out_of_stock_found = False
        # Site-specific selector for cosmiccollectables.co.uk: limit to main product container
        if not found and "cosmiccollectables.co.uk" in site:
            try:
                # Try to get the main product container
                product_container = page.query_selector('.product') or page.query_selector('.product-single')
                if product_container:
                    # Check for out-of-stock phrases only inside this container
                    for selector in ['button', 'div', 'span']:
                        elements = [el for el in product_container.query_selector_all(selector) if el.is_visible()]
                        for el in elements:
                            try:
                                el_text = el.inner_text().strip().lower()
                                if any(phrase in el_text for phrase in out_of_stock_phrases):
                                    print(f"Out of stock phrase found in main product container: '{el_text}'")
                                    out_of_stock_found = True
                                    break
                            except Exception:
                                continue
                        if out_of_stock_found:
                            break
            except Exception as e:
                print(f"CosmicCollectables site-specific check error: {e}")
        # Generic fallback: only if not found and not on cosmiccollectables
        if not found and not out_of_stock_found and "cosmiccollectables.co.uk" not in site:
            outer_break = False
            for selector in ['span', 'div']:
                elements = [el for el in page.query_selector_all(selector) if el.is_visible()]
                for el in elements:
                    try:
                        el_text = el.inner_text().strip().lower()
                        for phrase in out_of_stock_phrases:
                            if phrase in el_text:
                                print(f"Out of stock phrase found: '{phrase}'")
                                out_of_stock_found = True
                                outer_break = True
                                break
                        if outer_break:
                            break
                    except Exception:
                        continue
                if outer_break:
                    break
        # --- Amazon-specific out-of-stock/invite detection and in-stock logic ---
        is_amazon = "amazon.co.uk" in url or "amazon.com" in url
        amazon_out_phrases = [
            "currently unavailable",
            "out of stock",
            "request invitation",
            "available by invitation",
            "we don't know when or if this item will be back in stock",
            "this item is not available",
            "temporarily out of stock",
            "unavailable",
            "invitation required",
            "not yet released"
        ]
        amazon_out_found = False
        amazon_instock_found = False
        if is_amazon:
            # Check for out-of-stock/invite phrases in main product areas (do NOT check 'body')
            try:
                for selector in ['#availability', '#buybox', '#dp']:
                    elements = [el for el in page.query_selector_all(selector) if el.is_visible()]
                    for el in elements:
                        try:
                            el_text = el.inner_text().strip().lower()
                            if any(phrase in el_text for phrase in amazon_out_phrases):
                                print(f"Amazon out-of-stock/invite phrase found: '{el_text}'")
                                amazon_out_found = True
                                break
                        except Exception:
                            continue
                if amazon_out_found:
                    pass  # Removed invalid break
            except Exception as e:
                print(f"Amazon-specific check error: {e}")
            # Only consider in-stock if button is in buybox or add-to-cart area
            try:
                buybox = page.query_selector('#buybox')
                if buybox:
                    add_btn = buybox.query_selector('#add-to-cart-button')
                    buy_now_btn = buybox.query_selector('#buy-now-button')
                    if (add_btn and add_btn.is_visible()) or (buy_now_btn and buy_now_btn.is_visible()):
                        amazon_instock_found = True
                else:
                    # Fallback: check for add-to-cart-button anywhere
                    add_btn = page.query_selector('#add-to-cart-button')
                    buy_now_btn = page.query_selector('#buy-now-button')
                    if (add_btn and add_btn.is_visible()) or (buy_now_btn and buy_now_btn.is_visible()):
                        amazon_instock_found = True
            except Exception:
                pass
        # Return logic (Amazon override)
        if is_amazon:
            if amazon_out_found:
                in_stock = False
                print(f"{url} is OUT OF STOCK (Amazon-specific logic).")
            elif amazon_instock_found:
                in_stock = True
                print(f"{url} is IN STOCK! (Amazon-specific logic)")
            else:
                print(f"No clear in-stock or out-of-stock indicator found for {url} (Amazon). Returning uncertain (None).")
                in_stock = None
        else:
            if found:
                in_stock = True
                print(f"{url} is IN STOCK!")
            elif out_of_stock_found:
                in_stock = False
                print(f"{url} is OUT OF STOCK.")
            else:
                print(f"No clear in-stock or out-of-stock indicator found for {url}. Returning uncertain (None).")
                in_stock = None
    except Exception as e:
        print(f"Error loading {url}: {e}")
        in_stock = None
    finally:
        random_human_pause(1.5, 3.5)
        try:
            page.close()
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass
        try:
            playwright.stop()
        except Exception:
            pass
    return in_stock

def send_email(url):
    """
    Sends an email notification that the item at the given URL is in stock.
    """
    msg = MIMEText(f"The item is back in stock! {url}")
    msg["Subject"] = "Item Back in Stock!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"Email sent for {url}")
    except Exception as e:
        print(f"Failed to send email for {url}: {e}")

if __name__ == "__main__":
    checked = set()
    urls_to_check = list(URLS)
    while urls_to_check:
        for url in urls_to_check[:]:  # Iterate over a copy so we can remove
            if url in checked:
                continue  # Skip already notified items
            status = check_in_stock(url)
            if status is True:
                send_email(url)
                checked.add(url)
                urls_to_check.remove(url)
            elif status is None:
                print(f"Could not check {url} (page not found or error). Will retry later.")
            else:
                print(f"{url} is still out of stock.")
            interval = random.randint(9, 11)  # 9 to 11 seconds
            print(f"Waiting {interval} seconds before next check...")
            time.sleep(interval)
        if not urls_to_check:
            print("All items checked and notified. Exiting.")
            break