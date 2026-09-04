from paddleocr import PaddleOCR
from pathlib import Path
import json

image = Path("uploads/kurkurelabel.jpg")

ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv5",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
    enable_mkldnn=False,
)

result = ocr.predict(str(image))

for i, page in enumerate(result):
    print("\n========== PAGE", i, "==========")
    data = page.json
    print(json.dumps(data, indent=2, ensure_ascii=False))

print("\nDONE")
