"""裁切 RPG Maker MZ 頭像面板第一格 (144x144) 到前端 public/images/faces/"""
from pathlib import Path
from PIL import Image

FACES_DIR = Path("Consilience/img/faces")
OUTPUT_DIR = Path("consilience-web/frontend/public/images/faces")

# Face 檔名 → 角色 slug 映射
FACE_MAP = {
    "Face1_東方啟": "dongfang-qi",
    "Face2_湮菲花": "yan-feihua",
    "Face3_闕崇陽": "que-chongyang",
    "Face4_絲塔娜": "sitana",
    "Face5_染幽": "ran-you",
    "Face6_藍靜冥": "lan-jingming",
    "Face7_楊古晨": "yang-guchen",
    "Face8_司徒長生": "situ-changsheng",
    "Face9_無名丐": "wuming-gai",
    "Face10_聶思泠": "nie-siling",
    "Face11_郭霆黃": "guo-ting",
    "Face12_墨汐若": "mo-xiruo",
    "Face13_沅花": "yuan-hua",
    "Face14_談笑": "tan-xiao",
    "Face17_珞堇": "luo-jin",
    "Face21_七霜": "qi-shuang",
    "Face23_瑤琴劍": "yaoqin-jian",
    "Face24_莫縈懷": "mo-yinghuai",
    "Face25_黃凱竹": "huang-kaizhu",
    "Face26_劉靜靜": "liu-jingjing",
    "Face7_白沫檸": "bai-moning",
    "Face22_龍玉": "long-yu",
    "Face50_青兒": "qing-er",
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for face_name, slug in FACE_MAP.items():
    src = FACES_DIR / f"{face_name}.png"
    if not src.exists():
        print(f"  SKIP {face_name} — 檔案不存在")
        continue

    img = Image.open(src)
    w, h = img.size
    cell_w = w // 4
    cell_h = h // 2

    # 裁切左上角第一格
    face = img.crop((0, 0, cell_w, cell_h))
    out = OUTPUT_DIR / f"{slug}.png"
    face.save(out, "PNG")
    print(f"  OK {slug}.png ({cell_w}x{cell_h})")

print(f"\n完成！共產出 {len(list(OUTPUT_DIR.glob('*.png')))} 張頭像")
