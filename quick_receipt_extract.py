# 2. 单文件脚本 quick_receipt_extract.py
from paddleocr import PaddleOCR
import re, json, sys

IMG = sys.argv[1]          # receipt.jpg
LANG = 'en'                # 中文收据用 'ch'

# --- OCR ---
ocr = PaddleOCR(lang=LANG, use_angle_cls=True, show_log=False)
raw = ocr.ocr(IMG, cls=True)

lines = [''.join([w[0] for w in line]) for line in sum(raw, [])]

# --- 粗提取 ---
def find(patterns):
    for l in lines:
        for p in patterns:
            m = re.search(p, l, re.I)
            if m: return m.group(1) if m.groups() else l
    return None

info = {
    'date':  find([r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
                   r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})']),
    'total': find([r'(?:grand\s*)?total[^0-9]*([\d,]+\.\d{2})',
                   r'amount\s+due[^0-9]*([\d,]+\.\d{2})'])
}

# --- 明细行（示例规则：左边是商品，右边是价格）---
detail = []
for l in lines:
    m = re.match(r'(.+?)\s+([\d,]+\.\d{2})$', l)
    if m: detail.append({'item': m.group(1).strip(), 'price': m.group(2)})

info['items'] = detail
print(json.dumps(info, ensure_ascii=False, indent=2))

