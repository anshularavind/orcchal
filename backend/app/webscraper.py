from bs4 import BeautifulSoup
import requests
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartScrapeJobParams
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the Hyperbrowser client

client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

# Function to fetch and process the URL, extracting DOM, CSS, and screenshot

def fetch_url(url):
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            raise ValueError("Invalid URL: URL must start with 'http://' or 'https://'")

        # Start the scrape job using Hyperbrowser

        scrape_result = client.scrape.start_and_wait(
            StartScrapeJobParams(
                url=url,
                scrape_options={
                    "formats": ["html", "screenshot"],
                    "screenshot_options": {
                        "fullPage": True,
                        "format": "png",
                    }
                }
            )
        )

        html_content = scrape_result.data.html
        screenshot = scrape_result.data.screenshot

        if not html_content:
            raise ValueError("Failed to retrieve HTML content from the provided URL.")
        
        # Parse the HTML content using BeautifulSoup

        bs = BeautifulSoup(html_content, "html.parser")

        dom = bs.prettify()

        styles = [tag.get_text() for tag in bs.find_all("style")]

        css_links = [link.get("href") for link in bs.find_all("link", rel="stylesheet")]

        # Fetch CSS content from linked stylesheets

        css_content = []
        for css_link in css_links:
            try:
                if not css_link.startswith("http"):
                    css_link = url + css_link 
                response = requests.get(css_link)
                if response.status_code == 200:
                    css_content.append(response.text)
            except requests.RequestException as e:
                css_content.append(f"Error fetching CSS from {css_link}: {e}")

        return {
            "dom": dom,
            "styles": styles,
            "css_content": css_content,
            "screenshot": screenshot
        }

    except ValueError as ve:
        return {"error": str(ve)}
    except requests.RequestException as re:
        return {"error": f"Network error: {re}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}