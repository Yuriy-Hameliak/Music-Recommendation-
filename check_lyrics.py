import pandas as pd

# Завантажуємо оновлений датасет
df = pd.read_csv('all_tracks_with_lyrics.csv')

# Загальна кількість рядків
total_tracks = len(df)

# Рахуємо кількість заповнених текстів 
# (перевіряємо, щоб це був не NaN і не просто порожній рядок)
has_lyrics = df['Lyrics'].notna() & (df['Lyrics'].astype(str).str.strip() != '')

tracks_with_lyrics = has_lyrics.sum()
tracks_without_lyrics = total_tracks - tracks_with_lyrics

print("📊 Статистика завантаження текстів:")
print("-" * 40)
print(f"Загальна кількість треків: {total_tracks}")
print(f"✅ Треки З текстом: {tracks_with_lyrics} ({(tracks_with_lyrics/total_tracks)*100:.1f}%)")
print(f"❌ Треки БЕЗ тексту: {tracks_without_lyrics} ({(tracks_without_lyrics/total_tracks)*100:.1f}%)")
print("-" * 40)

# Додатково: виведемо статистику по категоріях, щоб побачити, де найбільше втрат
if 'Category' in df.columns:
    print("\nРозподіл наявності текстів по категоріях:")
    # Створюємо тимчасову колонку для групування
    df['Has_Lyrics'] = has_lyrics
    grouped = df.groupby('Category')['Has_Lyrics'].agg(['count', 'sum'])
    grouped.columns = ['Всього', 'З текстом']
    grouped['Відсоток'] = (grouped['З текстом'] / grouped['Всього'] * 100).round(1)
    print(grouped)