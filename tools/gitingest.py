import subprocess
import os
import sys

# Add src to path for core module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'src'))

# Import centralized configuration system
try:
    from core.env_loader import get_env_var, get_env_loader
    from core.path_utils import get_path_resolver
    
    # Load environment
    env_loader = get_env_loader()
    env_loader.load_environment()
    
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import core configuration system: {e}")
    CORE_AVAILABLE = False

def get_project_root():
    """Get project root directory using centralized config or fallback."""
    if CORE_AVAILABLE:
        try:
            path_resolver = get_path_resolver()
            return str(path_resolver.project_root)
        except Exception as e:
            print(f"Warning: Could not get project root from config: {e}")
    
    # Fallback: try to detect project root
    current = os.path.dirname(SCRIPT_DIR)  # Parent of tools directory
    if os.path.exists(os.path.join(current, 'launcher.py')):
        return current
    
    # Final fallback to hardcoded path (should be configurable via env var)
    return get_env_var('SLIDESHOW_PROJECT_ROOT', current) if CORE_AVAILABLE else current

def create_gitingest(repo_path=None):
    """
    Creates a Gitingest digest of the Git repository at the given path.

    Args:
        repo_path (str): The absolute path to the Git repository directory.
                        If None, uses project root from centralized config.
    """
    if repo_path is None:
        repo_path = get_project_root()
        print(f"Using project root: {repo_path}")
    try:
        # Construct the gitingest command
        command = ["gitingest", repo_path]

        print(f"Creating Gitingest digest for: {repo_path}")

        # Execute the command
        process = subprocess.run(command, capture_output=True, text=True, check=True)

        print("Gitingest process completed successfully.")
        print(f"Digest written to: {os.path.join(os.getcwd(), 'digest.txt')}")
        # You can further process the output if needed
        # print("Output:", process.stdout)
        # print("Errors:", process.stderr)

    except FileNotFoundError:
        print("Error: 'gitingest' command not found. Make sure it's installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Gitingest: {e}")
        print("Stderr:", e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Use centralized configuration instead of hardcoded path
    create_gitingest()  # Will auto-detect project root
    print("\nScript finished.")