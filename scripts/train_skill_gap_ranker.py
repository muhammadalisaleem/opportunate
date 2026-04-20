from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recommender.skill_gap_ranker import train_and_save_model


if __name__ == "__main__":
    metadata = train_and_save_model()
    print(metadata)
