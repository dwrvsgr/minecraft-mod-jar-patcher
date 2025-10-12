from patcher import JarPatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class ImmersiveAircraftPatcher(JarPatcher):
    def run(self):
        self.modify_recipes()

    def modify_recipes(self):
        pass