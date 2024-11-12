# Imports
import os
import shutil

# Torrents download folder cleanup
def delete_downloads_folder_contents():
    """
    Locate the 'Downloads' folder within the same folder as the script and delete all contents
    if the user confirms by pressing 'y'.
    """
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to the Downloads folder
    downloads_folder = os.path.join(current_dir, "Downloads")
    
    # Check if the Downloads folder exists
    if not os.path.exists(downloads_folder):
        print(f"The Downloads folder does not exist in the current directory: {current_dir}")
        return
    
    # Confirm with the user before deleting the contents
    user_input = input(f"Are you sure you want to delete all contents in {downloads_folder}? (y/n): ").strip().lower()
    if user_input == 'y':
        try:
            # Delete all contents in the Downloads folder
            for filename in os.listdir(downloads_folder):
                file_path = os.path.join(downloads_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove the file or link
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove the directory and its contents
            print(f"All contents in {downloads_folder} have been deleted.")
        except Exception as e:
            print(f"An error occurred while deleting contents: {e}")
    else:
        print("Deletion aborted by the user.")

# Example usage
if __name__ == "__main__":
    delete_downloads_folder_contents()

