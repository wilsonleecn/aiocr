import openai
import base64
import os
import sys
import json
import re

# 使用 GPT-4 Turbo 分析收据图像

# 强制统一 JSON 键名（通过 Prompt 限定 + 后处理标准化）

# 稳定提取 items，不论 key 是否被乱写

# 使用正则提取 JSON 区块

# 自动猜测商品全称和品牌名

# 打印 token 用量和费用估算

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    openai.api_key = api_key
    return openai


def extract_json_block(text):
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return None


def normalize_keys(data):
    """Standardize possible variations of JSON keys."""
    mapping = {
        "Items": "items",
        "Purchased Items": "items",
        "products": "items",
        "Date": "datetime",
        "date": "datetime",
        "store_info": "store",
        "Store Info": "store",
        "Cashier": "cashier",
        "Total Items": "total_items"
    }

    normalized = {}
    for key, value in data.items():
        std_key = mapping.get(key.strip(), key.strip())
        normalized[std_key] = value
    return normalized


def analyze_receipt_image(openai, base64_image):
    print("📷 Analyzing receipt image...")

    strict_prompt = (
        "Please analyze this receipt image and extract the information below "
        "using **exactly** these keys. Do not change key names. Return valid JSON only:\n\n"
        "{\n"
        "  \"store\": {\"name\": string, \"address\": string},\n"
        "  \"datetime\": string,\n"
        "  \"cashier\": string,\n"
        "  \"items\": [\n"
        "    {\"name\": string, \"quantity\": optional number, \"price\": number}\n"
        "  ],\n"
        "  \"subtotal\": number,\n"
        "  \"tax\": {\"total\": number, \"breakdown\": optional object},\n"
        "  \"total\": number,\n"
        "  \"total_items\": number\n"
        "}\n\n"
        "Respond with only valid JSON. No explanations or extra text."
    )

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": strict_prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }}
                ]
            }
        ],
        max_tokens=1000
    )
    return response


def guess_full_product_names(openai, abbreviated_items):
    prompt_dict = {item["name"]: None for item in abbreviated_items if item.get("name")}
    if not prompt_dict:
        print("⚠️ No abbreviated item names found for guessing.")
        return

    print("\n🔍 Guessing full product names...")
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": (
                    "These are abbreviated item names from a receipt. "
                    "Please guess their full product names and brand. "
                    "Respond only with valid JSON:\n\n"
                    + json.dumps(prompt_dict, indent=2)
                )
            }
        ],
        max_tokens=700
    )

    raw_text = response.choices[0].message.content
    json_block = extract_json_block(raw_text)

    print("\n🧠 Guessed Full Product Names:\n")
    if json_block:
        try:
            guesses = json.loads(json_block)
            print(json.dumps(guesses, indent=2))
        except Exception as e:
            print("⚠️ Could not parse guess JSON:", e)
            print("Raw guess output:\n", raw_text)
    else:
        print("⚠️ Could not find valid JSON block in guess response.")
        print("Raw guess output:\n", raw_text)


def analyze_receipt(image_path):
    openai_client = get_openai_client()
    base64_image = encode_image_to_base64(image_path)

    response = analyze_receipt_image(openai_client, base64_image)

    result_text = response.choices[0].message.content
    usage = response.usage

    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    input_cost = input_tokens * 0.01 / 1000
    output_cost = output_tokens * 0.03 / 1000
    total_cost = input_cost + output_cost

    print("\n--- Token Usage & Cost ---")
    print(f"Input tokens:    {input_tokens}")
    print(f"Output tokens:   {output_tokens}")
    print(f"Total tokens:    {total_tokens}")
    print(f"Estimated cost:  ${total_cost:.6f} USD")

    json_str = extract_json_block(result_text)
    if not json_str:
        print("\n❌ Could not find valid JSON in GPT response.\nRaw content:\n", result_text)
        return

    try:
        result_json = json.loads(json_str)
        normalized_result = normalize_keys(result_json)

        print("\n🧾 Receipt Data:\n")
        print(json.dumps(normalized_result, indent=2))

        items = normalized_result.get("items", [])
        if items:
            guess_full_product_names(openai_client, items)

    except Exception as e:
        print("\n❌ Failed to parse or normalize JSON:", e)
        print("Raw JSON text:\n", json_str)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_receipt.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    analyze_receipt(image_path)
