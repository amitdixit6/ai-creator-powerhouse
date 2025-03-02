from diffusers import StableDiffusionPipeline
import subprocess
from gtts import gTTS
from google.cloud import speech_v1p1beta1 as speech
import cv2
import os

# Google Cloud Speech-to-Text setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/ai-creator-powerhouse/speech-key.json"

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
narration_text = "This is a funny fitness clip made by AI!"
tts = gTTS(text=narration_text, lang="en", slow=False)
tts.save("narration.mp3")
print("Narration ban gaya: narration.mp3")

# Voice video mein add karo
subprocess.run("ffmpeg -i temp_video.mp4 -i narration.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 basic_video_with_voice.mp4")
print("Video with voice ban gaya: basic_video_with_voice.mp4")

# Extract audio for subtitles
subprocess.run("ffmpeg -i basic_video_with_voice.mp4 -vn -acodec mp3 temp_audio.mp3")
print("Audio extract ho gaya: temp_audio.mp3")

# Speech-to-Text se subtitles banao
client = speech.SpeechClient()
with open("temp_audio.mp3", "rb") as audio_file:
    content = audio_file.read()

audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.MP3,
    sample_rate_hertz=24000,  # narration.mp3 ka sample rate match karna
    language_code="en-US",
)

response = client.recognize(config=config, audio=audio)
subtitle_text = ""
for result in response.results:
    subtitle_text += result.alternatives[0].transcript + "\n"
print("Subtitles ban gaye:", subtitle_text)

# SRT file banao
with open("subtitles.srt", "w") as srt_file:
    srt_file.write("1\n00:00:00,000 --> 00:00:05,000\n" + subtitle_text)

# Subtitles video mein add karo
subprocess.run("ffmpeg -i basic_video_with_voice.mp4 -vf subtitles=subtitles.srt basic_video_with_subtitles.mp4")
print("Video with subtitles ban gaya: basic_video_with_subtitles.mp4")

# Video to Reels (vertical, short clip)
video = cv2.VideoCapture("basic_video_with_subtitles.mp4")
frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(video.get(cv2.CAP_PROP_FPS))

reel_width = 1080
reel_height = 1920
out = cv2.VideoWriter("reel_video.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (reel_width, reel_height))

while video.isOpened():
    ret, frame = video.read()
    if not ret:
        break
    resized_frame = cv2.resize(frame, (reel_width, reel_height), interpolation=cv2.INTER_AREA)
    out.write(resized_frame)

video.release()
out.release()
print("Reel video ban gaya: reel_video.mp4")

# Clean up temporary files
os.remove("temp_video.mp4")
os.remove("narration.mp3")
os.remove("temp_audio.mp3")
os.remove("subtitles.srt")