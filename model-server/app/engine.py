from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

# 사용할 모델 ID (Hugging Face Hub 기준)
# 4bit 양자화된 모델을 사용하여 메모리를 절약하고 속도를 높입니다.
MODEL_ID = "mlx-community/gemma-3-4b-it-4bit"  # 혹은 "mlx-community/gemma-3-4b-it-4bit" 등을 사용 가능


class LLMEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        print(f"🚀 Loading model: {MODEL_ID}...")

        # 모델과 토크나이저 로드 (최초 1회 실행 시 자동 다운로드됨)
        # tokenizer_config={"trust_remote_code": True}가 필요할 수 있음
        self.model, self.tokenizer = load(MODEL_ID)
        print("✅ Model loaded successfully!")

    def generate_text(
        self, prompt: str, max_tokens: int = 200, temperature: float = 0.7
    ) -> str:
        if not self.model:
            raise RuntimeError("Model is not loaded!")

        messages = [{"role": "user", "content": prompt}]

        # 예: "hello" -> "<start_of_turn>user\nhello<end_of_turn>\n<start_of_turn>model\n"
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


# 싱글톤 패턴처럼 전역 인스턴스로 관리 (FastAPI 시작 시 로드)
engine = LLMEngine()
