import subprocess
import os

def create_gitingest(repo_path):
    """
    Creates a Gitingest digest of the Git repository at the given path.

    Args:
        repo_path (str): The absolute path to the Git repository directory.
    """
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
    repo_path = r"C:\Users\Earth\BEDROT PRODUCTIONS\slideshow_editor"
    create_gitingest(repo_path)
    print("\nScript finished.")