import os
import csv
import random
from pathlib import Path

# Папка з нашими відсортованими плейлистами
dataset_path = "dataset"
# Папка, куди зберігати готові змерджені датасети (поточна коренева папка)
output_path = "." 

def merge_datasets(base_path=dataset_path, out_dir=output_path):
    base_dir = Path(base_path)
    output_dir = Path(out_dir)
    
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"❌ Помилка: Папку '{base_path}' не знайдено.")
        return

    # Головні категорії, для яких ми робимо окремі файли
    categories = ["season", "time", "weather"]
    
    # НОВЕ: Змінна для підрахунку загальної кількості конфліктів по всіх категоріях
    total_conflicts_all_categories = 0
    
    for category_name in categories:
        category_dir = base_dir / category_name
        if not category_dir.exists() or not category_dir.is_dir():
            continue
            
        print(f"\n🔄 Починаємо мердж для категорії: {category_name.upper()}")
        print("-" * 60)
        
        unique_tracks = {}
        master_header = None
        
        # Проходимося по підкатегоріях (наприклад, rainy, cloudy)
        for subcategory_dir in category_dir.iterdir():
            if not subcategory_dir.is_dir():
                continue
                
            label = subcategory_dir.name
            
            for csv_file in subcategory_dir.glob("*.csv"):
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        lines = list(reader)
                        
                        if not lines:
                            continue
                            
                        header_idx = -1
                        song_idx = -1
                        artist_idx = -1
                        
                        # Шукаємо хедер
                        for i, row in enumerate(lines):
                            if 'Song' in row and 'Artist' in row:
                                header_idx = i
                                song_idx = row.index('Song')
                                artist_idx = row.index('Artist')
                                
                                if master_header is None:
                                    master_header = row
                                break
                                
                        if header_idx == -1:
                            continue
                            
                        # Зчитуємо треки
                        for row in lines[header_idx + 1:]:
                            if not row or len(row) <= max(song_idx, artist_idx):
                                continue
                                
                            song_name = row[song_idx].strip()
                            artist_name = row[artist_idx].strip()
                            
                            if song_name and artist_name:
                                track_key = (song_name, artist_name)
                                
                                if track_key not in unique_tracks:
                                    unique_tracks[track_key] = {
                                        'row': row,
                                        'labels': [label]
                                    }
                                else:
                                    if label not in unique_tracks[track_key]['labels']:
                                        unique_tracks[track_key]['labels'].append(label)
                                        
                except Exception as e:
                    print(f"  [!] Помилка читання {csv_file.name}: {e}")
                    
        if not unique_tracks:
            print(f"⚠️ Немає даних для об'єднання в категорії {category_name}.")
            continue
            
        output_file = output_dir / f"{category_name}.csv"
        
        label_col_name = f"{category_name.capitalize()}_Label"
        final_header = master_header + [label_col_name]
        
        conflicts_count = 0
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(final_header)
            
            for (song, artist), data in unique_tracks.items():
                labels = data['labels']
                chosen_label = labels[0]
                
                if len(labels) > 1:
                    conflicts_count += 1
                    chosen_label = random.choice(labels)
                    print(f"🔀 Конфлікт: '{song}' - '{artist}' знайдено в {labels}. Обрано рандомно: '{chosen_label}'")
                    
                final_row = data['row'] + [chosen_label]
                writer.writerow(final_row)
                
        print(f"\n✅ Датасет '{output_file.name}' створено!")
        print(f"   Всього унікальних треків: {len(unique_tracks)}")
        print(f"   Конфліктів вирішено: {conflicts_count}")
        print("-" * 60)
        
        # НОВЕ: Додаємо конфлікти цієї категорії до загальної суми
        total_conflicts_all_categories += conflicts_count

    # НОВЕ: Фінальний вивід загальної статистики
    print(f"\n🎉 Всі етапи завершено!")
    print(f"🔥 ЗАГАЛЬНА КІЛЬКІСТЬ ВИРІШЕНИХ КОНФЛІКТІВ: {total_conflicts_all_categories}")
    print("=" * 60 + "\n")

# Запуск!
merge_datasets()