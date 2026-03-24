import os
import re
from pathlib import Path

def sort_playlists(sort_folder, dataset_folder):
    sort_path = Path(sort_folder)
    dataset_path = Path(dataset_folder)

    if not sort_path.exists() or not sort_path.is_dir():
        print(f"❌ Error: folder '{sort_folder}' does not exist or is not a directory.")
        return

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

    print("🚀 Starting to sort playlists...\n")
    processed_files = 0

    for file_path in sort_path.glob("*.csv"):
        filename_lower = file_path.name.lower()
        destinations = []

        for dest, keywords in rules.items():
            if any(re.search(kw, filename_lower) for kw in keywords):
                destinations.append(dest)

        if not destinations:
            print(f"⚠️ No matching category for '{file_path.name}', skipping.\n")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            header_idx = 0
            for i, line in enumerate(lines):
                if 'Song' in line and 'Artist' in line:
                    header_idx = i
                    break
            
            cleaned_lines = [line.lstrip() for line in lines[header_idx:]]

            if cleaned_lines and cleaned_lines[0].startswith(','):
                cleaned_lines[0] = '#' + cleaned_lines[0]

            for dest in destinations:
                dest_dir = dataset_path / dest
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                dest_file = dest_dir / file_path.name
                
                # --- ЛОГІКА ПЕРЕВІРКИ ДУБЛІКАТІВ ---
                if dest_file.exists():
                    # Читаємо існуючий файл, щоб порівняти його з поточним
                    with open(dest_file, 'r', encoding='utf-8') as existing_f:
                        existing_lines = existing_f.readlines()
                        
                    if existing_lines == cleaned_lines:
                        print(f"⏭️ File '{file_path.name}' is IDENTICAL to the one in '{dest}'. Skipping save.")
                        continue # Пропускаємо збереження, але йдемо до наступної папки призначення
                    else:
                        # Файли відрізняються, шукаємо вільне ім'я
                        base_name = file_path.stem   # Назва без .csv
                        extension = file_path.suffix # Самий .csv
                        counter = 2
                        
                        while True:
                            new_name = f"{base_name} #{counter}{extension}"
                            dest_file = dest_dir / new_name
                            # Якщо такого файлу ще немає, виходимо з циклу
                            if not dest_file.exists():
                                break
                            counter += 1
                        
                        print(f"🔄 File '{file_path.name}' differs from existing. Saving as '{new_name}' in '{dest}'.")

                # Записуємо фінальний варіант
                with open(dest_file, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                print(f"✅ Sorted '{dest_file.name}' to '{dest}'")

            # Видаляємо оригінальний файл у будь-якому випадку (навіть якщо він був 100% дублікатом скрізь)
            file_path.unlink()
            print(f"🗑️ Deleted original file: '{file_path.name}'\n")
            processed_files += 1

        except Exception as e:
            print(f"❌ Error processing '{file_path.name}': {e}\n")

    print(f"🎉 Done! Processed files: {processed_files}")

# --- Запуск скрипта ---
sort_folder_path = "sort" 
dataset_folder_path = "dataset"
sort_playlists(sort_folder_path, dataset_folder_path)