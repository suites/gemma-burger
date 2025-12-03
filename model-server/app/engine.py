# model-server/app/engine.py

from mlx_lm import generate, load

# 사용할 모델 ID (Hugging Face Hub 기준)
# 4bit 양자화된 모델을 사용하여 메모리를 절약하고 속도를 높입니다.
MODEL_ID = (
    "google/gemma-3-4b-it"  # 혹은 "mlx-community/gemma-3-4b-it-4bit" 등을 사용 가능
)


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
        self, prompt: str, max_tokens: int = 200, temp: float = 0.7
    ) -> str:
        """
        주어진 프롬프트에 대해 텍스트를 생성합니다.
        """
        if not self.model:
            raise RuntimeError("Model is not loaded!")

        # MLX-LM의 generate 함수는 매우 최적화되어 있습니다.
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temp,
            verbose=True,  # 터미널에 생성 과정을 출력 (디버깅용)
        )
        return response


# 싱글톤 패턴처럼 전역 인스턴스로 관리 (FastAPI 시작 시 로드)
engine = LLMEngine()
