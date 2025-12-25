import subprocess
import re
import os

def get_latest_tag():
    try:
        # Get the latest tag from git
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode('utf-8').strip()
        # Remove 'v' prefix if present
        if tag.startswith('v'):
            tag = tag[1:]
        return tag
    except Exception as e:
        print(f"Warning: Could not get git tag: {e}")
        return None

def update_v_file(version):
    init_file = os.path.join('src', 'finder_sight', '__init__.py')
    if not os.path.exists(init_file):
        print(f"Error: {init_file} not found.")
        return

    with open(init_file, 'r') as f:
        content = f.read()

    # Replace __version__ = "..." with the new version
    new_content = re.sub(r'__version__\s*=\s*".*?"', f'__version__ = "{version}"', content)

    with open(init_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated {init_file} to version {version}")

if __name__ == "__main__":
    version = get_latest_tag()
    if version:
        update_v_file(version)
    else:
        print("No version update performed.")
