import os
from dotenv import load_dotenv

# load secrets from env/.env
load_dotenv("env/discogs.env")

TOKEN = os.environ["DISCOGS_TOKEN"]
UA = os.getenv("USER_AGENT", "MusicDataProject/0.1 (contact: bhenzelc@gmail.com)")

