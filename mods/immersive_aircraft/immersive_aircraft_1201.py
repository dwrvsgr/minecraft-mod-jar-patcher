from ..patcher import JarPatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class ImmersiveAircraftPatcher_1201(JarPatcher):
    def run(self):
        self.modify_recipes()
        self.modify_lang()

    def modify_recipes(self):
        # 机身
        hull_path = './data/immersive_aircraft/recipes/hull.json'
        self.modify_recipe(
            recipe_path=hull_path,
            keys_to_update={
                "I": "minecraft:iron_block",
            }
        )

        # 发动机
        engine_path = './data/immersive_aircraft/recipes/engine.json'
        self.modify_recipe(
            recipe_path=engine_path,
            keys_to_update={
                "C": "minecraft:iron_block",
            }
        )

        # 风帆
        sail_path = './data/immersive_aircraft/recipes/sail.json'
        self.modify_recipe(
            recipe_path=sail_path,
            keys_to_update={
                "S": "minecraft:lead",
                "C": "#minecraft:wool_carpets"
            }
        )

        # 螺旋桨
        propeller_path = './data/immersive_aircraft/recipes/propeller.json'
        self.modify_recipe(
            recipe_path=propeller_path,
            keys_to_update={
                "I": "minecraft:iron_block",
            }
        )

        # 锅炉
        boiler_path = './data/immersive_aircraft/recipes/boiler.json'
        self.modify_recipe(
            recipe_path=boiler_path,
            keys_to_update={
                "C": "minecraft:copper_block",
                "W": "minecraft:water_bucket",
            },
            pattern=["CCC", "CWC", "CFC"]
        )

        # 增强型螺旋桨
        enhanced_propeller_path = './data/immersive_aircraft/recipes/enhanced_propeller.json'
        self.modify_recipe(
            recipe_path=enhanced_propeller_path,
            keys_to_update={
                "C": "minecraft:copper_block",
            },
        )

        # 经济型发动机
        eco_engine_path = './data/immersive_aircraft/recipes/eco_engine.json'
        self.modify_recipe(
            recipe_path=eco_engine_path,
            keys_to_update={
                "G": "minecraft:gold_block",
                "P": "minecraft:sticky_piston",
                "B": "minecraft:bricks",
            },
            keys_to_remove=['C', 'R', 'N'],
            pattern=["BGB", "PEP", "GBG"]
        )

        # 下界发动机
        nether_engine_path = './data/immersive_aircraft/recipes/nether_engine.json'
        self.modify_recipe(
            recipe_path=nether_engine_path,
            keys_to_update={
                "M": "minecraft:magma_block",
                "K": "minecraft:netherite_block",
                "L": "minecraft:ghast_tear",
            },
            keys_to_remove=['C', 'R', 'N'],
            pattern=["MKM", "BEB", "KLK"]
        )

        # 钢制锅炉
        steel_boiler_path = './data/immersive_aircraft/recipes/steel_boiler.json'
        self.modify_recipe(
            recipe_path=steel_boiler_path,
            keys_to_update={
                "C": "minecraft:iron_block",
            }
        )

        # 工业齿轮
        industrial_gears_path = './data/immersive_aircraft/recipes/industrial_gears.json'
        self.modify_recipe(
            recipe_path=industrial_gears_path,
            keys_to_update={
                "I": "minecraft:iron_block",
                "C": "minecraft:copper_block",
            }
        )

        # 加固管道
        sturdy_pipes_path = './data/immersive_aircraft/recipes/sturdy_pipes.json'
        self.modify_recipe(
            recipe_path=sturdy_pipes_path,
            keys_to_update={
                "I": "minecraft:iron_block",
                "C": "minecraft:copper_block",
            }
        )

        # 机身加固板
        hull_reinforcement_path = './data/immersive_aircraft/recipes/hull_reinforcement.json'
        self.modify_recipe(
            recipe_path=hull_reinforcement_path,
            keys_to_update={
                "I": "minecraft:iron_block",
            }
        )

        # 改良起落架
        improved_landing_gear_path = './data/immersive_aircraft/recipes/improved_landing_gear.json'
        self.modify_recipe(
            recipe_path=improved_landing_gear_path,
            keys_to_update={
                "I": "minecraft:iron_block",
            }
        )

    def modify_lang(self):
        lang_path = './assets/immersive_aircraft/lang/zh_cn.json'
        org_keys = self.read_json(lang_path)
        org_keys["itemGroup.immersive_aircraft.immersive_aircraft_tab"] = "沉浸式飞机（进阶版）"
        self.write_json(lang_path, org_keys)
