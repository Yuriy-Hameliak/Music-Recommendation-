import torch
import pandas as pd
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from transformers import AutoTokenizer, AutoModel

# 1. КОПІЯ АРХІТЕКТУРИ (щоб завантажити ваги)
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
        self.logit_scale = nn.Parameter(torch.ones([]) * 2.6592)

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

# 2. ПІДГОТОВКА ДАНИХ ДЛЯ ПОШУКУ
def setup_recommender():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Запуск на: {device}")

    # Завантажуємо дані
    df = pd.read_csv('all_tracks_ULTIMATE.csv')
    features = ['BPM', 'Energy', 'Dance', 'Acoustic', 'Valence']
    df = df.dropna(subset=['Lyrics'] + features).reset_index(drop=True)

    df = df.drop_duplicates(subset=['Artist', 'Song']).reset_index(drop=True)
    # Нормалізуємо так само, як при навчанні
    scaler = StandardScaler()
    audio_matrix = scaler.fit_transform(df[features].values)
    audio_tensor = torch.tensor(audio_matrix, dtype=torch.float32).to(device)

    # Завантажуємо навчену модель
    model = ContrastiveMusicModel().to(device)
    model.load_state_dict(torch.load('contrastive_music_model.pth', map_location=device))
    model.eval() # Переводимо в режим передбачення

    # Отримуємо ембеддинги (вектори) для всієї нашої бази пісень
    print("⏳ Векторизація музичної бази...")
    with torch.no_grad():
        audio_embeds = model.encode_audio(audio_tensor)
        # Нормалізуємо вектори для косинусної схожості
        audio_embeds = audio_embeds / audio_embeds.norm(dim=1, keepdim=True)

    return model, df, audio_embeds, device

# 3. ФУНКЦІЯ РЕКОМЕНДАЦІЇ
def recommend(query, model, df, audio_embeds, device, top_k=5):
    with torch.no_grad():
        # Перетворюємо текстовий запит у вектор
        text_embed = model.encode_text([query], device)
        text_embed = text_embed / text_embed.norm(dim=1, keepdim=True)

        # Рахуємо схожість між запитом та всіма піснями (Dot Product)
        similarities = (text_embed @ audio_embeds.t()).squeeze(0)

        # Знаходимо топ-К найсхожіших
        top_scores, top_indices = torch.topk(similarities, top_k)

    print(f"\n🎧 Рекомендації для запиту: '{query}'")
    print("-" * 50)
    for i, idx in enumerate(top_indices.cpu().numpy()):
        song = df.iloc[idx]
        print(f"{i+1}. {song['Artist']} - {song['Song']}")
        print(f"   [Energy: {song['Energy']:.0f} | Acoustic: {song['Acoustic']:.0f} | Valence: {song['Valence']:.0f}]")
        print(f"   Score: {top_scores[i].item():.4f}\n")

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    model, df, audio_embeds, device = setup_recommender()
    
    # Можеш тестувати будь-які свої запити українською або англійською!
    queries = [
        "sad rainy evening with acoustic guitar",
        "дуже енергійне тренування в спортзалі",
        "спокійна фонова музика для навчання"
    ]
    
    for q in queries:
        recommend(q, model, df, audio_embeds, device)