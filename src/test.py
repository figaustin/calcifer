from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import json

url = "https://www.youtube.com/watch?v=xoUVtthd7gY"

search = VideosSearch("tool pneuma", limit=5)
result = search.result()["result"][0]

print(result)