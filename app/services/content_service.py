import requests
from bs4 import BeautifulSoup
import logging
import re
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from config.config import (
    CONTENT_CLEANUP_MODEL,
    TITLE_GENERATION_MODEL
)
from .database_service import db

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI()

def is_url(text):
    """Check if the input is a URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(text) is not None

def fetch_url_content(url):
    """Fetch content from a URL with a browser User-Agent."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f'Error fetching URL {url}: {str(e)}')
        raise

# Constants for size limits
MAX_URL_LENGTH = 2048  # Standard browser URL length limit
MAX_INPUT_SIZE = 100 * 1024  # 100KB for direct text input
MAX_CONTENT_INFLATION = 1.2  # Maximum 20% increase from GPT processing

def validate_input(input_text):
    """Validate input and fetch URL content if necessary."""
    if not input_text or not input_text.strip():
        raise ValueError('Input text is empty')

    input_text = input_text.strip()

    # Check input size
    input_size = sys.getsizeof(input_text)
    if input_size > MAX_INPUT_SIZE:
        raise ValueError(f'Input text exceeds maximum size of {MAX_INPUT_SIZE/1024:.1f}KB')

    if is_url(input_text):
        # Check URL length
        if len(input_text) > MAX_URL_LENGTH:
            raise ValueError(f'URL exceeds maximum length of {MAX_URL_LENGTH} characters')
        # Fetch and return the raw HTML content
        return fetch_url_content(input_text), input_text

    return input_text, None

def clean_html_content(html_content):
    """Clean HTML content and extract readable text."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'header', 'footer', 'nav']):
        element.decompose()

    # Get text while preserving some structure
    paragraphs = []

    # Process headings
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = heading.get_text(strip=True)
        if text:
            paragraphs.append(text)

    # Process paragraphs
    for para in soup.find_all('p'):
        text = para.get_text(strip=True)
        if text:
            paragraphs.append(text)

    # Join with double newlines to maintain paragraph separation
    return '\n\n'.join(paragraphs)

def clean_text_with_gpt(text):
    """Use GPT to clean and format the text content."""
    # Get initial text size for inflation check
    initial_size = len(text.encode('utf-8'))
    """Use GPT to clean and format the text content."""
    messages = [
        {
            "role": "system",
            "content": """
            You will be given articles that have been extracted from web content. These articles will contain HTML, javascript, CSS, other code, web formatting and navigation elements that are not part of the main article content. Your task is to clean up these articles by removing any such unnecessary elements (the HTML, code, etc.) It is crucial that you do not alter the content of the articles in any way; only remove parts that are clearly not meant to be part of the article's title, author, date, section headings/titles and the main body. This includes, but is not limited to, related links, navigation menus, and footers not related to the article, and any stray formatting tags.

            Please ensure that:
            - The integrity of the article's main content remains untouched.
            - Section titles and articles titles remain intact
            - Only extraneous text or elements not part of the original article's narrative or informational content are removed.
            - Do not attempt to correct grammar, punctuation, or style issues unless they are part of removed elements.
            - Preserve all original formatting that pertains to the structure and presentation of the article content itself.
            - Only respond with the cleaned article content
            """
        },
        {
            "role": "user",
            "content": f"Article Content: {text}"
        }
    ]

    try:
        response = client.chat.completions.create(
            model=CONTENT_CLEANUP_MODEL,
            messages=messages,
            temperature=0.3,
            top_p=1
        )
        cleaned_text = response.choices[0].message.content.strip()

        # Check for content inflation
        cleaned_size = len(cleaned_text.encode('utf-8'))
        if cleaned_size > initial_size * MAX_CONTENT_INFLATION:
            logger.warning(f'GPT output exceeded inflation limit. Original: {initial_size}, Cleaned: {cleaned_size}')
            return text  # Return original text if inflation limit exceeded

        return cleaned_text
    except Exception as e:
        logger.error(f"Error cleaning text with GPT: {e}")
        return text

def generate_title(text):
    """Generate a title for the content using GPT."""
    messages = [
        {
            "role": "system",
            "content": "First, try to identify if there is a clear title within this article content. If you find a suitable title, provide it. If not, generate a new title that concisely represents its essence. The title should be brief and to the point. Only create a title if you don't identify the title. Only output the located or created title and nothing else. *Do not* output 'Title:' in the output."
        },
        {
            "role": "user",
            "content": f"Article Content: {text[:300]}"  # Only use first 300 chars for title generation
        }
    ]

    try:
        response = client.chat.completions.create(
            model=TITLE_GENERATION_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=20,
            top_p=1,
            stop=["\n"]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "Untitled Episode"

def save_episode_to_db(filename, title, description, duration=None):
    """Save episode information to the database."""
    pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return db.add_episode(filename, title, description, pub_date, duration=duration)

def generate_summary(text):
    """Generate a brief summary of the content using GPT."""
    messages = [
        {
            "role": "system",
            "content": "Generate a brief, engaging summary of the provided content in 2-3 sentences. Focus on the main points and key takeaways. Keep it concise but informative."
        },
        {
            "role": "user",
            "content": f"Content: {text[:1000]}"  # Use first 1000 chars for summary
        }
    ]

    try:
        response = client.chat.completions.create(
            model=CONTENT_CLEANUP_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            top_p=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "No summary available"

def process_validated_input(content, original_url=None):
    """Process pre-validated input content."""
    # If content is HTML (from URL), clean it
    if original_url:
        logger.info('Processing URL content')
        text = clean_html_content(content)
    else:
        logger.info('Processing raw text input')
        text = content

    # Clean the text with GPT
    logger.info('Cleaning text with GPT')
    cleaned_text = clean_text_with_gpt(text)

    # Generate title
    logger.info('Generating title')
    title = generate_title(cleaned_text)

    # Generate summary for description
    logger.info('Generating summary')
    summary = generate_summary(cleaned_text)

    # Create description based on input type
    if original_url:
        description = f"From URL: {original_url}\n\n\n{summary}"
    else:
        description = summary

    return {
        'text': cleaned_text,
        'title': title,
        'description': description
    }

def process_input(input_text):
    """Process input text or URL into clean content for TTS."""
    # This is kept for backward compatibility
    # It combines validation and processing
    content, url = validate_input(input_text)
    return process_validated_input(content, url)
