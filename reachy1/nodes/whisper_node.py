import pyarrow as pa
from pynput import keyboard
from pynput.keyboard import Key, Events
from dora import Node

import torch
import numpy as np
import pyarrow as pa
import sounddevice as sd
import gc  # garbage collect library


from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "distil-whisper/distil-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    torch_dtype=torch_dtype,
    device=device,
)
SAMPLE_RATE = 16000
MAX_DURATION = 30

policy_init = True
audio_data = None
node = Node()

for dora_event in node:
    if dora_event["type"] == "INPUT":
        ## Check for keyboard event
        with keyboard.Events() as events:
            event = events.get(1.0)
            if (
                event is not None
                and (event.key == Key.alt_r)
                and isinstance(event, Events.Press)
            ):
                ## Stop the previous recording
                node.send_output("stop", pa.array([]))

                ## Stop the previous Sound
                node.send_output("stop", pa.array([]))
                
                ## Microphone
                audio_data = sd.rec(
                    int(SAMPLE_RATE * MAX_DURATION),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype=np.int16,
                    blocking=False,
                )

            elif (
                event is not None
                and event.key == Key.alt_r
                and isinstance(event, Events.Release)
            ):
                sd.stop()
                if audio_data is None:
                    continue
                audio = audio_data.ravel().astype(np.float32) / 32768.0

                ## Speech to text
                result = pipe(audio)
                # result = model.transcribe(audio, language="en")
                node.send_output(
                    "text_llm", pa.array([result["text"]]), dora_event["metadata"]
                )
                # send_output("led", pa.array([0, 0, 255]))

                gc.collect()
                torch.cuda.empty_cache()
