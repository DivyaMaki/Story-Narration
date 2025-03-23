import gradio as gr
from gtts import gTTS
import moviepy
from moviepy.editor import ImageSequenceClip, AudioFileClip
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from diffusers import StableDiffusionPipeline
import torch
import cohere
import os
from PIL import Image

# Initialize models
model_name = "gpt2"
gpt2_model = GPT2LMHeadModel.from_pretrained(model_name)
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(model_name)

model_id = "CompVis/stable-diffusion-v1-4"
sd_pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
sd_pipe.to("cuda")

# Set your Cohere API key
api_key = 'YOUR-API-KEY'
co = cohere.Client(api_key)

def generate_story(prompt):
    try:
        response = co.generate(
            model='command-xlarge',  # Change model to a supported one
            prompt=f"Write a short story based on: {prompt}",
            max_tokens=500,
            temperature=0.9
        )
        story = response.generations[0].text.strip()
        return story
    except Exception as e:
        print(f"Error generating story: {e}")
        return f"Error generating story: {e}"
        
def generate_image(prompt, image_id):
    try:
        image = sd_pipe(prompt).images[0]
        image = image.convert("RGB")  # Ensure image is in RGB mode
        image_path = f"scene_{image_id}.png"
        image.save(image_path)
        print(f"Generated image saved at {image_path}")  # Debugging line
        return image_path
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def generate_audio(text, filename="output.mp3"):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        print(f"Generated audio saved at {filename}")  # Debugging line
        return filename
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def split_story(story, max_length=100):
    words = story.split()
    segments = []
    current_segment = []

    for word in words:
        current_segment.append(word)
        if len(' '.join(current_segment)) > max_length:
            segments.append(' '.join(current_segment))
            current_segment = []

    if current_segment:
        segments.append(' '.join(current_segment))

    return segments

def create_video(image_files, audio_file, output_file="output_video.mp4"):
    try:
        audio = AudioFileClip(audio_file)
        duration_per_image = audio.duration / len(image_files)

        # Create video clip with changing images
        clip = ImageSequenceClip(image_files, durations=[duration_per_image] * len(image_files))
        clip = clip.set_audio(audio)
        clip.write_videofile(output_file, codec="libx264", fps=24)
        print(f"Video created at {output_file}")  # Debugging line
    except Exception as e:
        print(f"Error creating video: {e}")

def generate_content(prompt):
    # Generate story
    story = generate_story(prompt)
    if "Error" in story:
        return story, None, None, None

    # Split story into segments
    story_segments = split_story(story)

    # Generate images for each segment
    image_files = []
    for i, segment in enumerate(story_segments):
        image_prompt = f"High-quality, clear anime style illustration of the following scene: {segment}"
        image_path = generate_image(image_prompt, i + 1)
        if image_path:
            image_files.append(image_path)

    if not image_files:
        return story, None, None, None

    # Generate audio
    audio_file = generate_audio(story)
    if audio_file is None:
        return story, image_files[0] if image_files else None, None, None

    # Create video
    create_video(image_files, audio_file=audio_file)

    # Check if files exist before returning
    if os.path.exists(audio_file) and os.path.exists("output_video.mp4"):
        return story, image_files[0] if image_files else None, audio_file, "output_video.mp4"
    else:
        return story, image_files[0] if image_files else None, audio_file, "output_video.mp4"

# Create the Gradio interface
inputs = gr.Textbox(lines=2, placeholder="Enter a sentence for the story...")
outputs = [
    gr.Textbox(label="Generated Story"),
    gr.Image(type="filepath", label="Generated Image"),
    gr.File(label="Generated Audio"),
    gr.File(label="Generated Video")
]

gr.Interface(fn=generate_content, inputs=inputs, outputs=outputs, title="Story Generator").launch(debug=True)
