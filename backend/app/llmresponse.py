import base64
from app.webscraper import fetch_url
from app.cssrag import save_css_file, get_llm_answer_for_css, remove_css_dirs
import anthropic
from dotenv import load_dotenv
import requests
import os
import httpx
import re
from bs4 import BeautifulSoup
from pathlib import Path

load_dotenv()

# Set all file paths
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_DIR = BASE_DIR / "final_html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

# Initialize the Anthropic client

client=anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

def llm_response(url, topic):
    if not url:
        return {"error": "No URL provided"}
    result = fetch_url(url)
    if "error" in result:
        return {"error": result["error"]}
    
    # Extracting the DOM, CSS content, and screenshot from the result of the web scraping
    
    dom = result.get("dom", "")
    dom = dom[:10000]
    css_content = result.get("css_content", [])
    screenshot = result.get("screenshot", "")

    save_css_file(css_content, url)

    # Encoding screenshot into LLM readable format

    image_url = screenshot
    image_media_type = "image/png"
    image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

    # Creating the initial prompt for the LLM to generate HTML skeleton code

    intro_prompt = """
    Given a SNIPPET of the HTML DOM of a website and a screenshot of the website, produce
    short HTML code that serves as a PREVIEW of a website about {topic_input}. The preview should be aesthetically
    similar to the provided screenshot.

    For any CSS styling (colors, fonts, layout), leave a placeholder comment of the form:
    
    <!-- CSS_REQ: <selector> -->

    where <selector> is either a class or id that needs styling (for instance, ".button", "#header", "body", etc.).
    Do NOT attempt to write actual CSS here—just output the HTML and insert EXACTLY ONE placeholder comment per selector 
    that needs styling.
    """

    intro_prompt_edited = intro_prompt.format(
        topic_input=topic
    )

    dom_prompt = f"SNIPPET of the HTML DOM:\n{dom}"
    transition = "\n\nand the screenshot provided below" 
    llm_request = "\n\nOutput the aesthetically similar HTML skeleton code for {topic_input} with placeholders for CSS styling that look like <!-- CSS_REQ: .some-selector -->."

    llm_request_edited = llm_request.format(
        topic_input=topic
    )

    # Sending the request to the LLM with the prompts and the screenshot

    message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": [
                {
                    "type": "text",
                    "text": intro_prompt_edited

                },
                {
                    "type": "text",
                    "text": dom_prompt

                },
                {
                    "type": "text",
                    "text": transition
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": llm_request_edited
                }
            ],
            }
    ]
    )

    # Checking if the message content is valid and extracting the text content

    if message.content and isinstance(message.content, list) and len(message.content) > 0:
        for content_block in message.content:
            if hasattr(content_block, 'text') and content_block.text:
                print(content_block.text)
        else:
            print("No text content found in the message.")
    
    unstylized_html = content_block.text

    # Extracting CSS selectors from the unstylized HTML using regex

    selector_list = set(re.findall(r"<!-- CSS_REQ:\s*([^ ]+)\s*-->", unstylized_html))

    # Generating CSS blocks for each selector using the LLM

    css_blocks = {}
    for selector in selector_list:
        css_blocks[selector] = get_llm_answer_for_css(selector, url)

    # Formatting the CSS blocks and inserting them into the HTML

    def strip_backticks(css: str) -> str:
        return css.replace("```css", "").replace("```", "").strip()

    all_css = "\n\n".join(
        strip_backticks(block["answer"])
        for block in css_blocks.values()
        if isinstance(block, dict) and "answer" in block and block["answer"].strip() != "```css\n```"
    )

    bs = BeautifulSoup(unstylized_html, "html.parser")

    if bs.head is None:
        head_tag = bs.new_tag("head")
        bs.insert(0, head_tag)
    else:
        head_tag = bs.head

    # Adding the CSS styles to the head of the HTML document

    style_tag = bs.new_tag("style")
    style_tag.string = all_css
    head_tag.append(style_tag)

    for css_selector_placeholder in bs.find_all(string=lambda x: isinstance(x, type(bs.Comment))):
        if "CSS_REQ:" in css_selector_placeholder:
            css_selector_placeholder.extract()

    result_html = str(bs)

    # Creating the second prompt for the LLM to refine the HTML code

    intro_prompt_two = """
    You will be given a rough draft of an HTML code for the cloned website that has the appropriate CSS options 
    that the original website uses.
     
    Your task is to look through this code and make sure that the HTML code is well-formed, syntactically correct
    and thorough such that the website is aesthetically similar to the website in the following screenshot. 

    You MUST use the styles provided by the rough draft provided, but you can add more styles if you think they are necessary. 
    Do NOT delete any of the styles that are currently present in the HTML rough draft code that is provided.

    Make sure every text that is shown is about the topic of the website, which is {topic_input} while keeping all styles & structure the same.

    Don't add any additional comments or explanations, just output the final HTML code.
    """

    intro_prompt_two_edited = intro_prompt_two.format(
        topic_input=topic
    )

    html_rough_draft = f"Rough Draft of the HTML Code:\n{result_html}"

    transition_two = "Here is the screenshot: \n\n"

    # Sending the second request to the LLM with the refined prompts and the screenshot

    message_two = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=6000,
    messages=[
        {"role": "user", "content": [
                {
                    "type": "text",
                    "text": intro_prompt_two_edited
                },
                {
                    "type": "text",
                    "text": html_rough_draft
                },
                {
                    "type": "text",
                    "text": transition_two
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data,
                    },
                }
            ],
            }
        ]
    )

    # Checking if the second message content is valid and extracting the text content

    if message_two.content and isinstance(message_two.content, list) and len(message_two.content) > 0:
        for content_block_two in message_two.content:
            if hasattr(content_block_two, 'text') and content_block_two.text:
                print(content_block_two.text)
        else:
            print("No text content found in the message.")

    final_html = content_block_two.text

    # Saving the final HTML code to a file

    with open(HTML_DIR / f"{url.split('//')[-1].replace('/', '_')}.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    remove_css_dirs()
