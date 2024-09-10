import os
import sys
import xml.etree.ElementTree as ET

# Check if the correct number of arguments is provided
if len(sys.argv) < 3:
    print("Usage: python script_name.py your-blog-archive.xml output_directory")
    sys.exit(1)

# Get the XML file and output directory from the command line arguments
xml_file = sys.argv[1]
output_dir = sys.argv[2]

# Check if the XML file exists
if not os.path.isfile(xml_file):
    print(f"Error: File '{xml_file}' not found.")
    sys.exit(1)

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the XML file
tree = ET.parse(xml_file)
root = tree.getroot()

# Define the XML namespaces
ns = {'atom': 'http://www.w3.org/2005/Atom', 'blogger': 'http://schemas.google.com/blogger/2008'}

# Iterate over each entry in the XML
for entry in root.findall('atom:entry', ns):
    # Check if the entry is a post (not a comment)
    if entry.find('atom:category[@term="http://schemas.google.com/blogger/2008/kind#post"]', ns) is None:
        continue

    post_status = entry.find('atom:control/blogger:draft', ns)
    
    # Skip drafts
    if post_status is not None and post_status.text == 'yes':
        continue

    title = entry.find('atom:title', ns).text
    link_element = entry.find('atom:link[@rel="alternate"]', ns)
    content = entry.find('atom:content', ns).text
    
    # Only process the post if it has a title and link
    if title and link_element is not None:
        link = link_element.get('href')
        
        # Create a filename based on the post title
        filename = f"{title.replace(' ', '_').replace('/', '-')}.txt"
        filepath = os.path.join(output_dir, filename)

        # Write the post content to a file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(f"Title: {title}\n")
            file.write(f"URL: {link}\n")
            file.write("\n")
            file.write(content)

print(f"Posts have been extracted and saved to the '{output_dir}' directory.")
