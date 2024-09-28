import streamlit as st
from auth import register_user, login_user, init_db
from profile_manager import create_profile, get_profile, update_profile
from PIL import Image
import os
from io import BytesIO
import datetime

# Initialize the database
init_db()

# Define the number of columns per row for posts
NUM_COLUMNS = 3

# Dark Theme using custom CSS
def load_css():
    with open("static/dark_theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Function to save uploaded media (image or video) to the server
def save_media(uploaded_file, username):
    media_folder = f"media/{username}"
    if not os.path.exists(media_folder):
        os.makedirs(media_folder)  # Create a directory for the user's media if it doesn't exist

    file_path = os.path.join(media_folder, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())  # Save the uploaded file

    return file_path  # Return the path where the file is saved

# Function to handle user posts (image/video with caption)
def get_user_posts(username):
    user_posts = []
    media_folder = f"media/{username}"
    
    if os.path.exists(media_folder):
        for file in os.listdir(media_folder):
            file_path = os.path.join(media_folder, file)
            if file.endswith(('jpg', 'png', 'mp4')):
                user_posts.append(file_path)

    return user_posts

# Function to download the media file with an icon next to the button
def download_icon_button(file_path):
    with open(file_path, "rb") as file:
        file_data = file.read()
        
        # Use Streamlit's download button without an icon
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            # Display an emoji or an image as an icon next to the button
            st.markdown("📥")  # This is an emoji, you can replace it with an icon image if desired
            
        with col2:
            st.download_button(
                label="Download",
                data=file_data,
                file_name=os.path.basename(file_path),
                mime="application/octet-stream",
                key=file_path  # Ensure unique key for each button
            )

# Updated encoding function
def encode(img_path: str, data: str, new_img_name: str) -> None:
    if not data:
        raise ValueError("Data is empty")
    image = Image.open(img_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    encoded_image = embed_data(image, data)
    encoded_image.save(new_img_name, format='PNG')

# Updated decoding function
def decode(img_path: str) -> str:
    image = Image.open(img_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    width, height = image.size
    binary_data = ""
    for y in range(height):
        for x in range(width):
            pixel = list(image.getpixel((x, y)))
            for color in pixel:
                binary_data += str(color & 1)
            if len(binary_data) >= 8 and binary_data[-8:] == '00000000':
                break
        if len(binary_data) >= 8 and binary_data[-8:] == '00000000':
            break
    decoded_data = ""
    for i in range(0, len(binary_data) - 8, 8):
        byte = binary_data[i:i+8]
        decoded_data += chr(int(byte, 2))
    return decoded_data.rstrip('\x00')

# Updated helper function for embedding data
def embed_data(image: Image.Image, data: str) -> Image.Image:
    width, height = image.size
    binary_data = ''.join(format(ord(char), '08b') for char in data) + '00000000'
    data_index = 0
    encoded_image = image.copy()
    
    for y in range(height):
        for x in range(width):
            pixel = list(encoded_image.getpixel((x, y)))
            for color_channel in range(3):
                if data_index < len(binary_data):
                    pixel[color_channel] = (pixel[color_channel] & ~1) | int(binary_data[data_index])
                    data_index += 1
            encoded_image.putpixel((x, y), tuple(pixel))
            if data_index >= len(binary_data):
                return encoded_image
    return encoded_image

def main():
    load_css()

    st.title("HIDE - Social Media App")

    # Session State Initialization for tracking user login status
    if 'username' not in st.session_state:
        st.session_state.username = None
        st.session_state.page = "Login"  # Default page set to Login

    # Page access control: Only show Home and Profile if logged in
    if st.session_state.username:
        menu = ["Home", "Profile", "Logout"]
    else:
        menu = ["Login", "Register"]

    # Sidebar navigation
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login to your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # Authenticate user
            if login_user(username, password):
                st.session_state.username = username  # Store the username in session
                st.session_state.page = "Home"  # Redirect to Home on successful login
                st.success(f"Welcome, {username}!")
            else:
                st.error("Account not found. Please register or try again.")

    elif choice == "Register":
        st.subheader("Create New Account")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            # Create a new account
            register_user(new_username, new_password)
            # Pass default empty values for name, bio, and profile pic
            create_profile(new_username, name="", bio="", profile_pic="")
            st.session_state.username = new_username  # Automatically log in after registration
            st.session_state.page = "Home"  # Redirect to Home after successful registration
            st.success("Account Created and Profile Initialized!")

    elif choice == "Home" and st.session_state.username:
        st.subheader(f"Welcome to HIDE, {st.session_state.username}!")

        # Section for multimedia upload (user's own post)
        uploaded_file = st.file_uploader("Upload Photo or Video", type=["jpg", "png", "mp4"])
        caption = None  # Initialize caption variable

        # Check if the user uploaded a file
        if uploaded_file is not None:
            file_path = save_media(uploaded_file, st.session_state.username)
            st.success(f"Uploaded {uploaded_file.name} to {file_path}")

            # Input for caption
            caption = st.text_input("Write a caption for your post")

            # Display the "Post" button only if there is a caption
            if caption:
                if st.button("Post"):
                    # Generate secret data
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    secret_data = f"Copyright_{st.session_state.username}_{current_time}"
                    
                    # Encode the secret data into the image
                    encoded_file_path = f"media/{st.session_state.username}/encoded_{uploaded_file.name}"
                    encode(file_path, secret_data, encoded_file_path)
                    
                    st.success("Post uploaded successfully with hidden data!")
                    st.experimental_rerun()  # Reload or redirect to the Home page after posting

        # Display user's own posts
        st.subheader("Your Posts")
        user_posts = get_user_posts(st.session_state.username)

        if len(user_posts) == 0:
            st.write("Yet to post.")
        else:
            # Iterate through the user's posts and display them in a grid
            for i in range(0, len(user_posts), NUM_COLUMNS):
                cols = st.columns(NUM_COLUMNS)  # Create columns dynamically

                for idx, col in enumerate(cols):
                    if i + idx < len(user_posts):  # Ensure we're not going out of bounds
                        post = user_posts[i + idx]
                        
                        # Display image or video
                        if post.endswith(('jpg', 'png')):
                            col.image(post, width=200)
                        elif post.endswith('mp4'):
                            col.video(post)

                        # Display the download button below the post
                        col.write("")  # Empty line to separate
                        col.download_button(
                            label="Download",
                            data=open(post, "rb").read(),
                            file_name=os.path.basename(post),
                            mime="application/octet-stream"
                        )
                        
                        # Add a button to reveal hidden data
                        if col.button(f"Reveal Hidden Data", key=f"reveal_{i+idx}"):
                            try:
                                hidden_data = decode(post)
                                if hidden_data:
                                    st.info(f"Hidden data in this post: {hidden_data}")
                                else:
                                    st.warning("No hidden data found in this image.")
                            except Exception as e:
                                st.error(f"Error decoding data: {str(e)}")

    elif choice == "Profile" and st.session_state.username:
        # Display and allow updates to the user's profile
        st.subheader(f"{st.session_state.username}'s Profile")
        username = st.session_state.username
        profile = get_profile(username)

        # Display current profile info
        if profile:
            st.write(f"Name: {profile[1]}")
            st.write(f"Bio: {profile[2]}")
            if profile[3]:  # Check if profile pic exists
                st.image(f"media/{username}/profile_pic.png", width=100)

        # Update profile information
        name = st.text_input("Update Name", value=profile[1] if profile else "")
        bio = st.text_area("Update Bio", value=profile[2] if profile else "")
        profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])

        if st.button("Update Profile"):
            if profile_pic:
                img = Image.open(profile_pic)
                img.save(f"media/{username}/profile_pic.png")
            update_profile(username, name, bio, f"media/{username}/profile_pic.png")
            st.success("Profile Updated Successfully!")

    elif choice == "Logout":
        # Handle logout by clearing session state
        st.session_state.username = None
        st.session_state.page = "Login"
        st.success("You have been logged out.")

    # Redirect to login if trying to access restricted pages
    if not st.session_state.username and st.session_state.page in ["Home", "Profile"]:
        st.warning("Please log in or register to access the Home or Profile page.")
        st.session_state.page = "Login"

if __name__ == '__main__':
    main()