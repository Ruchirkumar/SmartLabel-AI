from paddleocr import PaddleOCR
import json

ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv5",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
    enable_mkldnn=False,
)

result = ocr.predict("uploads/kurkurelabel.jpg")

for page in result:
    print(json.dumps(page.json, ensure_ascii=False, indent=2))
