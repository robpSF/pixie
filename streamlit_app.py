import requests
import time
from PIL import Image
import streamlit as st
from io import BytesIO
import zipfile

# Access API key from Streamlit secrets
API_KEY = st.secrets["pixabay_api_key"]
URL_ENDPOINT = "https://pixabay.com/api/"

# Streamlit input widgets
st.title("Pixabay Image Downloader")

# Toggle between searching by image ID or query
mode = st.radio("Choose mode:", ("Search by Image ID", "Search by Query"))

if mode == "Search by Image ID":
    image_id = st.text_input("Enter image ID:", "2575608")
else:
    query = st.text_input("Enter search query (e.g., 'nature', 'cars'):", "")
    
image_type = st.selectbox("Select image type:", ["all", "photo", "illustration", "vector"], index=1)
category = st.selectbox("Select category:", ["all", "fashion", "nature", "backgrounds", "science", "education", 
                                             "people", "feelings", "religion", "health", "places", 
                                             "animals", "industry", "food", "computer", "sports", 
                                             "transportation", "travel", "buildings", "business", "music"], index=0)
save_cropped_version = st.checkbox("Save cropped version for profile pics?", True)
grab_center = st.checkbox("Grab center of image?", True)
PER_PAGE = st.slider("Number of images per page:", 1, 20, 6)
NUM_PAGES = st.slider("Number of pages to retrieve:", 1, 10, 3)

# Initialize parameters based on mode
if mode == "Search by Image ID":
    PARAMS = {
        'key': API_KEY,
        'id': image_id
    }
else:
    PARAMS = {
        'key': API_KEY,
        'q': query,
        'image_type': image_type,
        'category': category if category != "all" else None,
        'per_page': PER_PAGE,
        'page': 1
    }

url_links = []

# Fetch images from Pixabay
for page in range(1, NUM_PAGES + 1):
    PARAMS['page'] = page
    req = requests.get(URL_ENDPOINT, params=PARAMS)
    data = req.json()

    if 'hits' in data and data['hits']:
        for image in data["hits"]:
            url_links.append(image["largeImageURL"])
            st.write(image["largeImageURL"])
    else:
        if mode == "Search by Image ID":
            st.warning(f"No image found for ID '{image_id}'.")
        else:
            st.warning(f"No images found for query '{query}' on page {page}.")
        break

if url_links:
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for index, image_url in enumerate(url_links):
            r = requests.get(image_url, allow_redirects=False)
            image_data = r.content
            
            extension = image_url[-4:]
            file_name = f"image_{index+1}{extension}"
            
            img = Image.open(BytesIO(image_data))
            st.image(img, caption=f"Downloaded Image {index+1}")
            
            img_buffer = BytesIO()
            img.save(img_buffer, format=img.format)
            
            # Save the original image in the zip file
            zf.writestr(file_name, img_buffer.getvalue())
            
            # If crop is true then fit to 250 x 250 for profile image
            if save_cropped_version:
                if grab_center:
                    width, height = img.size
                    x = (width / 2) - 125
                    y = (height / 2) - 125
                else:
                    x = 0
                    y = 0
                box = (x, y, x + 250, y + 250)
                crop = img.crop(box)
                crop_file_name = f"image_{index+1}_cropped{extension}"
                
                crop_buffer = BytesIO()
                crop.save(crop_buffer, format=img.format)
                zf.writestr(crop_file_name, crop_buffer.getvalue())
                st.image(crop, caption=f"Cropped Image {index+1}")

            # Twitter BG
            if save_cropped_version:
                if grab_center:
                    x = 0  # (width/2)-125  Don't adjust X for Twitter banner
                    y = (img.height / 2) - 105
                else:
                    x = 0
                    y = 0
                if img.width > 630 and img.height > 210:
                    box = (x, y, x + 630, y + 210)
                    crop = img.crop(box)
                    twitter_bg_file_name = f"image_{index+1}_twitter_bg{extension}"
                    
                    crop_buffer = BytesIO()
                    crop.save(crop_buffer, format=img.format)
                    zf.writestr(twitter_bg_file_name, crop_buffer.getvalue())
                    st.image(crop, caption=f"Twitter Background Image {index+1}")
    
    # Provide the download link for the zip file
    zip_buffer.seek(0)
    zip_file_name = f"{image_id}_images.zip" if mode == "Search by Image ID" else f"{query.replace(' ', '_')}_images.zip"
    st.download_button("Download All Images as Zip", zip_buffer, zip_file_name, "application/zip")

    st.success("Download and processing complete!")
else:
    st.warning("No images found.")
