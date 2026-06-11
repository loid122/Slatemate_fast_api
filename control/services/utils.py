import requests
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Rule, Category, Website
import google.generativeai as genai

# Gemini AI Setup
genai.configure(api_key="AIzaSyCYs-Ph0Dm5KY_irtq5qV7pqSuwkqQK5ao")
model = genai.GenerativeModel('gemini-2.0-flash')


async def gemini_classifyurl(url: str, website_text: str) -> str:
    prompt = (
        f"Can you classify this website with url {url}, If this is text scraped from this website "
        f"by doing a GET request: {website_text}, based on the text and your analysis on the url, "
        f"classify this website into the following categories: "
        "(Commerce & Marketplace, Media & Communication, Education & Knowledge, "
        "Gaming & Entertainment, Health & Wellness, Business & Professional Services, "
        "Travel & Local Services, Technology & Developer Tools, Security & Identity, "
        "Science & Environment, Lifestyle & Personal Interests, Specialized & Miscellaneous, "
        "Shopping, Social Media, Adult, News, Banking, Search Engine). "
        "Respond with only the category name."
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def scrape_and_categorize(url: str) -> str:
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

        text_blocks = [line.strip() for line in soup.get_text().splitlines() if line.strip()]
        first_lines = " ".join(text_blocks[:5])

        full_text = f"{title} {meta_desc} {first_lines}"
        category = gemini_classifyurl(url, full_text)

        return category
    except Exception as e:
        print("Error:", e)
        return "Unknown"


async def is_category_blocked(user_id: int, category: str, db: AsyncSession) -> bool:
    result = await db.execute(select(Rule).filter(Rule.user_id == user_id))
    rule = result.scalars().first()
    if rule:
        return category in (rule.categories or [])
    return False


async def update_web_categories_db(user_id: int, category: str, website: str, db: AsyncSession):
    # Ensure category exists
    result = await db.execute(select(Category).filter(Category.category_name == category))
    category_obj = result.scalars().first()
    if not category_obj:
        category_obj = Category(category_name=category)
        db.add(category_obj)
        await db.commit()
        await db.refresh(category_obj)

    # Insert website
    result = await db.execute(select(Website).filter(Website.website_name == website))
    website_obj = result.scalars().first()
    if not website_obj:
        website_obj = Website(website_name=website, category_id=category_obj.id)
        db.add(website_obj)
        await db.commit()

    # Update allowed list in Rule
    result = await db.execute(select(Rule).filter(Rule.user_id == user_id))
    rule = result.scalars().first()
    if not rule:
        rule = Rule(user_id=user_id, allowed_list=[])
        db.add(rule)

    if website not in (rule.allowed_list or []):
        rule.allowed_list.append(website)

    await db.commit()

import psycopg

conn_params = {
    "host": "localhost",
    "dbname": "webcategories_db",
    "user": "myuser",
    "password": "mypassword"
}

def expand_categories(categories: list, websites: list):
    expanded_websites = list(websites)
    try:
        conn = psycopg.connect(**conn_params)
        cur = conn.cursor()
        for category in categories:
            cur.execute("SELECT id FROM Categories WHERE category_name = %s", (category,))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT website_name FROM Websites WHERE category_id = %s", (row[0],))
                expanded_websites.extend([r[0] for r in cur.fetchall()])
    finally:
        cur.close()
        conn.close()
    return list(set(expanded_websites))
