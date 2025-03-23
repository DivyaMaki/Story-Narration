# Story Generator Application

Overview:
	This project uses multiple AI models to generate a multimedia story based on a user input prompt. 
	It integrates models for text generation (via Cohere), image generation (via Stable Diffusion), audio generation (via Google TTS), and video creation (via MoviePy). 
	The output includes a text-based story, images, an audio narration, and a video combining all the elements.
 
Features:

 ```
	Story Generation: Given a prompt, the application generates a short story using Cohere’s language model.

	Image Generation: For each segment of the story, it generates images using the Stable Diffusion model.

	Audio Generation: Converts the generated story into an audio file using Google's Text-to-Speech (gTTS) API.

	Video Creation: Combines the generated images and audio into a video using MoviePy, producing a final video file.
```

Requirements:

To run the application, you need to install the following dependencies:

```
	Python 3.8+

	Gradio: For creating the web-based interface.

	Cohere: For natural language processing and story generation.

	gTTS (Google Text-to-Speech): For generating audio from text.

	MoviePy: For creating videos by combining images and audio.

	Transformers: For loading the GPT-2 model to process text.

	Diffusers: For using the Stable Diffusion model to generate images.

	PIL (Pillow): For handling image processing.
```

Install Dependencies:

```
	pip install gradio gtts moviepy transformers diffusers torch cohere Pillow
```

Download Pretrained Models:

Before running the script, ensure that the following models are downloaded:

```
	GPT-2 model: Used for story generation.

	Stable Diffusion model: Used for generating images from the story segments.
```
 
API Keys:

For this application to work, you will need a valid API key from Cohere. You can obtain an API key by signing up at Cohere.

Once you have the API key, replace the placeholder in the code with your actual API key:

```
 	api_key = 'YOUR_COHERE_API_KEY'
```

Application Overview:

  1. Story Generation
     
	  The story generation is powered by the Cohere API. Given a prompt, the app will generate a story, which is divided into segments (max 100 characters per segment). This ensures that the story is broken into     digestible parts for subsequent image generation.

  2. Image Generation
     
	  For each story segment, the app sends the segment text to the Stable Diffusion model, which generates an anime-style image related to the content of the segment. The image is then saved and used in the video.

  3. Audio Generation
     
	  The generated story text is then converted to speech using gTTS (Google Text-to-Speech). The speech is saved as an audio file (MP3 format).

  4. Video Creation
     
	  The generated images are then assembled into a video. The video uses MoviePy to synchronize the images with the audio, ensuring that each image is shown for the correct amount of time based on the length of   the audio. The final video is saved as an MP4 file.

  5. Gradio Interface
      
	  A simple Gradio interface is used to take the user's input (a prompt) and provide the following outputs:

	  - Generated Story (Text)

	  - First Image (Image)

	  - Generated Audio (MP3 File)

	  - Generated Video (MP4 File)

Input

  The user provides an input prompt (a sentence) which serves as the starting point for generating a story.

Outputs

  The app will return the following:

- Generated Story: The AI-generated short story in text format.

- Generated Image: The first image corresponding to the first segment of the story.

- Generated Audio: An MP3 file of the audio narration of the story.

- Generated Video: An MP4 file of the video combining the images and audio.

How to Run the Application

1. Clone or Download the Repository

	Clone or download the repository containing the code.

2. Set Up API Key
   
	Ensure that you have the required API key from Cohere and update the following line in the script with your API key:
	api_key = 'YOUR_COHERE_API_KEY'

3. Install Dependencies
   
	Install the necessary dependencies as mentioned above.

4. Run the Application
   
	To start the application, simply run the Python script:
	python app.py
6. Using the Gradio Interface
Once the application is running, open a browser and navigate to the URL shown in the terminal (typically something like http://127.0.0.1:7860). There, you can enter a prompt, and the app will generate the story, images, audio, and video.
