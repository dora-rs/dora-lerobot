from dora import Node
import pyarrow as pa
from transformers import AutoProcessor, AutoModelForVision2Seq, AwqConfig
import torch
import gc
from transformers import BitsAndBytesConfig

import os


IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "480"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "640"))


quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)
model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceM4/idefics2-8b",
    torch_dtype=torch.float16,
    quantization_config=quantization_config,
)
processor = AutoProcessor.from_pretrained("HuggingFaceM4/idefics2-8b-base")


def ask_vlm(image, instruction):
    global model
    # Create inputs
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {
                    "type": "text",
                    "text": f"You are a humanoid robot named reachy built by pollen robotics. You have two arms with hands. Respond by being very descriptive and positive. {instruction}",
                },
            ],
        },
    ]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image], return_tensors="pt")
    inputs = {k: v.to("cuda") for k, v in inputs.items()}
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=250,
    )
    generated_texts = processor.batch_decode(generated_ids, skip_special_tokens=True)

    gc.collect()
    torch.cuda.empty_cache()
    return generated_texts[0].split("\nAssistant: ")[1]


# print(ask_vlm(image, "Can you give me a high five?"))
node = Node()
image = None
text = None
from PIL import Image

for event in node:
    if event["type"] == "INPUT":
        if event["id"] == "image":
            image = event["value"].to_numpy().reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
            # You may need to convert the color.
            image = Image.fromarray(image)
        elif event["id"] == "text":

            text = event["value"][0].as_py()
            output = ask_vlm(image, text).lower()
            print(output)
            node.send_output(
                "speak",
                pa.array([output]),
            )
