import urllib.request
import json
import ssl
from typing import Tuple, Optional, Dict, Any
from src.finder_sight.utils.logger import logger

import re

def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse a version string (e.g., 'v1.2.3', '1.2.3-alpha') into a tuple of integers.
    Extracts all numeric sequences and treats them as version components.
    """
    if not version_str:
        return (0,)
    
    # Extract all numeric parts
    # Using re.findall to get all digit sequences
    numeric_parts = re.findall(r'\d+', version_str)
    
    if not numeric_parts:
        return (0,)
        
    return tuple(int(p) for p in numeric_parts)

def check_for_updates(current_version: str, repo_owner: str, repo_name: str) -> Tuple[bool, str, str]:
    """
    Check for updates on GitHub.
    
    Args:
        current_version: The current version string of the app.
        repo_owner: GitHub repository owner.
        repo_name: GitHub repository name.
        
    Returns:
        Tuple containing:
        - update_available (bool): True if a newer version is found.
        - latest_version (str): The tag name of the latest release.
        - release_url (str): HTML URL of the latest release.
        - error_message (Optional[str]): Error message if check failed, otherwise None.
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    logger.debug(f"Checking updates from {api_url}")
    
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            api_url, 
            headers={'User-Agent': 'FinderSight-Updater'}
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            if response.status != 200:
                msg = f"GitHub API returned status {response.status}"
                logger.warning(msg)
                return False, current_version, "", msg
                
            data: Dict[str, Any] = json.loads(response.read().decode('utf-8'))
            latest_tag = data.get('tag_name', '')
            html_url = data.get('html_url', '')
            
            if not latest_tag:
                return False, current_version, "", "No tag found in release"
            
            current_ver_tuple = parse_version(current_version)
            latest_ver_tuple = parse_version(latest_tag)
            
            if latest_ver_tuple > current_ver_tuple:
                logger.info(f"New version found: {latest_tag} (current: {current_version})")
                return True, latest_tag, html_url, None
            
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}"
        if e.code == 404:
            logger.info("No releases found for this repository.")
            error_msg = "No releases found"
        else:
            logger.error(f"HTTP error checking for updates: {e}")
        return False, current_version, "", error_msg
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to check for updates: {e}")
        return False, current_version, "", error_msg
        
    return False, latest_tag if 'latest_tag' in locals() else current_version, html_url if 'html_url' in locals() else "", None
