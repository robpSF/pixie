import requests
import time
from PIL import Image
import streamlit as st
from io import BytesIO
import zipfile

API_KEY = "3939164-25537e67461883e93bbf859c4"
URL_ENDPOINT = "https://pixabay.com/api/"

# Streamlit input widgets
st.title("Pixabay Image Downloader")

id = st.text_input("Enter image id:", "2575608")
image_type = st.selectbox("Select image type:", ["all", "photo", "illustration", "vector"], index=1)
category = st.selectbox("Select category:", ["fashion", "nature", "backgrounds", "science", "education", 
                                             "people", "feelings", "religion", "health", "places", 
                                             "animals", "industry", "food", "computer", "sports", 
                                             "transportation", "travel", "buildings", "business", "music"], index=5)
save_cropped_version = st.checkbox("Save cropped version for profile pics?", True)
grab_center = st.checkbox("Grab center of image?", True)
PER_PAGE = st.slider("Number of images per page:", 1, 20, 6)
NUM_PAGES = st.slider("Number of pages to retrieve:", 1, 10, 3)

PARAMS = {'id': id}
ENDPOINT = URL_ENDPOINT + "?key=" + API_KEY

url_links = []

req = requests.get(url=ENDPOINT, params=PARAMS)
data = req.json()

for image in data["hits"]:
    url_links.append(image["webformatURL"])
    st.write(image["webformatURL"])

for page in range(2, NUM_PAGES):
    time.sleep(3)
    PARAMS['page'] = page
    st.write(f"Processing page {page}...")
    req = requests.get(url=ENDPOINT, params=PARAMS)
    data = req.json()
    for image in data["hits"]:
        url_links.append(image["largeImageURL"])

st.write(url_links)

if url_links:
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for index, image_url in enumerate(url_links):
            r = requests.get(image_url, allow_redirects=False)
            image_data = r.content
            
            extension = image_url[-4:]
            file_name = f"{id}_{index+1}{extension}"
            
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
                crop_file_name = f"{id}_{index+1}_cropped{extension}"
                
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
                    twitter_bg_file_name = f"{id}_{index+1}_twitter_bg{extension}"
                    
                    crop_buffer = BytesIO()
                    crop.save(crop_buffer, format=img.format)
                    zf.writestr(twitter_bg_file_name, crop_buffer.getvalue())
                    st.image(crop, caption=f"Twitter Background Image {index+1}")
    
    # Provide the download link for the zip file
    zip_buffer.seek(0)
    st.download_button("Download All Images as Zip", zip_buffer, f"{id}_images.zip", "application/zip")

    st.success("Download and processing complete!")
else:
    st.warning("No images found for the given ID.")
