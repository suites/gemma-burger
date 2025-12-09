import os
import re
import subprocess
import sys

import mlflow

# MLflow 서버 주소 (5001번 포트 확인!)
MLFLOW_TRACKING_URI = "http://localhost:5001"
EXPERIMENT_NAME = "Gemma-Burger-FineTuning"

# MinIO(S3) 설정
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"


def train_and_log():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    print("🚀 Starting training wrapper...")

    with mlflow.start_run() as run:
        mlflow.log_param("model", "gemma-3-4b-it-4bit")
        mlflow.log_param("method", "LoRA")

        # [핵심 변경 1] 환경변수 설정
        # PYTHONUNBUFFERED: 파이썬 출력 버퍼링 끄기
        # TQDM_DISABLE: 진행 바 끄기 (로그 막힘 방지)
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["TQDM_DISABLE"] = "1"

        # 프로세스 실행
        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "mlx_lm.lora",
                "--config",
                "lora_config.yaml",
                "--train",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # stderr도 stdout으로 합쳐서 받음
            text=True,
            bufsize=1,  # 라인 버퍼링
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )

        print("📊 Process started. Waiting for logs...")

        # 정규표현식 컴파일
        iter_pattern = re.compile(r"Iter (\d+):")
        train_loss_pattern = re.compile(r"Train loss (\d+\.\d+)")
        val_loss_pattern = re.compile(r"Val loss (\d+\.\d+)")

        # [핵심 변경 2] for 문 대신 while 문 사용
        # readline()으로 한 줄씩 읽고 즉시 출력
        while True:
            line = process.stdout.readline()

            # 프로세스가 종료되었고 더 이상 읽을 라인이 없으면 탈출
            if not line and process.poll() is not None:
                break

            if line:
                # 터미널에 즉시 출력 (공백 제거 후 출력)
                print(line.strip())

                # MLflow 메트릭 파싱
                iter_match = iter_pattern.search(line)
                if iter_match:
                    step = int(iter_match.group(1))

                    train_match = train_loss_pattern.search(line)
                    if train_match:
                        mlflow.log_metric(
                            "train_loss", float(train_match.group(1)), step=step
                        )

                    val_match = val_loss_pattern.search(line)
                    if val_match:
                        mlflow.log_metric(
                            "val_loss", float(val_match.group(1)), step=step
                        )

        # 종료 코드 확인
        if process.returncode == 0:
            print("\n✅ Training finished successfully!")

            adapter_dir = os.path.join(os.path.dirname(__file__), "..", "adapters")
            if os.path.exists(adapter_dir):
                print("📦 Uploading artifacts to MLflow...")
                mlflow.log_artifacts(adapter_dir, artifact_path="lora_adapter")
        else:
            print(f"\n❌ Training failed with code {process.returncode}")
            sys.exit(process.returncode)


if __name__ == "__main__":
    train_and_log()
