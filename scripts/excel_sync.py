import sys
import json
import os
import pandas as pd
from pathlib import Path

def export_to_excel(data_dir, output_file):
    data_dir = Path(data_dir)
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for json_file in data_dir.glob("*.json"):
            if not json_file.is_file(): continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading {json_file.name}: {e}")
                continue

            if not isinstance(data, list):
                continue  # skip objects like System.json

            rows = []
            for i, item in enumerate(data):
                if item is None:
                    continue
                row = {}
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        row[k] = json.dumps(v, ensure_ascii=False)[:32700]
                    else:
                        row[k] = v
                rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows)
                # Keep original column order, put id and name first if they exist
                cols = df.columns.tolist()
                first_cols = [c for c in ['id', 'name', 'description', 'note'] if c in cols]
                other_cols = [c for c in cols if c not in first_cols]
                df = df[first_cols + other_cols]
                
                sheet_name = json_file.stem[:31] # Excel limits sheet names to 31 chars
                try:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception as e:
                    print(f"Error writing sheet {sheet_name}: {e}")
                
    print(f"Exported to {output_file}")

def import_from_excel(excel_file, data_dir):
    data_dir = Path(data_dir)
    excel = pd.ExcelFile(excel_file)
    for sheet in excel.sheet_names:
        json_file = data_dir / f"{sheet}.json"
        
        # We only update files that exist
        if not json_file.exists():
            continue
            
        with open(json_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
            
        if not isinstance(original_data, list):
            continue
            
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.where(pd.notnull(df), None) # convert nan to None
        
        # Reconstruct list
        max_id = int(df['id'].max()) if 'id' in df.columns else len(df)
        new_data = [None] * (max_id + 1)
        
        # Keep original structure for unedited things, update from rows
        for idx, row in df.iterrows():
            # if 'id' missing, use index + 1
            item_id = int(row.get('id', idx + 1)) if row.get('id') is not None else idx + 1
            obj = {}
            # Base it off original if exists to preserve missing fields in excel
            if item_id < len(original_data) and original_data[item_id]:
                obj = original_data[item_id].copy()
                
            for k, v in row.items():
                if pd.isna(v) or v is None:
                    # In pandas, empty cells might be nan
                    continue
                if isinstance(v, str) and (v.startswith('[') or v.startswith('{')):
                    try:
                        obj[k] = json.loads(v)
                    except:
                        obj[k] = v
                else:
                    # Convert to appropriate type
                    if isinstance(v, float) and v.is_integer():
                        obj[k] = int(v)
                    else:
                        obj[k] = v
                        
            # Ensure ID stays integer
            if 'id' in obj and obj['id'] is not None:
                obj['id'] = int(obj['id'])
                
            # Expand new_data if needed
            if item_id >= len(new_data):
                new_data.extend([None] * (item_id - len(new_data) + 1))
                
            new_data[item_id] = obj
            
        # Write back
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, separators=(',', ':'))
            
    print(f"Imported from {excel_file}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python excel_sync.py [export|import] [data_dir] [excel_file]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    d_dir = sys.argv[2]
    e_file = sys.argv[3]
    
    if cmd == 'export':
        export_to_excel(d_dir, e_file)
    elif cmd == 'import':
        import_from_excel(e_file, d_dir)
