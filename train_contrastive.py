import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

# ==========================================
# 1. ПІДГОТОВКА ДАНИХ (Dataset)
# ==========================================
class MusicTextDataset(Dataset):
    def __init__(self, csv_file):
        print("⏳ Завантаження та очищення даних...")
        df = pd.read_csv(csv_file)
        
        # Залишаємо ТІЛЬКИ ті рядки, де є текст і всі аудіо-фічі
        features = ['BPM', 'Energy', 'Dance', 'Acoustic', 'Valence']
        df = df.dropna(subset=['Lyrics'] + features)
        
        # Щоб зекономити час на першому тесті, візьмемо перші 5000 треків
        # (Коли переконаєшся, що все працює, прибери або збільш цей ліміт!)
        
        self.texts = df['Lyrics'].tolist()
        
        # Нормалізуємо аудіо-дані (це критично важливо для нейромереж!)
        scaler = StandardScaler()
        self.audio_features = scaler.fit_transform(df[features].values)
        self.audio_features = torch.tensor(self.audio_features, dtype=torch.float32)

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        return self.audio_features[idx], self.texts[idx]

# ==========================================
# 2. АРХІТЕКТУРА МОДЕЛІ
# ==========================================
class ContrastiveMusicModel(nn.Module):
    def __init__(self, audio_dim=5, embed_dim=128):
        super().__init__()
        
        # Audio Encoder: Проста нейромережа для цифр
        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, 64),
            nn.ReLU(),
            nn.LayerNorm(64),
            nn.Linear(64, embed_dim)
        )
        
        # Text Encoder: Використовуємо легку мовну модель
        model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.text_model = AutoModel.from_pretrained(model_name)
        
        # Проєкція тексту в той самий розмір виміру, що й аудіо (128)
        self.text_projection = nn.Linear(384, embed_dim)
        
        # Температура для лоссу (допомагає розрізняти схожі вектори)
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def encode_audio(self, audio):
        return self.audio_encoder(audio)
        
    def encode_text(self, text_list, device):
        # Токенізуємо батч текстів (обрізаємо до 128 слів для швидкості)
        inputs = self.tokenizer(text_list, padding=True, truncation=True, max_length=128, return_tensors="pt").to(device)
        
        # Отримуємо ембеддинги (вектори)
        outputs = self.text_model(**inputs)
        
        # Використовуємо Mean Pooling (середнє значення всіх токенів)
        attention_mask = inputs['attention_mask'].unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(outputs.last_hidden_state * attention_mask, 1)
        sum_mask = torch.clamp(attention_mask.sum(1), min=1e-9)
        text_embeds = sum_embeddings / sum_mask
        
        return self.text_projection(text_embeds)

    def forward(self, audio, text_list, device):
        audio_embeds = self.encode_audio(audio)
        text_embeds = self.encode_text(text_list, device)
        
        # Нормалізація векторів
        audio_embeds = audio_embeds / audio_embeds.norm(dim=1, keepdim=True)
        text_embeds = text_embeds / text_embeds.norm(dim=1, keepdim=True)
        
        # Косинусна схожість
        logit_scale = self.logit_scale.exp()
        logits_per_audio = logit_scale * audio_embeds @ text_embeds.t()
        logits_per_text = logits_per_audio.t()
        
        return logits_per_audio, logits_per_text

# ==========================================
# 3. ЦИКЛ НАВЧАННЯ
# ==========================================
def train():
    # Налаштування пристрою (якщо в тебе Mac на M1/M2/M3, використаємо MPS для швидкості)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"🚀 Використовуємо пристрій: {device}")

    # Завантаження даних
    dataset = MusicTextDataset('all_tracks_ULTIMATE.csv')
    dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

    # Ініціалізація моделі
    model = ContrastiveMusicModel().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    loss_fn = nn.CrossEntropyLoss()

    epochs = 15
    print("🔥 Починаємо тренування...")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        progress_bar = tqdm(dataloader, desc=f"Епоха {epoch+1}/{epochs}")
        for audio_batch, text_batch in progress_bar:
            audio_batch = audio_batch.to(device)
            
            optimizer.zero_grad()
            
            # Отримуємо матриці схожості
            logits_per_audio, logits_per_text = model(audio_batch, text_batch, device)
            
            # Ідеальна схожість - це діагональ матриці (аудіо 1 має відповідати тексту 1)
            labels = torch.arange(len(audio_batch), dtype=torch.long, device=device)
            
            # Рахуємо симетричний лосс (як у CLIP)
            loss_audio = loss_fn(logits_per_audio, labels)
            loss_text = loss_fn(logits_per_text, labels)
            loss = (loss_audio + loss_text) / 2
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': f"{loss.item():.4f}"})
            
        print(f"✅ Епоха {epoch+1} завершена. Середній Loss: {total_loss/len(dataloader):.4f}")

    # Зберігаємо натреновану модель
    torch.save(model.state_dict(), 'contrastive_music_model.pth')
    print("💾 Модель збережено у 'contrastive_music_model.pth'")

if __name__ == "__main__":
    train()