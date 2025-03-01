from diffusers import StableDiffusionPipeline
import subprocess

# Model load karo – pehli baar download hoga
print("Model download shuru – thoda wait karo...")
model = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
model = model.to("cpu")  # CPU pe chalega

# Prompt se image banao (video ka pehla step)
prompt = "Ek chhota funny fitness clip"
image = model(prompt).images[0]
image.save("output.png")
print("Image ban gaya: output.png")

# Image ko 5-second video mein badlo
subprocess.run("ffmpeg -loop 1 -i output.png -c:v libx264 -t 5 -pix_fmt yuv420p basic_video.mp4")
print("Video ban gaya: basic_video.mp4")