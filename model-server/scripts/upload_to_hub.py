from huggingface_hub import HfApi, create_repo

# 1. 설정
ADAPTER_PATH = "adapters"  # 로컬 어댑터 폴더 경로
# 업로드할 저장소 이름 (본인의 Hugging Face 사용자명으로 변경하세요!)
# 예: "fred/gemma-2-2b-burger-chat-adapter"
REPO_ID = "fredisbusy/gemma-3-4b-gemma-burger"


def upload():
    print(f"🚀 Preparing to upload '{ADAPTER_PATH}' to '{REPO_ID}'...")

    api = HfApi()

    # 2. 저장소 생성 (없으면 생성, 있으면 무시)
    try:
        create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True)
        print(f"✅ Repository '{REPO_ID}' is ready.")
    except Exception as e:
        print(f"⚠️ Warning during repo creation: {e}")

    # 3. 폴더 전체 업로드
    print("📦 Uploading adapter files...")
    try:
        api.upload_folder(
            folder_path=ADAPTER_PATH,
            repo_id=REPO_ID,
            repo_type="model",
            commit_message="Upload LoRA adapter trained with MLX",
        )
        print("✅ Upload complete!")
        print(f"🔗 Check your model here: https://huggingface.co/{REPO_ID}")

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print(
            "💡 Hint: 'huggingface-cli login'을 실행하여 인증 토큰이 있는지 확인해주세요."
        )


if __name__ == "__main__":
    upload()
