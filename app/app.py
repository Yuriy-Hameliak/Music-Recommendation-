import os
import numpy as np
import torch
import pandas as pd
import torch.nn as nn
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from transformers import AutoTokenizer, AutoModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import uvicorn
from dotenv import load_dotenv

# ==========================================
# 0. НАЛАШТУВАННЯ ШЛЯХІВ
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env" if (BASE_DIR / ".env").exists() else BASE_DIR.parent / ".env"
load_dotenv(dotenv_path=env_path)

MODEL_PATH = BASE_DIR / "contrastive_music_model.pth"
DATA_PATH = BASE_DIR / "all_tracks_ULTIMATE.csv"
INDEX_PATH = BASE_DIR / "index.html"

# ==========================================
# 1. SPOTIFY API
# ==========================================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError(f"Ключі Spotify не знайдені за шляхом: {env_path}")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# ==========================================
# 2. АРХІТЕКТУРА МОДЕЛІ (Без заморозки)
# ==========================================
class ContrastiveMusicModel(nn.Module):
    def __init__(self, audio_dim=5, embed_dim=128):
        super().__init__()
        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, 64),
            nn.ReLU(),
            nn.LayerNorm(64),
            nn.Linear(64, embed_dim)
        )
        model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.text_model = AutoModel.from_pretrained(model_name)
        self.text_projection = nn.Linear(384, embed_dim)
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def encode_audio(self, audio):
        return self.audio_encoder(audio)
        
    def encode_text(self, text_list, device):
        inputs = self.tokenizer(text_list, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
        outputs = self.text_model(**inputs)
        attention_mask = inputs['attention_mask'].unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(outputs.last_hidden_state * attention_mask, 1)
        sum_mask = torch.clamp(attention_mask.sum(1), min=1e-9)
        text_embeds = sum_embeddings / sum_mask
        return self.text_projection(text_embeds)

# ==========================================
# 3. ІНІЦІАЛІЗАЦІЯ СЕРВЕРА
# ==========================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"🚀 Сервер запускається на: {device}")

if not DATA_PATH.exists() or not MODEL_PATH.exists():
    raise FileNotFoundError(f"Критичні файли не знайдені в {BASE_DIR}. Перевір структуру папок!")

print("⏳ Завантаження бази треків...")
df = pd.read_csv(DATA_PATH)
features = ['BPM', 'Energy', 'Dance', 'Acoustic', 'Valence']
df = df.dropna(subset=['Lyrics'] + features)
df = df.drop_duplicates(subset=['Artist', 'Song']).reset_index(drop=True)

scaler = StandardScaler()
audio_matrix = scaler.fit_transform(df[features].values)
audio_tensor = torch.tensor(audio_matrix, dtype=torch.float32).to(device)

print("⏳ Завантаження AI моделі...")
model = ContrastiveMusicModel().to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

with torch.no_grad():
    audio_embeds = model.encode_audio(audio_tensor)
    audio_embeds = audio_embeds / audio_embeds.norm(dim=1, keepdim=True)
    
print("✅ Система готова!")

# ==========================================
# 4. API ЕНДПОІНТИ
# ==========================================
@app.get("/")
def read_root():
    return FileResponse(INDEX_PATH)

class RecommendRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/api/recommend")
def get_recommendations(req: RecommendRequest):
    try:
        with torch.no_grad():
            text_embed = model.encode_text([req.query], device)
            text_embed = text_embed / text_embed.norm(dim=1, keepdim=True)
            similarities = (text_embed @ audio_embeds.t()).squeeze(0)
            top_scores, top_indices = torch.topk(similarities, req.top_k)

        results = []
        track_ids = []
        
        for i, idx in enumerate(top_indices.cpu().numpy()):
            song = df.iloc[idx]
            track_id = str(song['Spotify Track Id']).strip()
            track_ids.append(track_id)
            results.append({
                "artist": song['Artist'],
                "song": song['Song'],
                "spotify_id": track_id,
                "image": "https://via.placeholder.com/300/121212/FFFFFF?text=No+Cover", 
                "url": f"https://open.spotify.com/track/{track_id}"
            })
        
        if track_ids:
            tracks_data = sp.tracks(track_ids)['tracks']
            for i, track_info in enumerate(tracks_data):
                if track_info and track_info['album']['images']:
                    results[i]['image'] = track_info['album']['images'][0]['url']

        return {"tracks": results}
    except Exception as e:
        print(f"🚨 Помилка при рекомендації: {e}")
        return {"tracks": [], "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)