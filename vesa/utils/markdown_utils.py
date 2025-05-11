"""
Markdown processing utilities.
"""
import re
from typing import List, Dict, Any, Optional

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


def render_markdown(text: str) -> str:
    """
    Render markdown text to HTML.
    
    Args:
        text: Markdown text
        
    Returns:
        HTML string
    """
    extensions = [
        'extra',
        FencedCodeExtension(),
        CodeHiliteExtension(css_class='highlight'),
        TableExtension()
    ]
    
    html = markdown.markdown(text, extensions=extensions)
    return html


def extract_links(text: str) -> List[Dict[str, Any]]:
    """
    Extract links from markdown text.
    
    Args:
        text: Markdown text
        
    Returns:
        List of dictionaries with link information
    """
    # Regular expression for markdown links: [text](url)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    links = []
    for match in re.finditer(link_pattern, text):
        link_text = match.group(1)
        link_url = match.group(2)
        
        links.append({
            'text': link_text,
            'url': link_url,
            'start': match.start(),
            'end': match.end()
        })
    
    return links


def extract_tags(text: str) -> List[str]:
    """
    Extract hashtags from markdown text.
    
    Args:
        text: Markdown text
        
    Returns:
        List of tags
    """
    # Regular expression for hashtags: #tag
    tag_pattern = r'(?:^|\s)#([a-zA-Z0-9_-]+)'
    
    tags = []
    for match in re.finditer(tag_pattern, text):
        tag = match.group(1)
        if tag not in tags:
            tags.append(tag)
    
    return tags


def create_document_preview(content: str, max_length: int = 200) -> str:
    """
    Create a preview of document content.
    
    Args:
        content: Document content
        max_length: Maximum length of preview
        
    Returns:
        Preview text
    """
    # Remove markdown formatting
    text = re.sub(r'#+\s+', '', content)  # Remove headings
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Replace links with text
    text = re.sub(r'[*_~]{1,2}(.*?)[*_~]{1,2}', r'\1', text)  # Remove bold/italic/strikethrough
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)  # Remove code blocks
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
    
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rstrip() + '...'
    
    return text
