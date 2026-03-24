import os
import re
import shutil
from pathlib import Path

def sort_playlists(sort_folder, dataset_folder):
    sort_path = Path(sort_folder)
    dataset_path = Path(dataset_folder)

    # Перевіряємо, чи існує папка sort
    if not sort_path.exists() or not sort_path.is_dir():
        print(f"Error: folder '{sort_folder}' does not exist or is not a directory.")
        return

    # Словник з правилами сортування (шлях_призначення: [список_ключових_слів])
    # Використовуємо регулярні вирази, щоб ловити варіації (наприклад, rain, raining, rainy)
    rules = {
        # WEATHER
        "weather/cloudy": [r"cloud", r"cloudy", r"overcast", r"gloom"],
        "weather/rainy":  [r"rain", r"rainy", r"raining", r"drizzle", r"storm"],
        "weather/snow":   [r"snow", r"snowy", r"cold", r"freeze", r"ice"],
        "weather/sunny":  [r"sun", r"sunny", r"clear", r"bright"],
        
        # TIME
        "time/morning":   [r"morning", r"sunrise", r"wake\s*up", r"dawn"],
        "time/day":       [r"daytime", r"afternoon", r"midday", r"work"],
        "time/evening":   [r"evening", r"sunset", r"dusk", r"chill"],
        "time/night":     [r"night", r"midnight", r"late", r"sleep", r"dark"],
        
        # SEASON
        "season/spring":  [r"spring", r"bloom", r"march", r"april", r"may"],
        "season/summer":  [r"summer", r"beach", r"june", r"july", r"august"],
        "season/autumn":  [r"autumn", r"fall", r"september", r"october", r"november"],
        "season/winter":  [r"winter", r"cold", r"december", r"january", r"february"]
    }

    print("Starting to sort playlists...")
    processed_files = 0

    for file_path in sort_path.glob("*.csv"):
        filename_lower = file_path.name.lower()
        destinations = []

        # 1. Знаходимо всі папки, куди треба закинути файл
        for dest, keywords in rules.items():
            if any(re.search(kw, filename_lower) for kw in keywords):
                destinations.append(dest)

        if not destinations:
            print(f"⚠️ No matching category for '{file_path.name}', skipping.")
            continue

        # 2. Читаємо, чистимо і записуємо файл
        # 2. Читаємо, чистимо і записуємо файл
        # 2. Читаємо, чистимо і записуємо файл
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            header_idx = 0
            for i, line in enumerate(lines):
                if 'Song' in line and 'Artist' in line:
                    header_idx = i
                    break
            
            # Відрізаємо все до хедера і прибираємо пробіли на початку кожного рядка
            cleaned_lines = [line.lstrip() for line in lines[header_idx:]]

            # НОВИЙ ФІКС: якщо хедер починається з коми, додаємо #
            if cleaned_lines and cleaned_lines[0].startswith(','):
                cleaned_lines[0] = '#' + cleaned_lines[0]

            for dest in destinations:
                dest_dir = dataset_path / dest
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                dest_file = dest_dir / file_path.name
                with open(dest_file, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                print(f"Sorted '{file_path.name}' to '{dest_dir}'")

            # 3. Видаляємо оригінальний брудний файл
            file_path.unlink()
            print(f"Deleted original file: '{file_path.name}'")
            processed_files += 1

        except Exception as e:
            print(f"❌ Error processing '{file_path.name}': {e}")

    print(f"\n🎉 Done! Sorted files: {processed_files}")

# --- How to use ---
# Make sure the 'sort' folder is in the same directory as the script, or specify the full paths
sort_folder_path = "sort" 
dataset_folder_path = "dataset"
sort_playlists(sort_folder_path, dataset_folder_path)