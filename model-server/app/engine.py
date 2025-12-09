import os

import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

mx.set_default_device(mx.gpu)

MODEL_ID = "mlx-community/gemma-3-4b-it-4bit"


class LLMEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        print(f"🚀 Loading model: {MODEL_ID}...")

        adapter_path = "adapters"

        if os.path.exists(adapter_path):
            print(f"✨ Found adapter at '{adapter_path}'. Loading with LoRA...")
            self.model, self.tokenizer = load(MODEL_ID, adapter_path=adapter_path)
        else:
            print("⚠️ Adapter not found. Loading base model only.")
            self.model, self.tokenizer = load(MODEL_ID)

        print("✅ Model loaded successfully!")

    def generate_text_stream(
        self, prompt: str, max_tokens: int = 200, temperature: float = 0.7
    ):
        """
        텍스트 생성 결과를 실시간으로 yield 하는 제너레이터 함수
        """
        if not self.model:
            raise RuntimeError("Model is not loaded!")

        messages = [{"role": "user", "content": prompt}]
        prompt_formatted = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # stream_generate 함수 사용
        # 이 함수는 (token, text) 튜플을 yield 합니다.
        stream = stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt_formatted,
            max_tokens=max_tokens,
            sampler=make_sampler(temp=temperature),
        )

        for response in stream:
            # response.text에 새로 생성된 텍스트 조각이 들어있습니다.
            # 이것을 바로바로 yield 하여 호출자에게 전달합니다.
            yield response.text


engine = LLMEngine()
