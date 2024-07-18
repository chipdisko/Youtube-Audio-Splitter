import os
import flet as ft
from pytube import YouTube
from pydub import AudioSegment
import subprocess

def download_audio(youtube_url, output_path):
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(only_audio=True).first()
    stream.download(output_path=output_path, filename='audio.mp4')
    return os.path.join(output_path, 'audio.mp4')

def convert_to_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path, format="mp4")
    audio.export(output_path, format="wav")
    return output_path

def separate_audio(input_path, output_dir):
    command = f"demucs.separate -o {output_dir} {input_path}"
    subprocess.run(command, shell=True)

def main(page: ft.Page):
    page.title = "YouTube Audio Separator"
    
    def on_submit(e):
        youtube_url = url_input.value
        output_dir = "output"
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        audio_mp4_path = download_audio(youtube_url, output_dir)
        audio_wav_path = convert_to_wav(audio_mp4_path, os.path.join(output_dir, 'audio.wav'))
        separate_audio(audio_wav_path, output_dir)
        
        result_text.value = "Audio separation completed!"
        page.update()
    
    url_input = ft.TextField(label="YouTube URL", width=400)
    submit_button = ft.ElevatedButton(text="Separate Audio", on_click=on_submit)
    result_text = ft.Text(value="")
    
    page.add(url_input, submit_button, result_text)

ft.app(target=main)