import os
import csv
from pathlib import Path

path = "dataset"

def analyze_dataset_structure(base_path = path):
    base_dir = Path(base_path)
    
    # Перевірка, чи існує папка
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Error: The specified path '{base_path}' does not exist or is not a directory.")
        return

    grand_total_rows = 0
    
    print(f"\n{base_dir.name}")
    print("–" * 50)

    # Проходимося по головних категоріях (Погода, Час дня, Пора року)
    for category_dir in sorted(base_dir.iterdir()):
        if category_dir.is_dir():
            category_name = category_dir.name
            category_total = 0
            subcategory_stats = []

            # Проходимося по підкатегоріях (rain, morning, winter тощо)
            for subcategory_dir in sorted(category_dir.iterdir()):
                if subcategory_dir.is_dir():
                    subcategory_name = subcategory_dir.name
                    
                    # Множина тепер зберігатиме тупли вигляду: ("Назва пісні", "Артист")
                    subcategory_unique_tracks = set()

                    for csv_file in subcategory_dir.glob("*.csv"):
                        try:
                            with open(csv_file, 'r', encoding='utf-8') as f:
                                # Використовуємо csv.reader для безпечного парсингу ком
                                reader = csv.reader(f)
                                lines = list(reader)
                                
                                if not lines:
                                    continue
                                
                                header_idx = -1
                                song_idx = -1
                                artist_idx = -1
                                
                                # Шукаємо рядок хедера і точні індекси потрібних колонок
                                for i, row in enumerate(lines):
                                    if 'Song' in row and 'Artist' in row:
                                        header_idx = i
                                        song_idx = row.index('Song')
                                        artist_idx = row.index('Artist')
                                        break
                                
                                # Якщо хедера немає або не знайшли колонки — скіпаємо
                                if header_idx == -1:
                                    continue

                                # Проходимося по треках
                                for row in lines[header_idx + 1:]:
                                    # Захист від порожніх або битих рядків
                                    if not row or len(row) <= max(song_idx, artist_idx):
                                        continue
                                        
                                    song_name = row[song_idx].strip()
                                    artist_name = row[artist_idx].strip()
                                    
                                    if song_name and artist_name:
                                        # Додаємо тупл у множину
                                        subcategory_unique_tracks.add((song_name, artist_name))

                        except Exception as e:
                            print(f"  [!] Failed to read {csv_file.name}: {e}")
                    
                    subcategory_total = len(subcategory_unique_tracks)
                    subcategory_stats.append((subcategory_name, subcategory_total))
                    category_total += subcategory_total
            
            print(f"Category: {category_name.upper()} | Overall tracks: {category_total}")
            for sub_name, sub_total in subcategory_stats:
                print(f"   └── 📂 {sub_name}: {sub_total} rows")
            print("–" * 50)
            
            grand_total_rows += category_total

    # Фінальний підрахунок
    print(f"Overall # of tracks: {grand_total_rows}")
    print("=" * 50 + "\n")

analyze_dataset_structure()