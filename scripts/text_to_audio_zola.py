import os
import re
import json
import math
import asyncio
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List
import logging

import requests
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
import edge_tts

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----- Config & environment -----
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # optional but recommended

BASE_CONTENT = Path("content/blog")
BASE_CONTENT.mkdir(parents=True, exist_ok=True)
TMP_DIR = Path("audio_output/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ----- Utilities -----

from scripts.utils import slugify

# ----- Config & environment -----
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # optional but recommended
