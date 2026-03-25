import pandas as pd
import random
from pathlib import Path

# Папки
dataset_path = Path("dataset")
output_path = Path(".")

# Твій жорстко заданий порядок колонок
TARGET_COLUMNS = [
    "#", "Song", "Artist", "BPM", "Camelot", "Energy", "Duration", 
    "Popularity", "Genres", "Album", "Album Date", "Dance", "Acoustic", 
    "Instrumental", "Valence", "Speech", "Live", "Loud (db)", "Key", 
    "Time Signature", "Spotify Track Id"
]

categories = ["season", "time", "weather"]

def merge_clean_datasets():
    for category in categories:
        category_dir = dataset_path / category
        if not category_dir.exists() or not category_dir.is_dir():
            continue
            
        print(f"\n🔄 Обробка категорії: {category.upper()}")
        print("-" * 50)
        
        all_dfs = []
        label_col = f"{category.capitalize()}_Label"
        
        for subcategory_dir in category_dir.iterdir():
            if not subcategory_dir.is_dir():
                continue
                
            label = subcategory_dir.name
            
            for csv_file in subcategory_dir.glob("*.csv"):
                try:
                    # Читаємо файл. on_bad_lines='skip' проігнорує криві рядки, які ламають структуру
                    df = pd.read_csv(csv_file, on_bad_lines='skip', low_memory=False)
                    
                    # Очищаємо назви колонок від випадкових пробілів (напр. " BPM " -> "BPM")
                    df.columns = df.columns.str.strip()
                    
                    # Якщо немає базових колонок - скіпаємо файл
                    if 'Song' not in df.columns or 'Artist' not in df.columns:
                        continue
                    
                    # Залишаємо ТІЛЬКИ ті колонки, які є в твоєму списку і присутні у файлі
                    existing_cols = [c for c in TARGET_COLUMNS if c in df.columns]
                    df = df[existing_cols]
                    
                    # Примусово робимо Song та Artist рядками, щоб не було проблем при групуванні
                    df['Song'] = df['Song'].astype(str).str.strip()
                    df['Artist'] = df['Artist'].astype(str).str.strip()
                    
                    # Додаємо наш лейбл (rainy, summer, night тощо)
                    df[label_col] = label
                    
                    all_dfs.append(df)
                    
                except Exception as e:
                    print(f" [!] Помилка з {csv_file.name}: {e}")
        
        if not all_dfs:
            print(f"⚠️ Немає даних для {category}")
            continue
            
        # Зліплюємо всі дані в одну велику таблицю. 
        # Pandas автоматично підставить порожнечу (NaN) туди, де колонок не вистачало
        merged_df = pd.concat(all_dfs, ignore_index=True)
        
        # Видаляємо порожні рядки, де немає назви пісні
        merged_df = merged_df.dropna(subset=['Song', 'Artist'])
        merged_df = merged_df[(merged_df['Song'] != '') & (merged_df['Song'] != 'nan')]
        
        # Створюємо фінальний набір колонок: твій список + колонка лейблу
        for col in TARGET_COLUMNS:
            if col not in merged_df.columns:
                merged_df[col] = None # Створюємо пусті колонки, якщо їх взагалі ніде не було
                
        # Функція для вирішення конфліктів (коли одна пісня має кілька міток)
        def resolve_labels(x):
            unique_labels = list(set(x.dropna()))
            return random.choice(unique_labels) if unique_labels else None

        # Правила злиття дублікатів: для фічів беремо перше значення, для лейблів - рандом з доступних
        agg_funcs = {col: 'first' for col in TARGET_COLUMNS if col not in ['Song', 'Artist']}
        agg_funcs[label_col] = resolve_labels
        
        print("⏳ Групування унікальних треків та вирішення конфліктів...")
        final_df = merged_df.groupby(['Song', 'Artist'], as_index=False).agg(agg_funcs)
        
        # Задаємо ЖОРСТКИЙ порядок колонок, як ти просив
        final_cols = TARGET_COLUMNS + [label_col]
        final_df = final_df[final_cols]
        
        # Зберігаємо
        out_file = output_path / f"{category}.csv"
        final_df.to_csv(out_file, index=False)
        print(f"✅ Готово! Збережено: {out_file.name} (Унікальних треків: {len(final_df)})")

if __name__ == "__main__":
    merge_clean_datasets()