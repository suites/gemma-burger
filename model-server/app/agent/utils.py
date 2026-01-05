import os

import yaml


def load_yaml(filename):
    """프로젝트 루트 또는 리소스 폴더에서 YAML 파일을 찾습니다."""
    # 현재 파일(app/agent/utils.py) 기준으로 루트 경로 추적
    base_path = os.path.dirname(__file__)
    # 예: app/agent/ -> app/ -> root/
    project_root = os.path.abspath(os.path.join(base_path, "../../../"))

    path = os.path.join(project_root, filename)

    if not os.path.exists(path):
        # 혹시 resources 폴더에 있을 경우 대비
        path = os.path.join(project_root, "resources", filename)

    if not os.path.exists(path):
        print(f"⚠️ Warning: {filename} not found at {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 전역 설정 로드
PERSONAS = load_yaml("personas.yaml")
PROMPTS = load_yaml("prompts.yaml")


def build_prompt(persona_key, task_instruction, context_data, user_query):
    """prompts.yaml의 common 템플릿을 사용하여 프롬프트를 조립합니다."""
    p = PERSONAS.get(persona_key, PERSONAS.get("rosy"))
    template = PROMPTS["common"]["base_template"]

    return template.format(
        name=p["name"],
        description=p["description"],
        task_instruction=task_instruction,
        context_data=context_data,
        style=p["style"],
        prefix=p["prefix"],
        user_query=user_query,
    )
