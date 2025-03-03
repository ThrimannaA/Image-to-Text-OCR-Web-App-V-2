import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import time

st.set_page_config(layout="wide")  # Enables wide mode

# Initialize Google Drive Authentication
gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")  # Load saved credentials 

if gauth.credentials is None:
    gauth.LocalWebserverAuth()  # Authenticate manually
elif gauth.access_token_expired:
    gauth.Refresh()  
else:
    gauth.Authorize()  # Use existing credentials

gauth.SaveCredentialsFile("mycreds.txt")  # Save credentials
drive = GoogleDrive(gauth)

# Preprocess Image for OCR
def preprocess_image(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)  # Binarization
    return Image.fromarray(thresh)

# OCR Functions
def extract_text_tesseract(image):
    return pytesseract.image_to_string(image)

def upload_to_drive(text, ref_number, uploaded_file, errors, rating):
    """
    Uploads extracted text, errors, and rating along with the uploaded image 
    to a newly created folder named after the reference number in Google Drive.
    """

    # Define Google Drive Parent Folder ID
    parent_folder_id = '1SXT8l8R1i3LktVSxU5mosdU5TczIVT_F'  

    # Step 1: Check if the folder exists
    folder_query = f"title='{ref_number}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    folder_list = drive.ListFile({'q': folder_query}).GetList()

    if folder_list:
        folder_id = folder_list[0]['id']  # Use existing folder
    else:
        # Step 2: Create a new folder with the reference number
        folder_metadata = {
            'title': ref_number,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': parent_folder_id}]
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        folder_id = folder['id']

    # Step 3: Save Extracted Text as .txt and Upload
    text_file_path = f"{ref_number}_extracted_text.txt"
    with open(text_file_path, "w", encoding="utf-8") as file:
        file.write(text)

    text_file_drive = drive.CreateFile({'title': f"{ref_number}_extracted_text.txt", 'parents': [{'id': folder_id}]})
    text_file_drive.SetContentFile(text_file_path)
    text_file_drive.Upload()
    
    # Release the file before deleting
    text_file_drive = None  
    time.sleep(1)  # Ensure the file is not locked

    try:
        os.remove(text_file_path)  # Delete local file
    except PermissionError:
        print(f"Retrying deletion of {text_file_path}...")
        time.sleep(2)
        try:
            os.remove(text_file_path)
        except Exception as e:
            print(f"Final error deleting {text_file_path}: {e}")

    # Step 4: Save Errors as .txt and Upload
    error_file_path = f"{ref_number}_errors.txt"
    with open(error_file_path, "w", encoding="utf-8") as file:
        file.write(errors)

    error_file_drive = drive.CreateFile({'title': f"{ref_number}_errors.txt", 'parents': [{'id': folder_id}]})
    error_file_drive.SetContentFile(error_file_path)
    error_file_drive.Upload()

    error_file_drive = None  # Release the file before deleting
    time.sleep(1)

    try:
        os.remove(error_file_path)  # Delete local file
    except PermissionError:
        print(f"Retrying deletion of {error_file_path}...")
        time.sleep(2)
        try:
            os.remove(error_file_path)
        except Exception as e:
            print(f"Final error deleting {error_file_path}: {e}")

    # Step 5: Save and Upload the Uploaded Image
    image_file_path = f"{ref_number}.png"
    with open(image_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    image_file_drive = drive.CreateFile({'title': f"{ref_number}.png", 'parents': [{'id': folder_id}]})
    image_file_drive.SetContentFile(image_file_path)
    image_file_drive.Upload()

    image_file_drive = None  # Release the file before deleting
    time.sleep(1)

    try:
        os.remove(image_file_path)  # Delete local image file
    except PermissionError:
        print(f"Retrying deletion of {image_file_path}...")
        time.sleep(2)
        try:
            os.remove(image_file_path)
        except Exception as e:
            print(f"Final error deleting {image_file_path}: {e}")

    # Step 6: Save Rating as .txt and Upload
    rating_file_path = f"{ref_number}_rating.txt"
    with open(rating_file_path, "w", encoding="utf-8") as file:
        file.write(f"User Rating: {rating}/5")

    rating_file_drive = drive.CreateFile({'title': f"{ref_number}_rating.txt", 'parents': [{'id': folder_id}]})
    rating_file_drive.SetContentFile(rating_file_path)
    rating_file_drive.Upload()

    rating_file_drive = None  # Release the file before deleting
    time.sleep(1)

    try:
        os.remove(rating_file_path)  # Delete local file
    except PermissionError:
        print(f"Retrying deletion of {rating_file_path}...")
        time.sleep(2)
        try:
            os.remove(rating_file_path)
        except Exception as e:
            print(f"Final error deleting {rating_file_path}: {e}")

    return f"✅ Uploaded to Google Drive successfully!"
    #st.success("✅ Uploaded to Google Drive successfully!")
    time.sleep(2)
    st.experimental_rerun()

# Streamlit UI
st.markdown(
    "<h1 style='text-align: center;'>🔍 Let's Extract Text from Images - Instantly! </h1>",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("Upload an Image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    preprocessed_img = preprocess_image(img)
    extracted_text = extract_text_tesseract(preprocessed_img)  

    # Get image height 
    img_width, img_height = img.size
    text_area_height = min(img_height, 800)

    # Create two columns for layout
    col1, col2 = st.columns(2)

    with col1:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    with col2:
        st.text_area("Extracted Text", extracted_text, height=text_area_height)

    st.session_state["extracted_text"] = extracted_text

# New text input area for pasting errors
errors_text = st.text_area("Paste Any Errors Here", height=200)

# Small text input field for Reference Number
col1, col2 = st.columns([1, 3])  # Adjust the ratio to control width
with col1:
    ref_number = st.text_input("Enter Reference Number", max_chars=10)


# Rating Selection (1 to 5)
rating = st.radio("Rate the OCR Extraction (1-5)", options=[1, 2, 3, 4, 5], horizontal=True)

# Save & Upload to Google Drive
if ref_number and st.button("Save & Upload to Google Drive"):
    message = upload_to_drive(
        st.session_state["extracted_text"], ref_number, uploaded_file, errors_text, rating
    )
    st.success(message)

