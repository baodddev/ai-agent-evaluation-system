import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent[1] / "agents")
)

from agent import agent
from dataset import dataset
from model import eval_model