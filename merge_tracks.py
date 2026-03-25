import pandas as pd
from pathlib import Path

dataset_path = Path("dataset")
output_path = Path(".")
categories = ["season", "time", "weather"]

df_list = []

print("Починаємо збір даних через Pandas...")

for category in categories:
    cat_dir = dataset_path / category
    if not cat_dir.exists():
        continue
        
    for subcat_dir in cat_dir.iterdir():
        if not subcat_dir.is_dir():
            continue
            
        subcat = subcat_dir.name
        
        for csv_file in subcat_dir.glob("*.csv"):
            try:
                # Зчитуємо файл, пропускаючи пошкоджені рядки
                temp_df = pd.read_csv(csv_file, on_bad_lines='skip', low_memory=False)
                
                if 'Song' not in temp_df.columns or 'Artist' not in temp_df.columns:
                    continue
                    
                # Беремо лише першого виконавця
                temp_df['Artist'] = temp_df['Artist'].astype(str).apply(lambda x: x.split(',')[0].strip())
                
                # Додаємо мітки
                temp_df['Category'] = category
                temp_df['Subcategory'] = subcat
                
                df_list.append(temp_df)
            except Exception as e:
                print(f"Помилка з файлом {csv_file.name}: {e}")

if not df_list:
    print("Не знайдено валідних даних для об'єднання.")
else:
    # Об'єднуємо всі таблиці
    full_df = pd.concat(df_list, ignore_index=True)
    
    # Вирішення конфліктів: перемішуємо і видаляємо дублікати за ключем (Song, Artist, Category)
    full_df = full_df.sample(frac=1, random_state=42).reset_index(drop=True)
    final_df = full_df.drop_duplicates(subset=['Song', 'Artist', 'Category'], keep='first')
    
    # Зберігаємо чистий файл
    output_file = output_path / "all_tracks_merged.csv"
    final_df.to_csv(output_file, index=False)
    
    print(f"Фінальний датасет успішно створено!")
    print(f"Всього рядків записано: {len(final_df)}")