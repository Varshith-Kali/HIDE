import random
import requests
import os
#

# Generate random posts with media from online sources
def generate_random_posts():
    users = ['john_doe', 'jane_smith', 'alex_jones']
    posts = []

    for user in users:
        post_text = random.choice([
            "Had an amazing day!",
            "Check out this cool sunset.",
            "Here is a video from my vacation!",
            "Loving the new features on HIDE!"
        ])

        media = None
        media_type = None

        # Randomly decide if the post contains an image or video
        if random.choice([True, False]):
            # Use Lorem Picsum for random image
            media = f"https://picsum.photos/seed/{random.randint(1, 1000)}/300"
            media_type = "image"
        else:
            # Use Pexels API for random video (replace with your own API key)
            api_key = "YOUR_PEXELS_API_KEY"  # Get this from Pexels API website
            headers = {"Authorization": api_key}
            video_data = requests.get("https://api.pexels.com/videos/popular?per_page=1", headers=headers).json()
            video_url = video_data['videos'][0]['video_files'][0]['link']
            media = video_url
            media_type = "video"

        posts.append({
            "username": user,
            "text": post_text,
            "media": media,
            "media_type": media_type
        })

    return posts
