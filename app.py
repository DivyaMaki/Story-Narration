import os
import streamlit as st
from gtts import gTTS
from moviepy.editor import ImageSequenceClip, AudioFileClip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time
import cohere  # Import the cohere package
from PIL import Image

# Suppress only the single InsecureRequestWarning from urllib3 needed for this example
warnings.simplefilter('ignore', InsecureRequestWarning)

# Initialize Cohere client
cohere_api_key = "YOUR API KEY"
cohere_client = cohere.Client(cohere_api_key)

# Function to generate a story using Cohere
def generate_story(prompt):
    response = cohere_client.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=300
    )
    story = response.generations[0].text.strip()
    return story

# Function to generate prompts from the story
def generate_prompts(story, character_details):
    prompts = story.split('. ')
    detailed_prompts = []
    for prompt in prompts:
        if prompt.strip():
            detailed_prompt = f"{character_details}. {prompt.strip()}."
            detailed_prompts.append(detailed_prompt)
    return detailed_prompts

# Function to generate images for each prompt
def generate_images(prompts, save_directory):
    images = []
    service = Service(r"C:\Users\User\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://aicreate.com/text-to-image-generator/")

    for i, prompt in enumerate(prompts):
        image_generated = False
        while not image_generated:
            try:
                # Enter the prompt
                prompt_input = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.NAME, "caption"))
                )
                prompt_input.clear()
                prompt_input.send_keys(prompt)

                # Enhance the prompt
                enhance_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "enhance-prompt"))
                )
                enhance_button.click()

                # Make the image photo-realistic
                photo_realistic_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "make-photo-realistic"))
                )
                photo_realistic_button.click()

                # Wait for the loading overlay to disappear
                WebDriverWait(driver, 30).until(
                    EC.invisibility_of_element((By.ID, "loading-overlay"))
                )

                # Select the model version
                model_select = driver.find_element(By.NAME, "model_version")
                model_select.find_element(By.XPATH, "//option[@value='flux']").click()

                # Select the image size
                size_select = driver.find_element(By.NAME, "size")
                size_select.find_element(By.XPATH, "//option[@value='1024x1024']").click()

                # Click the Generate Images button using JavaScript to bypass overlay
                generate_button = driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Generate Images')]")
                driver.execute_script("arguments[0].click();", generate_button)

                # Wait for the image to be generated and locate the download button
                WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "download-image"))
                )

                # Find the image URL and download button
                image_element = driver.find_element(By.CSS_SELECTOR, "div.image-wrapper img")
                image_url = image_element.get_attribute("src")

                # Click the download button to download the image
                download_button = driver.find_element(By.CLASS_NAME, "download-image")
                driver.execute_script("arguments[0].click();", download_button)

                # Download the image directly from the URL
                image_path = os.path.join(save_directory, f"generated_image_{i+1}.jpg")
                image_data = requests.get(image_url, verify=False).content
                with open(image_path, "wb") as handler:
                    handler.write(image_data)

                images.append(image_path)
                image_generated = True
                print(f"Image {i+1} downloaded successfully! Saved at {image_path}")
            except Exception as e:
                print(f"Error generating image for prompt {i+1}: {e}. Retrying...")
                time.sleep(5)  # Wait before retrying to avoid overwhelming the server

    driver.quit()
    return images

# Function to generate audio from the story
def generate_audio(story_text, audio_path):
    tts = gTTS(story_text, lang='en')
    tts.save(audio_path)
    print(f"Audio generated successfully! Saved at {audio_path}")

# Function to create a video from images and audio
def create_video(images, audio_path, video_path):
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration

    # Ensure at least 6 images are used
    num_images = max(6, len(images))
    if len(images) < num_images:
        print(f"Warning: Less than {num_images} images found. Using {len(images)} images.")

    duration_per_image = audio_duration / num_images

    # Pad the images list with the last image if there are fewer images than needed
    images += [images[-1]] * (num_images - len(images))

    clip = ImageSequenceClip(images, durations=[duration_per_image] * num_images)
    final_clip = clip.set_audio(audio)
    final_clip.write_videofile(video_path, codec="libx264", fps=24)
    print(f"Video created successfully! Saved at {video_path}")

def create_animated_gif(images, gif_path, duration=500):
    """
    Create an animated GIF from a list of image file paths.

    Parameters:
    - images: List of paths to image files.
    - gif_path: Path where the GIF will be saved.
    - duration: Duration of each frame in milliseconds (default is 500ms).
    """
    # Open images and ensure they are in 'RGB' mode
    image_list = [Image.open(img).convert('RGB') for img in images]
    
    # Save the images as an animated GIF
    image_list[0].save(
        gif_path,
        save_all=True,
        append_images=image_list[1:],
        optimize=False,
        duration=duration,
        loop=0  # Loop forever
    )
    print(f"Animated GIF created successfully! Saved at {gif_path}")

# Streamlit UI
st.title("TEXT TO STORY NARRATION")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page == 'home':
    st.header("STORY GENERATOR \n BRING YOUR IMAGINATIONS TRUE!")
    st.write("Click the button below to start using the Generator")
    if st.button("Start"):
        st.session_state.page = 'input'

elif st.session_state.page == 'input':
    st.header("Generate Story and Media")
    prompt_text = st.text_area("Enter a prompt for the story")
    if st.button("Generate Story and Video"):
        story = generate_story(prompt_text)
        st.write("Generated Story:")
        st.write(story)

        save_directory = "./generated_media"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Generate images and save them as an animated GIF
        character_details = "Include details from the story for personalization"
        prompts = generate_prompts(story, character_details)
        images = generate_images(prompts, save_directory)
        gif_path = os.path.join(save_directory, "story_animation.gif")
        create_animated_gif(images, gif_path)
        
        # Generate audio and video
        audio_path = os.path.join(save_directory, "story_audio.mp3")
        video_path = os.path.join(save_directory, "story_video.mp4")
        generate_audio(story, audio_path)
        create_video(images, audio_path, video_path)
        
        # Display the GIF and Video in Streamlit
        st.write("Animated GIF:")
        st.image(gif_path)
        st.write("Video:")
        st.video(video_path)
