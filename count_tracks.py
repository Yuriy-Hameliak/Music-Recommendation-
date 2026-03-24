import os
from pathlib import Path

path = r"C:\BA\ML\Project\dataset"

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
                    subcategory_total = 0

                    # Шукаємо всі CSV файли в підкатегорії
                    for csv_file in subcategory_dir.glob("*.csv"):
                        try:
                            # Відкриваємо файл і рахуємо рядки
                            with open(csv_file, 'r', encoding='utf-8') as f:
                                # sum(1 for line in f) рахує всі рядки, -1 відкидає рядок з назвами колонок
                                row_count = sum(1 for _ in f) - 1
                                if row_count > 0:
                                    subcategory_total += row_count
                        except Exception as e:
                            print(f"  [!] Failed to read {csv_file.name}: {e}")
                    
                    subcategory_stats.append((subcategory_name, subcategory_total))
                    category_total += subcategory_total
            
            # Гарний вивід результатів для поточної категорії
            print(f"Category: {category_name.upper()} | Overall tracks: {category_total}")
            for sub_name, sub_total in subcategory_stats:
                print(f"   └── 📂 {sub_name}: {sub_total} rows")
            print("–" * 50)
            
            grand_total_rows += category_total

    # Фінальний підрахунок
    print(f"Overall # of tracks: {grand_total_rows}")
    print("=" * 50 + "\n")

# --- Як використовувати ---
# Просто встав шлях до своєї головної папки сюди:
# folder_path = r"C:\Users\Andriy\Documents\Spotify_Dataset" 
# analyze_dataset_structure(folder_path)

analyze_dataset_structure()