import openai
import base64
import os
import sys
import json
import re


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
    """Tries to extract a JSON block from text using regex."""
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return None


def analyze_receipt_image(openai, base64_image):
    print("📷 Analyzing receipt image...")

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "This is a photo of a Costco receipt. "
                            "Please extract the following in **valid JSON** format:\n"
                            "- Store name and address\n"
                            "- Date and time\n"
                            "- Cashier/operator name\n"
                            "- A list of purchased items (name, quantity if available, price)\n"
                            "- Subtotal, tax (with breakdown), and total\n"
                            "- Total number of items\n\n"
                            "Respond with JSON only. No explanations or headings. Return a valid JSON object."
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
                    "These are abbreviated item names from a Costco receipt. "
                    "Please guess their full product names and brand. "
                    "Respond only with valid JSON (no extra comments or explanations):\n\n"
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

    # Step 1: Analyze receipt
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

    # Step 2: Extract JSON block
    json_str = extract_json_block(result_text)
    if not json_str:
        print("\n❌ Could not find valid JSON in GPT response.\nRaw content:\n", result_text)
        return

    try:
        result_json = json.loads(json_str)
        print("\n🧾 Receipt Data:\n")
        print(json.dumps(result_json, indent=2))

        # Step 3: Guess product names
        items = result_json.get("items", [])
        if items:
            guess_full_product_names(openai_client, items)

    except Exception as e:
        print("\n❌ Failed to parse extracted JSON:", e)
        print("Raw JSON text:\n", json_str)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_receipt.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    analyze_receipt(image_path)
