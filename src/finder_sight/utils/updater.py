import urllib.request
import json
import ssl
from typing import Tuple, Optional, Dict, Any
from src.finder_sight.utils.logger import logger

def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse a version string (e.g., 'v1.2.3' or '1.2.3') into a tuple of integers.
    Non-numeric components are ignored/treated as delimiters.
    """
    # Remove 'v' prefix if present
    if version_str.lower().startswith('v'):
        version_str = version_str[1:]
    
    parts = []
    for part in version_str.split('.'):
        try:
            parts.append(int(part))
        except ValueError:
            # Handle cases like 'rc1', 'beta' if strictly necessary, 
            # but for this simple app, we expect standard semver.
            # Just skipping non-digits for now or stopping.
            continue
    return tuple(parts)

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
    """
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    logger.debug(f"Checking updates from {api_url}")
    
    try:
        # Create a context that doesn't verify certificates if strictly necessary, 
        # but usually default is fine. Using standard context.
        ctx = ssl.create_default_context()
        
        req = urllib.request.Request(
            api_url, 
            headers={'User-Agent': 'FinderSight-Updater'}
        )
        
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            if response.status != 200:
                logger.warning(f"GitHub API returned status {response.status}")
                return False, current_version, ""
                
            data: Dict[str, Any] = json.loads(response.read().decode('utf-8'))
            
            latest_tag = data.get('tag_name', '')
            html_url = data.get('html_url', '')
            
            if not latest_tag:
                return False, current_version, ""
            
            current_ver_tuple = parse_version(current_version)
            latest_ver_tuple = parse_version(latest_tag)
            
            if latest_ver_tuple > current_ver_tuple:
                logger.info(f"New version found: {latest_tag} (current: {current_version})")
                return True, latest_tag, html_url
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.info("No releases found for this repository.")
        else:
            logger.error(f"HTTP error checking for updates: {e}")
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        
    return False, current_version, ""
