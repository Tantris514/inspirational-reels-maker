import yaml
import argparse
from openai import OpenAI
import requests
import random
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop
from moviepy.video.fx.margin import margin
from moviepy.editor import AudioFileClip
import os


parser = argparse.ArgumentParser(description="Okta Client Configuration")
parser.add_argument("-c", "--config", help="Path to the configuration YAML file", required=True)
args = parser.parse_args()
loadConfig = lambda config_file: yaml.safe_load(open(config_file, 'r'))
yamlConfig = loadConfig(args.config)

openai_key = yamlConfig["openai"]["apikey"]
pexels_key = yamlConfig["pexels"]["apikey"]
freesound_key = yamlConfig["freesound"]["apikey"]




client = OpenAI(
  organization='org-ucCRhUIXtuLLYoGQMZ2l0oXm',
  project='proj_MaMf0mWqgLNrTCzQrxbvBrdZ',
)

prompt = f"""
Your goal is to give an inspirational quote to help people feel better for 2025, you must include 2025 and something that will talk to people. 
Juste reply to quote, nothing more. 
Here are examples :
Let 2025 be the year we discover the strength in our resilience, the beauty in our dreams, and the boundless potential within our hearts.

In 2025, let us rise with determination, dream with fervor, and create a future that shines brighter than our wildest imaginations.

In 2025, let us embrace every challenge as an opportunity to grow, every setback as a lesson, and every success as a stepping stone to even greater heights.

Finally, Try to be as creative as possible. Do not reuse.

"""

def search_sounds(access_token, query, max_results=1000, duration_range="[10 TO 60]"):
    url = "https://freesound.org/apiv2/search/text/"
    headers = {"Authorization": f"Token {access_token}"}
    params = {
        "query": query,
        "filter": f"duration:{duration_range}",
        "fields": "id,name,previews,tag",
        "page_size": max_results,
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error searching sounds:", response.json())
        return None

def download_sound(preview_url, save_directory="./sounds/"):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    filename = preview_url.split("/")[-1]
    save_path = os.path.join(save_directory, filename)
    try:
        response = requests.get(preview_url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Sound downloaded and saved as {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading sound: {e}")
        return None

def get_inspirational_quote(prompt,client) -> str:
    stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    )
    awnser = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            awnser += chunk.choices[0].delta.content
    print(awnser)
    with open("used_quote.txt", "a") as file:
        file.write(awnser + "\n")
    return awnser


def get_video_url(apikey):
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": apikey
    }
    params = {
        "query": "inspiration,waterfall,nature,forest,space,animals",
        "per_page": 1,
        "page" : random.randint(1,8000),
        "orientation" : "portrait",
        "min_duration" : 5,
        "max_duration" : 10,
        "size" : "small"
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()["videos"][0]["video_files"][0]["link"]


def download_video(url, save_directory="./videos/"):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    filename = url.split("/")[-1]
    save_path = os.path.join(save_directory, filename)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return save_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading video: {e}")
        return None

def add_text_to_video(path,text):
    video = VideoFileClip(path)
    if video.h >= 1000:
        font_size = 100
    else:
        font_size = 40
    
    text_clip = TextClip(
        text,
        fontsize=font_size,
        font="Georgia",  
        color='white',
        bg_color='rgba(0, 0, 0, 0.2)', 
        size=(video.w * 0.8, None),  
        method='caption'
    )
    
    text_clip = text_clip.set_position("center").set_duration(video.duration)
    video_with_text = CompositeVideoClip([video, text_clip])
    output_path = F"./videos/video{random.randint(1,9*99999)}.mp4"
    video_with_text.write_videofile(output_path, codec="libx264", fps=24)
    os.remove(path)
    return output_path
    

def trim_to_first_10_seconds(input_path, output_path=None):
    
    try:
        video = VideoFileClip(input_path)
        trimmed_video = video.subclip(0, min(10, video.duration))
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_trimmed{ext}"
            trimmed_video.write_videofile(output_path, codec="libx264", fps=24)
        video.close()
        trimmed_video.close()
        print(f"Trimmed video saved as {output_path}")
        return output_path
    except Exception as e:
        print(f"Error trimming video: {e}")
        return None
    
def resize_to_1080x2048(input_path, output_path=None):
    try:
        video = VideoFileClip(input_path)
        target_width, target_height = 1080, 2048
        
        video_aspect_ratio = video.w / video.h
        target_aspect_ratio = target_width / target_height
        
        if video_aspect_ratio > target_aspect_ratio:
            resized_video = resize(video, height=target_height)
            excess_width = resized_video.w - target_width
            cropped_video = crop(
                resized_video,
                x_center=resized_video.w / 2,
                y_center=resized_video.h / 2,
                width=target_width,
                height=target_height
            )
        else:
            resized_video = resize(video, width=target_width)
            excess_height = resized_video.h - target_height
            cropped_video = crop(
                resized_video,
                x_center=resized_video.w / 2,
                y_center=resized_video.h / 2,
                width=target_width,
                height=target_height
            )
        
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_resized{ext}"
        
        cropped_video.write_videofile(output_path, codec="libx264", fps=24)
        
        video.close()
        resized_video.close()
        cropped_video.close()
        
        print(f"Resized video saved as {output_path}")
        return output_path
    except Exception as e:
        print(f"Error resizing video: {e}")
        return None



def check_video_validity(path):
    video = VideoFileClip(path)
    duration = video.duration
    video.close()
    print(duration)
    if duration >= 10:
        return False
    else:
        return True
    
def add_audio_to_video(video_path, sound_path,name=None):
    video = VideoFileClip(video_path)
    sound = AudioFileClip(sound_path)
    
    if sound.duration > video.duration:
        sound = sound.subclip(0, video.duration)  
    
    video = video.set_audio(sound)
    if name == None:
        output_path = f"./videos_and_sound/reel{random.randint(1, 999)}.mp4"
    else:
        output_path = f"./videos_and_sound/reel{name}.mp4"

    video.write_videofile(output_path, codec="libx264", fps=24)

    
    video.close()
    sound.close()
    
    return output_path





def make_a_reel(name=None):
    music_keyword = [
    "Piano", "Inspirational", "Violon", "Calm", "Motivational", "Peaceful", "Uplifting",
    "Hopeful", "Strings", "Serene", "Emotional", "Epic", "Relaxing", "Cinematic", "Ambient", "Warm",
    "Joyful", "Beautiful", "Dreamy", "Positive", "Empowering", "Flowing", "Soothing", "Elegant", "Peaceful",
    "Ethereal", "Triumphant", "Light", "Heartfelt", "Graceful", "Tranquil", "Majestic", "Melodic", "Orchestration",
    "Soft", "Passionate", "Motivating", "Healing", "Lush", "Inspirational strings", "Refined", "Vibrant", "Noble",
    "Bright", "Acoustic", "Joyous", "Positive energy", "Healing vibes", "Euphoria", "Relaxation", "Introspective",
    "Serendipity", "Harmony", "Reflective", "Cinematic strings", "Adventure", "Powerful", "Solo piano", "Rising",
    "Wonder", "Dreamlike", "Grace", "Unstoppable", "Light-hearted", "Sweeping", "Spirit-lifting",
    "Courageous", "Motivating beat", "Timeless", "Everlasting", "Sacred", "Victory", "Freedom", "Exploration",
    "Invigorating", "Radiant", "Glorious", "Determined", "Striking", "Infinite", "Visionary", "Moving", "Rejuvenating",
    "Glowing", "Focused", "Powerful melody", "Steady", "Inspirational rise", "Anthemic", "Warmth", "Strength",
    "Invincible", "Alluring", "Blissful", "Tender", "Monumental", "Motivating rhythm", "Captivating"
    ]

    music_query = random.choice(music_keyword)
    print(music_query)
    sounds = search_sounds(freesound_key, music_query)
    results = sounds["results"]
    sound_obj = (random.choice(results))
    preview_url = sound_obj["previews"]["preview-lq-mp3"]
    sound_path = download_sound(preview_url)
    
    
    video_url = get_video_url(pexels_key)
    video_path = download_video(video_url)
    if not check_video_validity(video_path):
        old_video_path = video_path
        video_path = trim_to_first_10_seconds(video_path)
        os.remove(old_video_path)
    old_video_path = video_path
    video_path = resize_to_1080x2048(video_path)
    os.remove(old_video_path)
    quote = get_inspirational_quote(prompt,client)
    video_path = add_text_to_video(video_path,quote)
    reels_name = add_audio_to_video(video_path,sound_path,name)
    os.remove(video_path)
    os.remove(sound_path)
    return reels_name
    

def main():
    for i in range(1,100):
        try:
            print(make_a_reel(name=i))
        except:
            continue
        

        
main()