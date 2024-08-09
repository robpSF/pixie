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
    search_term = image_id  # Use the image ID for naming
else:
    query = st.text_input("Enter search query (e.g., 'nature', 'cars'):", "")
    search_term = query.replace(' ', '_')  # Use the query for naming
    
image_type = st.selectbox("Select image type:", ["all", "photo", "illustration", "vector"], index=1)
category = st.selectbox("Select category:", ["all", "fashion", "nature", "backgrounds", "science", "education", 
                                             "people", "feelings", "religion", "health", "places", 
                                             "animals", "industry", "food", "computer", "sports", 
                                             "transportation", "travel", "buildings", "business", "music"], index=0)

# Cropping options
crop_option = st.radio(
    "Choose cropping option:",
    ("Save cropped version for profile pics", "Crop to custom aspect ratio", "No cropping")
)

if crop_option == "Crop to custom aspect ratio":
    aspect_ratio = st.radio("Select aspect ratio:", ("16:9", "1:1"))
else:
    aspect_ratio = None

grab_center = st.checkbox("Grab center of image?", True)
PER_PAGE = st.slider("Number of images per page:", 3, 200, 6)  # Valid range 3-200
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
    
    # Check if the request was successful
    if req.status_code == 200:
        try:
            data = req.json()
        except requests.exceptions.JSONDecodeError:
            st.error("Error parsing the response as JSON. The API might be down or returning unexpected content.")
            st.write("Response content:", req.text)
            break
        
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
    else:
        st.error(f"Request failed with status code {req.status_code}.")
        st.write("Response content:", req.text)
        break

if url_links:
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for index, image_url in enumerate(url_links):
            r = requests.get(image_url, allow_redirects=False)
            image_data = r.content
            
            extension = image_url[-4:]
            img = Image.open(BytesIO(image_data))
            
            # Cropping logic
            if crop_option == "Save cropped version for profile pics":
                if grab_center:
                    width, height = img.size
                    x = (width / 2) - 125
                    y = (height / 2) - 125
                else:
                    x = 0
                    y = 0
                box = (x, y, x + 250, y + 250)
                crop = img.crop(box)
                file_name = f"{search_term}_{index+1}_cropped{extension}"
                st.image(crop, caption=f"Cropped Image {index+1}")

            elif crop_option == "Crop to custom aspect ratio":
                width, height = img.size
                if aspect_ratio == "16:9":
                    target_width = width
                    target_height = int(width * 9 / 16)
                else:  # "1:1"
                    target_width = target_height = min(width, height)
                
                if grab_center:
                    x = (width - target_width) / 2
                    y = (height - target_height) / 2
                else:
                    x = 0
                    y = 0
                
                box = (x, y, x + target_width, y + target_height)
                crop = img.crop(box)
                file_name = f"{search_term}_{index+1}_{aspect_ratio.replace(':', '_')}{extension}"
                st.image(crop, caption=f"{aspect_ratio} Cropped Image {index+1}")
                
                # Only save the cropped image
                crop_buffer = BytesIO()
                crop.save(crop_buffer, format=img.format)
                zf.writestr(file_name, crop_buffer.getvalue())
                continue  # Skip saving the original or other versions

            else:
                # Save the original image if no cropping is selected
                file_name = f"{search_term}_{index+1}{extension}"
                st.image(img, caption=f"Original Image {index+1}")

            img_buffer = BytesIO()
            img.save(img_buffer, format=img.format)
            
            # Save the image (either cropped or original) in the zip file
            zf.writestr(file_name, img_buffer.getvalue())

    # Provide the download link for the zip file
    zip_buffer.seek(0)
    zip_file_name = f"{search_term}_images.zip"
    st.download_button("Download All Images as Zip", zip_buffer, zip_file_name, "application/zip")

    st.success("Download and processing complete!")
else:
    st.warning("No images found.")
