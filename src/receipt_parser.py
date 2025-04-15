import openai
import base64
import os
import sys
import json

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def analyze_receipt(image_path):
    # 从系统环境变量中获取 OPENAI_API_KEY
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    openai.api_key = api_key

    base64_image = encode_image_to_base64(image_path)

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Please analyze this receipt image and extract the following information in structured JSON:\n"
                            "- Store name and address\n"
                            "- Date and time\n"
                            "- Cashier/operator name\n"
                            "- A list of purchased items (name, quantity if available, price)\n"
                            "- Subtotal, tax (with breakdown), and total\n"
                            "- Total number of items\n"
                            "Output in English and in valid JSON format."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )

    result = response.choices[0].message.content
    print(result)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python receipt_parser.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    analyze_receipt(image_path)
