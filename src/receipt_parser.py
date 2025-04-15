import openai
import base64
import os
import sys
import json

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
def analyze_receipt(image_path):
    import math

    # 获取 OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    openai.api_key = api_key

    # 图像转 base64
    base64_image = encode_image_to_base64(image_path)

    # 调用 GPT-4 Turbo 处理图像
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
                            "Output in valid JSON format."
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
    usage = response.usage

    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    # 计算费用（单位是美元）
    input_cost = input_tokens * 0.01 / 1000
    output_cost = output_tokens * 0.03 / 1000
    total_cost = input_cost + output_cost

    print("🧾 Receipt Analysis Result:\n")
    print(result)

    print("\n--- Token Usage & Cost ---")
    print(f"Input tokens:    {input_tokens}")
    print(f"Output tokens:   {output_tokens}")
    print(f"Total tokens:    {total_tokens}")
    print(f"Estimated cost:  ${total_cost:.6f} USD")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python receipt_parser.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    analyze_receipt(image_path)
