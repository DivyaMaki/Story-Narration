Text to Story Narration

Overview

The Text to Story Narration application is a Streamlit-based tool that transforms a user-provided text prompt into a narrated story with accompanying visuals. This application leverages Cohere's AI capabilities to generate stories, Google's gTTS for voice narration, and MoviePy for video creation. Additionally, it uses Selenium to automate the image generation process through an online text-to-image generator, and the final output is presented as both an animated GIF and a video.

Features

● Story Generation: Utilizes Cohere's NLP model to create a narrative based on user input.

● Image Generation: Automates image creation using Selenium and an online generator based on the story content.

● Audio Narration: Converts the generated story into an audio file using gTTS.

● Video Creation: Compiles images and narration into a video file using MoviePy.

● Animated GIF: Creates an animated GIF from the generated images.

Requirements

Before running the project, ensure you have the following installed:

1.Python 3.x

2.Streamlit

3.gTTS

4.MoviePy

5.Selenium

6.Cohere Python SDK

7.PIL (Pillow)

Requests

● You can install the required packages using pip:

|pip install streamlit gtts moviepy selenium cohere pillow requests|

Additionally, you'll need:

● Cohere API Key: Sign up at Cohere to get an API key.

● Chrome WebDriver: Download the Chrome WebDriver that matches your Chrome browser version from here.

Setup

Set Up Chrome WebDriver:

● Download the Chrome WebDriver and place it in an accessible directory.

● Update the Service path in the code to point to your WebDriver location.

Configure Cohere:

● Replace cohere_api_key in the script with your actual Cohere API key.

Run the Application:

● Navigate to the project directory.

Run the Streamlit application using the following command:

|streamlit run app.py|

Access the Application:

● Once the server is running, you'll be able to access the application in your web browser.

Notes

● The image generation process uses Selenium to interact with a third-party online service. 

● Ensure that your WebDriver is compatible with your browser version.

● The GIF and video creation are designed to work even with a limited number of images; however, a minimum of 6 images is recommended for optimal results.

Troubleshooting

● If the WebDriver fails to load or interact with the page, verify the path to your WebDriver and check that it matches your Chrome version.

● In case of repeated failures during image generation, check the connection and consider increasing the timeout in the script.
