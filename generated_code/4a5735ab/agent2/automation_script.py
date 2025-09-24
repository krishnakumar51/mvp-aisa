# -*- coding: utf-8 -*-
"""
Playwright automation script based on the provided JSON blueprint.
The script uses Faker to generate realistic data for emails, passwords, and names.
"""

from playwright.sync_api import sync_playwright, Playwright, expect
import time
import random
import string
from faker import Faker


def random_email(fake: Faker) -> str:
    """Generate a realistic email address."""
    return fake.email()


def random_password() -> str:
    """Generate a complex password satisfying common criteria."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    pwd = "".join(random.choice(chars) for _ in range(12))
    # Ensure at least one of each required character type
    if not any(c.islower() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in pwd):
        pwd = pwd[:-1] + random.choice(string.digits)
    if not any(c in "!@#$%^&*()" for c in pwd):
        pwd = pwd[:-1] + random.choice("!@#$%^&*()")
    return pwd


def random_name(fake: Faker) -> tuple[str, str]:
    """Generate a realistic first and last name."""
    return fake.first_name(), fake.last_name()


def run(playwright: Playwright) -> None:
    """Main function to run the web automation script."""
    print("Setting up browser...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()
    page.set_default_timeout(60000)  # 60 s default timeout
    print("✓ Browser is ready.")

    # ------------------------------------------------------------------
    # 1️⃣  Navigate to the start page (replace with the actual URL)
    # ------------------------------------------------------------------
    page.goto("https://outlook.live.com")  # <-- Change this to the real URL
    # Wait for the page to fully load
    page.wait_for_load_state("networkidle")

    # ------------------------------------------------------------------
    # Data generation
    # ------------------------------------------------------------------
    fake = Faker()
    email = random_email(fake)
    password = random_password()
    first_name, last_name = random_name(fake)

    # ------------------------------------------------------------------
    # 1. Click "Crear cuenta" button
    # ------------------------------------------------------------------
    page.click("text=Crear cuenta")
    time.sleep(2)

    # ------------------------------------------------------------------
    # 2. Enter desired email address
    # ------------------------------------------------------------------
    email_input = page.locator("input[name='email'], input[type='email']")
    email_input.wait_for(state="visible")
    email_input.fill(email)

    # ------------------------------------------------------------------
    # 3. Click "Siguiente" button
    # ------------------------------------------------------------------
    page.click("text=Siguiente")

    # ------------------------------------------------------------------
    # 4. Create a password
    # ------------------------------------------------------------------
    password_input = page.locator("input[type='password'], input[name='password']")
    password_input.wait_for(state="visible")
    password_input.fill(password)

    # ------------------------------------------------------------------
    # 5. Click "Siguiente" button
    # ------------------------------------------------------------------
    page.click("text=Siguiente")

    # ------------------------------------------------------------------
    # 6-7. Enter first and last name
    # ------------------------------------------------------------------
    first_name_input = page.locator("input[placeholder='First name'], input[name='firstName']")
    last_name_input = page.locator("input[placeholder='Last name'], input[name='lastName']")
    first_name_input.wait_for(state="visible")
    first_name_input.fill(first_name)
    last_name_input.fill(last_name)

    # ------------------------------------------------------------------
    # 8. Click "Siguiente" button
    # ------------------------------------------------------------------
    page.click("text=Siguiente")

    # ------------------------------------------------------------------
    # 9-12. Set country/region and date of birth
    # ------------------------------------------------------------------
    country_input = page.locator("input[placeholder='Country/Region'], input[name='country']")
    day_input = page.locator("input[placeholder='Day'], input[name='day']")
    month_input = page.locator("input[placeholder='Month'], input[name='month']")
    year_input = page.locator("input[placeholder='Year'], input[name='year']")

    country_input.wait_for(state="visible")
    country_input.fill("México")
    day_input.fill("24")
    month_input.fill("febrero")
    year_input.fill("1996")

    # ------------------------------------------------------------------
    # 13. Click "Siguiente" button
    # ------------------------------------------------------------------
    page.click("text=Siguiente")

    # ------------------------------------------------------------------
    # 14-15. CAPTCHA – press and hold, then continue holding
    # ------------------------------------------------------------------
    captcha_button = page.locator("text=PRESIONAR Y MANTENER PRESIONADO")
    captcha_button.wait_for(state="visible")
    box = captcha_button.bounding_box()
    if box:
        # Move mouse to the button and press down
        page.mouse.move(box["x"] + 5, box["y"] + 5)
        page.mouse.down()
        # Hold for a few seconds (adjust as needed for the real CAPTCHA)
        time.sleep(5)
        # Release the mouse
        page.mouse.up()
    else:
        print("⚠️  CAPTCHA button not found – skipping hold steps")

    # ------------------------------------------------------------------
    # 16. Click "ACEPTAR" button to finish
    # ------------------------------------------------------------------
    page.click("text=ACEPTAR")
    # Optional: Wait for a success message (adjust selector to match real site)
    try:
        page.wait_for_selector("text=Your account has been created", timeout=120000)
        print("✓ Account creation succeeded.")
    except Exception:
        print("⚠️  Success message not found – account may still be pending.")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)