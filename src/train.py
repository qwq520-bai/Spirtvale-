"""使用合并后的战斗 + NPC 数据集继续训练。"""

from pathlib import Path

from ultralytics import YOLO


REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "models" / "spirt_three.pt"
DATA_PATH = REPO_ROOT / "training_data" / "merged_dataset_v3" / "merged_dataset_v3.yaml"


def main():
    model = YOLO(MODEL_PATH)
    model.train(
        data=str(DATA_PATH),
        epochs=600,
        batch=4,
        workers=0,
        project=str(REPO_ROOT / "training_data" / "runs"),
        name="merged_npc_train",
        exist_ok=False,
    )


if __name__ == "__main__":
    main()
