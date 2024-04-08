from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import json


search = VideosSearch("megadeth", limit=5)

print(search.result()["result"][0])
    