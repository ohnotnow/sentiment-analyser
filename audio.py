from pydub import AudioSegment
import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')

song = AudioSegment.from_mp3("01 Marple - A Murder Is Announced - Episode 1.mp3")

# PyDub handles time in milliseconds
ten_minutes = 10 * 60 * 1000

first_10_minutes = song[:ten_minutes]

first_10_minutes.export("test.mp3", format="mp3")

# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
audio_file= open("test.mp3", "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
print(transcript)

