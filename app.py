# import gradio as gr
# from gtts import gTTS
# import spaces
# import moviepy
# from moviepy.editor import ImageSequenceClip, AudioFileClip
# from diffusers import StableDiffusionPipeline
# import torch
# import cohere
# import os
# from PIL import Image


# model_id = "CompVis/stable-diffusion-v1-4"
# sd_pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
# sd_pipe.to("cuda")

# # Initialize Cohere securely
# api_key = os.getenv("COHERE_API_KEY")

# co = cohere.ClientV2(api_key=api_key) if api_key else None

# # def generate_story(prompt):
# #     try:
# #         response = co.generate(
# #             model='command-xlarge',  # Change model to a supported one
# #             prompt=f"Write a short story based on: {prompt}",
# #             max_tokens=500,
# #             temperature=0.9
# #         )
# #         story = response.generations[0].text.strip()
# #         return story
# #     except Exception as e:
# #         print(f"Error generating story: {e}")
# #         return f"Error generating story: {e}"
# def generate_story(prompt):
#     try:
#         if co is None:
#             return "Error: Cohere API key is not configured."

#         response = co.chat(
#             model="command-a-03-2025",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": f"Write a creative, engaging short story based on: {prompt}"
#                 }
#             ],
#             max_tokens=500,
#             temperature=0.9
#         )

#         story = response.message.content[0].text.strip()
#         return story

#     except Exception as e:
#         print(f"Error generating story: {e}")
#         return f"Error generating story: {e}"
        
# def generate_image(prompt, image_id):
#     try:
#         image = sd_pipe(prompt).images[0]
#         image = image.convert("RGB")  # Ensure image is in RGB mode
#         image_path = f"scene_{image_id}.png"
#         image.save(image_path)
#         print(f"Generated image saved at {image_path}")  # Debugging line
#         return image_path
#     except Exception as e:
#         print(f"Error generating image: {e}")
#         return None

# def generate_audio(text, filename="output.mp3"):
#     try:
#         tts = gTTS(text=text, lang='en')
#         tts.save(filename)
#         print(f"Generated audio saved at {filename}")  # Debugging line
#         return filename
#     except Exception as e:
#         print(f"Error generating audio: {e}")
#         return None

# def split_story(story, max_length=100):
#     words = story.split()
#     segments = []
#     current_segment = []

#     for word in words:
#         current_segment.append(word)
#         if len(' '.join(current_segment)) > max_length:
#             segments.append(' '.join(current_segment))
#             current_segment = []

#     if current_segment:
#         segments.append(' '.join(current_segment))

#     return segments

# def create_video(image_files, audio_file, output_file="output_video.mp4"):
#     try:
#         audio = AudioFileClip(audio_file)
#         duration_per_image = audio.duration / len(image_files)

#         # Create video clip with changing images
#         clip = ImageSequenceClip(image_files, durations=[duration_per_image] * len(image_files))
#         clip = clip.set_audio(audio)
#         clip.write_videofile(output_file, codec="libx264", fps=24)
#         print(f"Video created at {output_file}")  # Debugging line
#     except Exception as e:
#         print(f"Error creating video: {e}")

# @spaces.GPU(duration=180)
# def generate_content(prompt):
#     # Generate story
#     story = generate_story(prompt)
#     if "Error" in story:
#         return story, None, None, None

#     # Split story into segments
#     story_segments = split_story(story)

#     # Generate images for each segment
#     image_files = []
#     for i, segment in enumerate(story_segments):
#         image_prompt = f"High-quality, clear anime style illustration of the following scene: {segment}"
#         image_path = generate_image(image_prompt, i + 1)
#         if image_path:
#             image_files.append(image_path)

#     if not image_files:
#         return story, None, None, None

#     # Generate audio
#     audio_file = generate_audio(story)
#     if audio_file is None:
#         return story, image_files[0] if image_files else None, None, None

#     # Create video
#     create_video(image_files, audio_file=audio_file)

#     # Check if files exist before returning
#     if os.path.exists(audio_file) and os.path.exists("output_video.mp4"):
#         return story, image_files[0] if image_files else None, audio_file, "output_video.mp4"
#     else:
#         return story, image_files[0] if image_files else None, audio_file, "output_video.mp4"

# # Create the Gradio interface
# inputs = gr.Textbox(lines=2, placeholder="Enter a sentence for the story...")
# outputs = [
#     gr.Textbox(label="Generated Story"),
#     gr.Image(type="filepath", label="Generated Image"),
#     gr.File(label="Generated Audio"),
#     gr.File(label="Generated Video")
# ]

# gr.Interface(fn=generate_content, inputs=inputs, outputs=outputs, title="Story Generator").launch(debug=True)



import json
import os
import re
import tempfile
import textwrap

import cohere
import gradio as gr
import numpy as np
import spaces
import torch
from diffusers import StableDiffusionXLPipeline
from gtts import gTTS
from moviepy.editor import AudioFileClip, VideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
IMG_MODEL = "cagliostrolab/animagine-xl-3.1"  # anime-tuned SDXL
GEN_W, GEN_H = 1344, 768          # SDXL-friendly 16:9-ish size
VID_W, VID_H = 1280, 720          # final video size
FPS = 24
FADE = 0.4                        # seconds of fade in/out per scene
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

NEGATIVE = (
    "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, "
    "fewer digits, cropped, worst quality, low quality, jpeg artifacts, "
    "signature, watermark, username, blurry, deformed, ugly"
)
QUALITY = "masterpiece, best quality, very aesthetic, absurdres"

STYLES = {
    "Classic anime": "anime style, vibrant colors, detailed background, soft lighting",
    "Ghibli-like watercolor": "watercolor, soft pastel colors, hand-painted background, whimsical, studio ghibli inspired",
    "Cinematic anime": "cinematic lighting, dramatic composition, depth of field, film still, anime style",
    "Dark fantasy": "dark fantasy, moody lighting, dramatic shadows, rich detail, anime style",
}

# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
sd_pipe = StableDiffusionXLPipeline.from_pretrained(
    IMG_MODEL, torch_dtype=torch.float16, use_safetensors=True
)
sd_pipe.to("cuda")

api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key=api_key) if api_key else None


# ----------------------------------------------------------------------------
# 1. Story -> structured scenes
# ----------------------------------------------------------------------------
STORY_SYSTEM = """You are a screenwriter for short animated stories.
Return ONLY valid JSON with this exact shape:
{
  "title": "story title",
  "characters": "comma-separated visual tags describing the main character(s): hair, eyes, outfit, age, distinctive items. Keep it under 25 words. No names.",
  "scenes": [
    {
      "narration": "2-3 sentences of narration for this scene, vivid and emotional",
      "visual": "comma-separated visual tags for the image: setting, action, camera angle, lighting, mood. Under 30 words. No names, no text in image."
    }
  ]
}
The story must have a clear beginning, middle and satisfying ending across the scenes."""


def _parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def write_story(prompt, n_scenes):
    if co is None:
        raise gr.Error("COHERE_API_KEY is not configured.")

    response = co.chat(
        model="command-a-03-2025",
        messages=[
            {"role": "system", "content": STORY_SYSTEM},
            {
                "role": "user",
                "content": f"Idea: {prompt}\nNumber of scenes: exactly {n_scenes}.",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=2000,
        temperature=0.8,
    )
    raw = response.message.content[0].text
    try:
        data = _parse_json(raw)
        scenes = data["scenes"][:n_scenes]
        assert scenes and all("narration" in s and "visual" in s for s in scenes)
    except Exception as e:
        raise gr.Error(f"Could not parse story from the model: {e}")
    data["scenes"] = scenes
    data.setdefault("title", "Untitled")
    data.setdefault("characters", "")
    return data


# ----------------------------------------------------------------------------
# 2. Images (GPU only for this step to save quota)
# ----------------------------------------------------------------------------
@spaces.GPU(duration=240)
def generate_images(story, style_name, seed):
    style = STYLES[style_name]
    images = []
    for i, scene in enumerate(story["scenes"]):
        prompt = ", ".join(
            p for p in [QUALITY, story["characters"], scene["visual"], style] if p
        )
        gen = torch.Generator("cuda").manual_seed(seed + i)
        img = sd_pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE,
            width=GEN_W,
            height=GEN_H,
            num_inference_steps=28,
            guidance_scale=7.0,
            generator=gen,
        ).images[0]
        images.append(img.convert("RGB"))
    return images


# ----------------------------------------------------------------------------
# 3. Audio + captions + Ken Burns animation
# ----------------------------------------------------------------------------
def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def tts(text, path):
    gTTS(text=text, lang="en").save(path)
    return path


def split_caption_chunks(text, max_chars=95):
    """Split narration into short caption chunks (by sentence, then by length)."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    for s in sentences:
        if len(s) <= max_chars:
            chunks.append(s)
        else:
            chunks.extend(textwrap.wrap(s, max_chars))
    return [c for c in chunks if c]


def wrap_pixels(draw, text, font, max_w):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_w:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def render_caption_layer(text, font):
    """RGBA overlay with a translucent bar and outlined white text at the bottom."""
    layer = Image.new("RGBA", (VID_W, VID_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap_pixels(d, text, font, VID_W - 160)
    line_h = font.size + 10
    block_h = line_h * len(lines) + 40
    y0 = VID_H - block_h - 30
    d.rounded_rectangle(
        (60, y0, VID_W - 60, y0 + block_h), radius=24, fill=(0, 0, 0, 150)
    )
    y = y0 + 20
    for line in lines:
        w = d.textlength(line, font=font)
        d.text(
            ((VID_W - w) / 2, y), line, font=font, fill="white",
            stroke_width=2, stroke_fill="black",
        )
        y += line_h
    return layer


def make_scene_clip(image, narration, audio_path, idx):
    audio = AudioFileClip(audio_path)
    dur = audio.duration + 0.6

    # Crop generation image to exact 16:9 for camera moves
    sw, sh = image.size
    target_h = int(sw * 9 / 16)
    top = (sh - target_h) // 2
    src = image.crop((0, top, sw, top + target_h))
    sw, sh = src.size

    # Alternate camera moves: zoom in, zoom out, pan left, pan right
    moves = [
        dict(z=(1.0, 1.18), px=(0.5, 0.5), py=(0.5, 0.5)),
        dict(z=(1.18, 1.0), px=(0.5, 0.5), py=(0.5, 0.5)),
        dict(z=(1.15, 1.15), px=(0.0, 1.0), py=(0.5, 0.5)),
        dict(z=(1.15, 1.15), px=(1.0, 0.0), py=(0.5, 0.5)),
    ]
    mv = moves[idx % len(moves)]

    # Captions synced to narration (proportional to chunk length)
    font = load_font(38)
    chunks = split_caption_chunks(narration)
    total = sum(len(c) for c in chunks) or 1
    timeline, t_acc = [], 0.0
    for c in chunks:
        span = audio.duration * len(c) / total
        timeline.append((t_acc, t_acc + span, render_caption_layer(c, font)))
        t_acc += span

    def make_frame(t):
        p = min(max(t / dur, 0), 1)
        p = p * p * (3 - 2 * p)  # smoothstep easing
        z = mv["z"][0] + (mv["z"][1] - mv["z"][0]) * p
        cw, ch = sw / z, sh / z
        fx = mv["px"][0] + (mv["px"][1] - mv["px"][0]) * p
        fy = mv["py"][0] + (mv["py"][1] - mv["py"][0]) * p
        x0, y0 = (sw - cw) * fx, (sh - ch) * fy
        frame = src.resize(
            (VID_W, VID_H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)
        )
        for start, end, layer in timeline:
            if start <= t < end:
                frame.paste(layer, (0, 0), layer)
                break
        arr = np.asarray(frame)
        f = min(1.0, t / FADE, max(dur - t, 0) / FADE)
        if f < 1.0:
            arr = (arr * f).astype(np.uint8)
        return arr

    return VideoClip(make_frame, duration=dur).set_audio(audio)


def build_video(story, images, workdir):
    clips = []
    for i, (scene, img) in enumerate(zip(story["scenes"], images)):
        audio_path = tts(scene["narration"], os.path.join(workdir, f"scene_{i}.mp3"))
        clips.append(make_scene_clip(img, scene["narration"], audio_path, i))
    final = concatenate_videoclips(clips, method="chain")
    out = os.path.join(workdir, "story.mp4")
    final.write_videofile(
        out, fps=FPS, codec="libx264", audio_codec="aac",
        preset="veryfast", threads=4, logger=None,
    )
    return out


# ----------------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------------
def run(prompt, n_scenes, style_name, seed, progress=gr.Progress()):
    if not prompt or not prompt.strip():
        raise gr.Error("Please enter a story idea.")
    seed = int(seed)
    workdir = tempfile.mkdtemp()

    progress(0.05, desc="Writing story...")
    story = write_story(prompt.strip(), int(n_scenes))

    progress(0.2, desc="Painting scenes...")
    images = generate_images(story, style_name, seed)

    progress(0.7, desc="Narrating and animating...")
    video_path = build_video(story, images, workdir)

    text = f"# {story['title']}\n\n" + "\n\n".join(
        f"**Scene {i + 1}.** {s['narration']}" for i, s in enumerate(story["scenes"])
    )
    gallery = [(img, f"Scene {i + 1}") for i, img in enumerate(images)]
    return video_path, text, gallery


with gr.Blocks(title="Animated Story Generator") as demo:
    gr.Markdown("# Animated Story Generator\nText idea → illustrated, narrated, captioned animation.")
    with gr.Row():
        with gr.Column(scale=1):
            prompt = gr.Textbox(lines=3, label="Story idea",
                                placeholder="A lonely lighthouse keeper befriends a storm spirit...")
            n_scenes = gr.Slider(3, 8, value=5, step=1, label="Number of scenes")
            style = gr.Dropdown(list(STYLES), value="Classic anime", label="Art style")
            seed = gr.Number(value=42, precision=0, label="Seed (same seed = same look)")
            btn = gr.Button("Generate", variant="primary")
        with gr.Column(scale=2):
            video = gr.Video(label="Animated story")
    story_md = gr.Markdown()
    gallery = gr.Gallery(label="Scenes", columns=4, height="auto")

    btn.click(run, [prompt, n_scenes, style, seed], [video, story_md, gallery])

demo.queue().launch()
