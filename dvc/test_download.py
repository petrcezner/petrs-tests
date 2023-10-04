import os

from dvc.api import DVCFileSystem

"""
Test script for downloading data from a DVC remote repository. Data are stored on the private blob storage. See .env.example for the required environment variables.
"""


def list_files(directory: str) -> None:
    """
    List files in a directory recursively
    :param directory:
    :return:
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            print(file_path)


url = f"https://petrcezner:{os.environ['GITHUB_TOKEN']}@https://github.com/DataSentics/qi-project-template.git"
fs = DVCFileSystem(url, rev="v3")

fs.get("data/image_folder_datasets", "./data/", recursive=True)

# Get the current directory
current_directory = os.getcwd()

# Call the function to list all files recursively
list_files(current_directory)
