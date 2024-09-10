import requests
import json

# Replace these with your own credentials
ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'
USER_ID = 'YOUR_USER_ID'

# Medium API endpoint to fetch user's posts
url = f"https://api.medium.com/v1/users/{USER_ID}/publications"

# Set up headers with the access token for authentication
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# Function to get all posts for the authenticated user
def get_user_posts(user_id):
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching posts: {response.status_code}, {response.text}")
    
    posts = response.json().get('data')
    return posts

# Fetch all your posts
posts = get_user_posts(USER_ID)

# Saving the posts to a local file
with open('my_medium_posts.json', 'w') as f:
    json.dump(posts, f, indent=4)

print(f"Downloaded {len(posts)} posts and saved to 'my_medium_posts.json'")
import requests
import json

# Replace these with your own credentials
ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'
USER_ID = 'YOUR_USER_ID'

# Medium API endpoint to fetch user's posts
url = f"https://api.medium.com/v1/users/{USER_ID}/publications"

# Set up headers with the access token for authentication
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

# Function to get all posts for the authenticated user
def get_user_posts(user_id):
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching posts: {response.status_code}, {response.text}")
    
    posts = response.json().get('data')
    return posts

# Fetch all your posts
posts = get_user_posts(USER_ID)

# Saving the posts to a local file
with open('my_medium_posts.json', 'w') as f:
    json.dump(posts, f, indent=4)

