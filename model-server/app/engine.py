import os

import mlx.core as mx
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

# GPU 강제 사용
mx.set_default_device(mx.gpu)

MODEL_ID = "mlx-community/gemma-2-2b-it-4bit"


class LLMEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        print(f"🚀 Loading model: {MODEL_ID}...")

        # model-server/adapters 폴더를 가리킵니다.
        adapter_path = "adapters"

        # 어댑터 파일이 실제로 있는지 확인
        if os.path.exists(adapter_path):
            print(f"✨ Found adapter at '{adapter_path}'. Loading with LoRA...")
            self.model, self.tokenizer = load(MODEL_ID, adapter_path=adapter_path)
        else:
            print("⚠️ Adapter not found. Loading base model only.")
            self.model, self.tokenizer = load(MODEL_ID)

        print("✅ Model loaded successfully!")

    def generate_text(
        self, prompt: str, max_tokens: int = 200, temperature: float = 0.7
    ) -> str:
        if not self.model:
            raise RuntimeError("Model is not loaded!")

        messages = [{"role": "user", "content": prompt}]
        prompt_formatted = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt_formatted,
            max_tokens=max_tokens,
            sampler=make_sampler(temp=temperature),
            verbose=True,
        )
        return response


engine = LLMEngine()
