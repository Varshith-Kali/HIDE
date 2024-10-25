import os
import streamlit as st
from auth import register_user, login_user, init_db
from profile_manager import create_profile, get_profile, update_profile
from PIL import Image
import glob
from io import BytesIO
import datetime
from lsb import encode, decode

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


def get_all_user_posts():
    all_posts = []
    media_root = "media"

    # Check if media folder exists
    if os.path.exists(media_root):
        # Iterate over each user folder
        for user_folder in os.listdir(media_root):
            user_path = os.path.join(media_root, user_folder)

            if os.path.isdir(user_path):
                # Collect all image and video files for each user
                for file in os.listdir(user_path):
                    if file.endswith(('jpg', 'png', 'mp4')):
                        file_path = os.path.join(user_path, file)
                        # Append file path, creation time, and username (folder name)
                        all_posts.append((file_path, os.path.getctime(file_path), user_folder))

    # Sort posts by creation time, descending
    if all_posts:
        sorted_posts = sorted(all_posts, key=lambda x: x[1], reverse=True)
        return [(post[0], post[2]) for post in sorted_posts]  # Return file path and username
    else:
        return []  # Return empty list if no posts found



# Function to delete the selected post
def delete_post(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)  # Remove the file from the server
        return True
    return False

# Main application function
def main():
    load_css()

    st.title("HIDE - Social Media App")

    # Session State Initialization for tracking user login status
    if 'username' not in st.session_state:
        st.session_state.username = None
        st.session_state.page = "Login"  # Default page set to Login

    # Page access control: Only show Home, Profile, and Check Copyright if logged in
    if st.session_state.username:
        menu = ["Home", "Profile", "Post", "Check Copyright", "Logout"]
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
                st.rerun()  # Force the page to rerun and redirect to "Home"
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
        st.subheader("Feed - Latest Posts from All Users")

        # Fetch all user posts and display in descending order by time
        all_posts = get_all_user_posts()

        if len(all_posts) == 0:
            st.write("No posts available.")
        else:
            # Display posts in a grid
            for i in range(0, len(all_posts), NUM_COLUMNS):
                cols = st.columns(NUM_COLUMNS)

                for idx, col in enumerate(cols):
                    if i + idx < len(all_posts):
                        post, username = all_posts[i + idx]

                        # Display the image or video
                        if post.endswith(('jpg', 'png')):
                            col.image(post, width=200)
                        elif post.endswith('mp4'):
                            col.video(post)

                        # Add "Posted by {username}" text below the post
                        col.markdown(f'Posted by <span style="color:red;">{username}</span>', unsafe_allow_html=True)
                        
                        cred_user = decode(post).split("_")[1]

                        if cred_user != username:
                            col.markdown(f'Cred: <span style="color:red;">{cred_user}</span>', unsafe_allow_html=True)

                        # Optionally, add a download button
                        col.download_button(
                            label="Download",
                            data=open(post, "rb").read(),
                            file_name=os.path.basename(post),
                            mime="application/octet-stream"
                        )

    elif choice == "Post" and st.session_state.username:
        st.subheader(f"Post your Moments...")

        # Section for multimedia upload (user's own post)
        uploaded_file = st.file_uploader("Upload Photo or Video", type=["jpg", "png", "mp4"])
        caption = None  # Initialize caption variable

        # Only proceed if the user has uploaded a file
        if uploaded_file is not None:
            caption = st.text_input("Write a caption for your post")

            # Display the "Post" button only if there is a caption
            if caption:
                if st.button("Post"):
                    # Save media and process only when Post is clicked
                    file_path = save_media(uploaded_file, st.session_state.username)
                    # st.session_state.uploaded_file = None
                    # st.rerun() 
                    
                    # Check if the uploaded image already contains hidden data
                    try:
                        hidden_data = decode(file_path)
                        if hidden_data[:10] == "Copyright_":
                            # st.error(f"Cannot post! This file already contains hidden data: {hidden_data}")

                            original_username = hidden_data.split("_")[1]
                            st.info(f"This post belongs to {original_username}.")
                            # encoded_file_path = f"media/{st.session_state.username}/encoded_{uploaded_file.name}"
                            # if os.path.exists(file_path):
                            #     os.rename(file_path, encoded_file_path) 
                                
                        else:
                            # If no hidden data is found, proceed with encoding
                            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            secret_data = f"Copyright_{st.session_state.username}_{current_time}"

                            # Encode the secret data into the image
                            encoded_file_path = f"media/{st.session_state.username}/encoded_{uploaded_file.name}"
                            encode(file_path, secret_data, encoded_file_path)
                            delete_post(f"media/{st.session_state.username}/{uploaded_file.name}")  # Delete the original file after encoding

                            st.success(f"Uploaded {uploaded_file.name} to {encoded_file_path}")
                            st.success("Post uploaded successfully with hidden data!")
                            st.rerun()  # Reload or redirect to the Home page after posting
                    except Exception as e:  
                        st.error(f"Error while checking for hidden data: {str(e)}")


        # Display user's own posts after a successful post
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

                        # Add delete button for each post
                        if col.button(f"Delete Post", key=f"delete_{i+idx}"):
                            if delete_post(post):
                                st.success(f"Post {os.path.basename(post)} deleted successfully.")
                                st.rerun()  # Reload page to reflect the deleted post
                            else:
                                st.error(f"Failed to delete post {os.path.basename(post)}.")


    

    elif choice == "Profile" and st.session_state.username:
        st.subheader(f"Your Profile, {st.session_state.username}")

        # Display the user's profile information
        profile = get_profile(st.session_state.username)

        if profile:
            name = profile[1] if profile and profile[1] else st.session_state.username  # Username as the default name
            bio = profile[2] if profile and profile[2] else "Tell the world about yourself!"  # Default bio message

            st.write(f"**Name**: {name}")  # Show the name or username
            st.write(f"**Bio**: {bio}")  # Show the bio or default message

            if profile[3]:  # Check if profile pic exists
                st.image(f"media/{st.session_state.username}/profile_pic.png", width=100)

        # Update profile information
        name = st.text_input("Update Name", value=profile[1] if profile and profile[1] else "Your Name")
        bio = st.text_area("Update Bio", value=profile[2] if profile and profile[2] else "Write a brief bio...")
        profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])

        if st.button("Update Profile"):
            if profile_pic:
                img = Image.open(profile_pic)
                img.save(f"media/{st.session_state.username}/profile_pic.png")
            update_profile(st.session_state.username, name, bio, f"media/{st.session_state.username}/profile_pic.png")
            st.success("Profile Updated Successfully!")


    elif choice == "Check Copyright":
        st.subheader("Check for Copyright Data")
        
        # Allow user to upload an image to check
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
        
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.image(img, caption="Uploaded Image", width=300)
            
            # Decode and check for hidden data
            if st.button("Check for Hidden Data"):
                try:
                    hidden_data = decode(uploaded_file)
                    if hidden_data:
                        st.success(f"Hidden data found: {hidden_data}")
                    else:
                        st.warning("No hidden data found.")
                except Exception as e:
                    st.error(f"Error decoding image: {str(e)}")

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
