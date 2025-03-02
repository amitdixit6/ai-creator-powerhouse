from diffusers import StableDiffusionPipeline
import subprocess
from gtts import gTTS
import cv2
import os

print("Model download shuru – thoda wait karo...")
model = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
model = model.to("cpu")

# Prompt se video banao
prompt = "Ek chhota funny fitness clip"
image = model(prompt).images[0]
image.save("output.png")
print("Image ban gaya: output.png")

# Video without voice
subprocess.run("ffmpeg -loop 1 -i output.png -c:v libx264 -t 5 -pix_fmt yuv420p temp_video.mp4")
print("Temp video ban gaya: temp_video.mp4")

# Real Human Voice narration with gTTS
narration_text = "This is a funny fitness clip made by AI!"  # Prompt se narration ban sakta hai
tts = gTTS(text=narration_text, lang="en", slow=False)
tts.save("narration.mp3")
print("Narration ban gaya: narration.mp3")

# Voice video mein add karo
subprocess.run("ffmpeg -i temp_video.mp4 -i narration.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 basic_video_with_voice.mp4")
print("Video with voice ban gaya: basic_video_with_voice.mp4")

# Video to Reels (vertical, short clip)
video = cv2.VideoCapture("basic_video_with_voice.mp4")
frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(video.get(cv2.CAP_PROP_FPS))

# Reels format: 9:16 aspect ratio (1080x1920)
reel_width = 1080
reel_height = 1920
out = cv2.VideoWriter("reel_video.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (reel_width, reel_height))

while video.isOpened():
    ret, frame = video.read()
    if not ret:
        break
    # Resize aur crop karo
    resized_frame = cv2.resize(frame, (reel_width, reel_height), interpolation=cv2.INTER_AREA)
    out.write(resized_frame)

video.release()
out.release()
print("Reel video ban gaya: reel_video.mp4")

# Clean up temporary files
os.remove("temp_video.mp4")
os.remove("narration.mp3")