# To prepare an entire medium blog for ingestion.

First download the entire blog archive.
visit https://medium.com/me/settings/security and select Download your information

Watch your email for notification within the next 24 hours.

Save to the downloads directory and process it to extract the story content, which will be saved to the author directory

## How to Use the Script
Save the Script: Save the script as extract_medium_stories.py.
Prepare Your Input:
The input can be either:
A ZIP file (e.g., medium-archive.zip).
A directory that has been extracted from a Medium ZIP archive.

Run the Script:
Open your terminal or command prompt.
Navigate to the directory where you saved the script.
Run the script using the following command:

```python code/medium_posts.py <path_to_zip_or_directory> <output_directory>```

Replace <path_to_zip_or_directory> with the path to the downloaded ZIP file or the expanded directory, and <output_directory> with authors/<author name>/medium_posts.

## Script Details
Two Modes of Operation:
If the input is a ZIP file, the script will extract the posts directory from the ZIP and save the stories to the specified output directory.
If the input is an already expanded directory, the script will look for the posts subdirectory, and then copy the stories to the specified output directory.

Story Filtering:
The script ignores any files in the posts subdirectory that start with "draft", ensuring that only published stories are processed.
Flexible Input:
The script can handle both ZIP files and directories, making it versatile for different use cases.

Output:
Stories are saved or copied into the specified output directory, with their filenames preserved.



