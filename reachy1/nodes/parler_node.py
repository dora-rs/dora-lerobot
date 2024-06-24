from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import pygame
from dora import Node
import pyarrow as pa

model = ParlerTTSForConditionalGeneration.from_pretrained(
    "ylacombe/parler-tts-mini-jenny-30H"
).to("cuda:0")
tokenizer = AutoTokenizer.from_pretrained("ylacombe/parler-tts-mini-jenny-30H")

pygame.mixer.init()

input_ids = tokenizer(
    "Jenny delivers her words quite expressively, in a very confined sounding environment with clear audio quality.",
    return_tensors="pt",
).input_ids.to("cuda:0")

generation = model.generate(
    input_ids=input_ids,
    min_new_tokens=100,
    #   max_length=350,
    prompt_input_ids=tokenizer(["abc"], return_tensors="pt").input_ids.to("cuda:0"),
)
node = Node()
for event in node:
    if event["type"] == "INPUT":
        text = event["value"][0].as_py()
        print(text)
        generation = model.generate(
            input_ids=input_ids,
            min_new_tokens=100,
            #   max_length=350,
            prompt_input_ids=tokenizer(text, return_tensors="pt").input_ids.to(
                "cuda:0"
            ),
        )
        sf.write(
            "parler_tts_out.wav",
            generation.cpu().numpy().squeeze(),
            model.config.sampling_rate,
        )

        pygame.mixer.music.load("parler_tts_out.wav")
        pygame.mixer.music.play()
        while pygame.mixer.get_busy():
            pass

        text = text.lower()
        if ("yes" in text or "sure" in text) and "high" in text and "five" in text:
            node.send_output(
                "start_high_five",
                pa.array([False]),
            )


# op = Operator()
# import pyarrow as pa

# op.on_event({"type": "INPUT", "value": pa.array(["Hello, how are you?"])}, None)
