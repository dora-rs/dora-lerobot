import math
from queue import Queue
from threading import Thread
from typing import Optional
from dora import Node

import numpy as np
import torch
import time
import pyaudio

from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer, AutoFeatureExtractor, set_seed, StoppingCriteria, StoppingCriteriaList
from transformers.generation.streamers import BaseStreamer

device = "cuda:0" #if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
torch_dtype = torch.float16 if device != "cpu" else torch.float32

repo_id = "ylacombe/parler-tts-mini-jenny-30H"

model = ParlerTTSForConditionalGeneration.from_pretrained(
    repo_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True
).to(device)

tokenizer = AutoTokenizer.from_pretrained(repo_id)
feature_extractor = AutoFeatureExtractor.from_pretrained(repo_id)

SAMPLE_RATE = feature_extractor.sampling_rate
SEED = 42

default_text = "Hello, my name is Reachy the best robot in the world !"
default_description = "Speaks in a crystal clear female voice."
init_sleep = True


p = pyaudio.PyAudio()

class ParlerTTSStreamer(BaseStreamer):
    def __init__(
        self,
        model: ParlerTTSForConditionalGeneration,
        device: Optional[str] = None,
        play_steps: Optional[int] = 10,
        stride: Optional[int] = None,
        timeout: Optional[float] = None,
    ):
        """
        Streamer that stores playback-ready audio in a queue, to be used by a downstream application as an iterator. This is
        useful for applications that benefit from accessing the generated audio in a non-blocking way (e.g. in an interactive
        Gradio demo).
        Parameters:
            model (`ParlerTTSForConditionalGeneration`):
                The Parler-TTS model used to generate the audio waveform.
            device (`str`, *optional*):
                The torch device on which to run the computation. If `None`, will default to the device of the model.
            play_steps (`int`, *optional*, defaults to 10):
                The number of generation steps with which to return the generated audio array. Using fewer steps will
                mean the first chunk is ready faster, but will require more codec decoding steps overall. This value
                should be tuned to your device and latency requirements.
            stride (`int`, *optional*):
                The window (stride) between adjacent audio samples. Using a stride between adjacent audio samples reduces
                the hard boundary between them, giving smoother playback. If `None`, will default to a value equivalent to
                play_steps // 6 in the audio space.
            timeout (`int`, *optional*):
                The timeout for the audio queue. If `None`, the queue will block indefinitely. Useful to handle exceptions
                in `.generate()`, when it is called in a separate thread.
        """
        self.decoder = model.decoder
        self.audio_encoder = model.audio_encoder
        self.generation_config = model.generation_config
        self.device = device if device is not None else model.device

        # variables used in the streaming process
        self.play_steps = play_steps
        if stride is not None:
            self.stride = stride
        else:
            hop_length = math.floor(self.audio_encoder.config.sampling_rate / self.audio_encoder.config.frame_rate)
            self.stride = hop_length * (play_steps - self.decoder.num_codebooks) // 6
        self.token_cache = None
        self.to_yield = 0

        # varibles used in the thread process
        self.audio_queue = Queue()
        self.stop_signal = None
        self.timeout = timeout

    def apply_delay_pattern_mask(self, input_ids):
        # build the delay pattern mask for offsetting each codebook prediction by 1 (this behaviour is specific to Parler)
        _, delay_pattern_mask = self.decoder.build_delay_pattern_mask(
            input_ids[:, :1],
            bos_token_id=self.generation_config.bos_token_id,
            pad_token_id=self.generation_config.decoder_start_token_id,
            max_length=input_ids.shape[-1],
        )
        # apply the pattern mask to the input ids
        input_ids = self.decoder.apply_delay_pattern_mask(input_ids, delay_pattern_mask)

        # revert the pattern delay mask by filtering the pad token id
        mask = (delay_pattern_mask != self.generation_config.bos_token_id) & (delay_pattern_mask != self.generation_config.pad_token_id)
        input_ids = input_ids[mask].reshape(1, self.decoder.num_codebooks, -1)
        # append the frame dimension back to the audio codes
        input_ids = input_ids[None, ...]

        # send the input_ids to the correct device
        input_ids = input_ids.to(self.audio_encoder.device)

        decode_sequentially = (
            self.generation_config.bos_token_id in input_ids
            or self.generation_config.pad_token_id in input_ids
            or self.generation_config.eos_token_id in input_ids
        )
        if not decode_sequentially:
            output_values = self.audio_encoder.decode(
                input_ids,
                audio_scales=[None],
            )
        else:
            sample = input_ids[:, 0]
            sample_mask = (sample >= self.audio_encoder.config.codebook_size).sum(dim=(0, 1)) == 0
            sample = sample[:, :, sample_mask]
            output_values = self.audio_encoder.decode(sample[None, ...], [None])

        audio_values = output_values.audio_values[0, 0]
        return audio_values.cpu().float().numpy()

    def put(self, value):
        batch_size = value.shape[0] // self.decoder.num_codebooks
        if batch_size > 1:
            raise ValueError("ParlerTTSStreamer only supports batch size 1")

        if self.token_cache is None:
            self.token_cache = value
        else:
            self.token_cache = torch.concatenate([self.token_cache, value[:, None]], dim=-1)

        if self.token_cache.shape[-1] % self.play_steps == 0:
            audio_values = self.apply_delay_pattern_mask(self.token_cache)
            self.on_finalized_audio(audio_values[self.to_yield : -self.stride])
            self.to_yield += len(audio_values) - self.to_yield - self.stride

    def end(self):
        """Flushes any remaining cache and appends the stop symbol."""
        if self.token_cache is not None:
            audio_values = self.apply_delay_pattern_mask(self.token_cache)
        else:
            audio_values = np.zeros(self.to_yield)

        self.on_finalized_audio(audio_values[self.to_yield :], stream_end=True)

    def on_finalized_audio(self, audio: np.ndarray, stream_end: bool = False):
        """Put the new audio in the queue. If the stream is ending, also put a stop signal in the queue."""
        self.audio_queue.put(audio, timeout=self.timeout)
        if stream_end:
            self.audio_queue.put(self.stop_signal, timeout=self.timeout)

    def __iter__(self):
        return self

    def __next__(self):
        value = self.audio_queue.get(timeout=self.timeout)
        if not isinstance(value, np.ndarray) and value == self.stop_signal:
            raise StopIteration()
        else:
            return value


sampling_rate = model.audio_encoder.config.sampling_rate
frame_rate = model.audio_encoder.config.frame_rate

stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sampling_rate,
                    output=True)

def play_audio(audio_array):
    
    if np.issubdtype(audio_array.dtype, np.floating):
        max_val = np.max(np.abs(audio_array))
        audio_array = (audio_array / max_val) * 32767
        audio_array = audio_array.astype(np.int16)
    
    stream.write(audio_array.tobytes())
    
class InterruptStoppingCriteria(StoppingCriteria):
    def __init__(self):
        self.stop_signal = False

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        return self.stop_signal

    def stop(self):
        self.stop_signal = True

def generate_base(node, text=default_text, description=default_description, play_steps_in_s=0.5, len_t = 60):
    global init_sleep
    play_steps = int(frame_rate * play_steps_in_s)
    streamer = ParlerTTSStreamer(model, device=device, play_steps=play_steps)
    inputs = tokenizer(description, return_tensors="pt").to(device)
    prompt = tokenizer(text, return_tensors="pt").to(device)
    
    stopping_criteria = InterruptStoppingCriteria()

    generation_kwargs = dict(
        input_ids=inputs.input_ids,
        prompt_input_ids=prompt.input_ids,
        streamer=streamer,
        do_sample=True,
        temperature=1.0,
        min_new_tokens=10,
        stopping_criteria=StoppingCriteriaList([stopping_criteria]),
    )
    set_seed(SEED)
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    prev_time = time.time()
    
    for new_audio in streamer:
        print("Playing")
        if init_sleep:
            print("Initialising")
            init_sleep = False
            time.sleep(len_t/60)
        
        current_time = time.time()
        print(f"Sample of length: {round(new_audio.shape[0] / sampling_rate, 2)} seconds")
        print(f"Time between iterations: {round(current_time - prev_time, 2)} seconds")
        prev_time = current_time
        play_audio(new_audio)
        event = node.next(timeout=0.01)
        print(event["type"])
        if event["type"] == "ERROR":
            pass
        elif event["type"] == "INPUT":
            if event["id"] == "stop":
                stopping_criteria.stop()
                break

node = Node()
while True:
    event = node.next()
    if event is None:
        break
    if event["type"] == "INPUT" and event["id"] == "text":
        text = event["value"][0].as_py()
        generate_base(node, text, default_description, 1, len(text) + 1)

stream.stop_stream()
stream.close()
p.terminate()