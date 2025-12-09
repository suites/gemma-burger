from huggingface_hub import snapshot_download

# 1. 설정
DOWNLOAD_PATH = "adapters"  # 로컬 다운로드 경로
REPO_ID = "fredisbusy/gemma-3-4b-gemma-burger"


def download():
    print(f"🚀 Preparing to download '{REPO_ID}' to '{DOWNLOAD_PATH}'...")

    try:
        snapshot_download(
            repo_id=REPO_ID,
            local_dir=DOWNLOAD_PATH,
            local_dir_use_symlinks=False,  # 실제 파일 다운로드
            repo_type="model",
        )
        print("✅ Download complete!")
        print(f"📂 Files saved to: {DOWNLOAD_PATH}")

    except Exception as e:
        print(f"❌ Download failed: {e}")


if __name__ == "__main__":
    download()

