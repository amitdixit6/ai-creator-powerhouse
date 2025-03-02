from flask import Flask, render_template, request
from diffusers import StableDiffusionPipeline
import subprocess
from gtts import gTTS
from google.cloud import speech_v1p1beta1 as speech
import cv2
import os

app = Flask(__name__)

# Google Cloud Speech-to-Text setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/ai-creator-powerhouse/speech-key.json"

# Video generation function
def generate_video(prompt):
    print("Model download shuru – thoda wait karo...")
    model = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    model = model.to("cpu")
    image = model(prompt).images[0]
    image.save("static/output.png")

    subprocess.run("ffmpeg -loop 1 -i static/output.png -c:v libx264 -t 5 -pix_fmt yuv420p static/temp_video.mp4")

    narration_text = prompt  # User prompt narration ke liye
    tts = gTTS(text=narration_text, lang="en", slow=False)
    tts.save("static/narration.mp3")

    subprocess.run("ffmpeg -i static/temp_video.mp4 -i static/narration.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 static/basic_video_with_voice.mp4")

    subprocess.run("ffmpeg -i static/basic_video_with_voice.mp4 -vn -acodec mp3 static/temp_audio.mp3")

    client = speech.SpeechClient()
    with open("static/temp_audio.mp3", "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=24000,
        language_code="en-US",
    )
    response = client.recognize(config=config, audio=audio)
    subtitle_text = ""
    for result in response.results:
        subtitle_text += result.alternatives[0].transcript + "\n"
    with open("static/subtitles.srt", "w") as srt_file:
        srt_file.write("1\n00:00:00,000 --> 00:00:05,000\n" + subtitle_text)

    subprocess.run("ffmpeg -i static/basic_video_with_voice.mp4 -vf subtitles=static/subtitles.srt static/basic_video_with_subtitles.mp4")

    video = cv2.VideoCapture("static/basic_video_with_subtitles.mp4")
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    reel_width = 1080
    reel_height = 1920
    out = cv2.VideoWriter("static/reel_video.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (reel_width, reel_height))
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        resized_frame = cv2.resize(frame, (reel_width, reel_height), interpolation=cv2.INTER_AREA)
        out.write(resized_frame)
    video.release()
    out.release()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prompt = request.form["prompt"]
        generate_video(prompt)
        return render_template("index.html", video_created=True)
    return render_template("index.html", video_created=False)

if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(debug=True)