from flask import Flask, render_template, request
import subprocess
from gtts import gTTS
from google.cloud import speech_v1p1beta1 as speech
import os
import json
from google.oauth2 import service_account

app = Flask(__name__)

# Google Cloud credentials environment se load karo
credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if credentials_json:
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/speech-key.json"
    with open("/tmp/speech-key.json", "w") as f:
        json.dump(credentials_info, f)
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/render/project/src/speech-key.json"

def generate_video(prompt):
    print("Base video use kar rahe hain: static/dancing_dog.mp4")
    base_video = "static/dancing_dog.mp4"

    # Narration banao
    narration_text = prompt
    tts = gTTS(text=narration_text, lang="en", slow=False)
    tts.save("static/narration.mp3")
    print("Narration ban gaya: static/narration.mp3")

    # Video mein audio add karo
    subprocess.run("ffmpeg -i static/dancing_dog.mp4 -i static/narration.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest static/temp_video.mp4 -y", shell=True)
    print("Temp video ban gaya: static/temp_video.mp4")

    # Audio extract karo
    subprocess.run("ffmpeg -i static/temp_video.mp4 -vn -acodec mp3 static/temp_audio.mp3 -y", shell=True)
    print("Audio extract ho gaya: static/temp_audio.mp3")

    # Subtitles banao
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
    print("Subtitles ban gaye:", subtitle_text)
    with open("static/subtitles.srt", "w") as srt_file:
        srt_file.write("1\n00:00:00,000 --> 00:00:05,000\n" + subtitle_text)

    # Subtitles add karo
    subprocess.run("ffmpeg -i static/temp_video.mp4 -vf subtitles=static/subtitles.srt static/basic_video_with_subtitles.mp4 -y", shell=True)
    print("Video with subtitles ban gaya: static/basic_video_with_subtitles.mp4")

    # Reels format banao
    subprocess.run("ffmpeg -i static/basic_video_with_subtitles.mp4 -vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2 -c:v libx264 -c:a aac -t 5 static/reel_video.mp4 -y", shell=True)
    print("Reel video ban gaya: static/reel_video.mp4")

    # Cleanup
    os.remove("static/narration.mp3")
    os.remove("static/temp_audio.mp3")
    os.remove("static/subtitles.srt")
    os.remove("static/temp_video.mp4")

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