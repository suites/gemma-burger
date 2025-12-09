## Fine-tuning

resources/fine_tuning 폴더의 학습용 데이터셋과 검증용 데이터셋으로 학습을 진행합니다.

### 데이터 준비

Hugging Face의 Chat Templates 형태로 데이터를 준비합니다.
https://huggingface.co/docs/transformers/chat_templating

```json
{
  "messages": [
    { "role": "user", "content": "Hi there!" },
    {
      "role": "assistant",
      "content": "Hello! Welcome to Gemma Burger! 🍔 How can I help you today? 😋"
    }
  ]
}
```

- LoRA (Low-Rank Adaptation)
  - LLM을 효율적으로 학습시키기 위한 경량화 파인튜닝 기법
  - 기존의 파인튜닝은 모델의 모든 파라미터 (Gemma 2B의 경우 약 26억개)를 전부 업데이트 했습니다.
    - VRAM이 엄청나게 필요하고 학습시간이 오래 걸립니다.
  - LoRA는 다음과 같은 특징을 가지고 있습니다.
    - LLM의 파라미터를 Freeze합니다.
    - 옆에 작은 행렬을 붙여서 학습합니다.
    - 모델의 일부 파라미터만 업데이트하여 메모리 사용량을 줄입니다.
    - 학습 시간을 단축할 수 있습니다.

$$W_{new} = W_{old} + \Delta W = W_{old} + (A \times B)$$

- $W_{old}$: 원래 모델의 가중치 ($d \times d$ 행렬, 고정됨)
- $A, B$: 학습 가능한 작은 행렬들 ($d \times r$, $r \times d$)
- $r$ (Rank): 우리가 설정 파일(lora_config.yaml)에서 **rank: 8**로 설정한 값입니다. 이 숫자가 작을수록 학습할 양이 줄어듭니다.

### Train

```bash
poetry run mlx_lm.lora --config lora_config.yaml --train
```

학습이 끝나면 데이터는 adapters 폴더에 저장됩니다.

```bash
|
└── adapters
    └── 0000600_adapters.safetensors
    └── adapter_config.json
    ├── adapters.safetensors
```
