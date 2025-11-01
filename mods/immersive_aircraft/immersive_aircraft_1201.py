"""沉浸式飞机模组补丁器（适用于 Minecraft 1.20.1）。

此模块提供了 ImmersiveAircraftPatcher_1201 类，用于修改沉浸式飞机模组的 JAR 文件。
主要修改内容包括：
- 调整各种飞机部件的合成配方（使用原版材料替换模组特有材料）
- 更新中文语言文件中的模组名称
"""
from ..patcher import JarPatcher
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class ImmersiveAircraftPatcher_1201(JarPatcher):
    """沉浸式飞机模组补丁器（Minecraft 1.20.1 版本）。
    
    此类继承自 JarPatcher，用于修改沉浸式飞机模组的 JAR 文件。
    主要功能包括修改合成配方和语言文件。
    """
    
    def run(self):
        """执行补丁流程。
        
        该方法按顺序调用各个修改方法来完成对模组的修改。
        """
        self.modify_recipes()
        self.modify_lang()

    def modify_recipes(self):
        """修改所有飞机部件的合成配方。
        
        将所有使用模组特有材料的配方替换为使用原版 Minecraft 材料，
        以便在不依赖模组其他部分的情况下合成这些部件。
        
        修改的配方包括：
        - 机身 (Hull)
        - 发动机 (Engine)
        - 风帆 (Sail)
        - 螺旋桨 (Propeller)
        - 锅炉 (Boiler)
        - 增强型螺旋桨 (Enhanced Propeller)
        - 经济型发动机 (Eco Engine)
        - 下界发动机 (Nether Engine)
        - 钢制锅炉 (Steel Boiler)
        - 工业齿轮 (Industrial Gears)
        - 加固管道 (Sturdy Pipes)
        - 机身加固板 (Hull Reinforcement)
        - 改良起落架 (Improved Landing Gear)
        """
        # 机身 (Hull) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/hull.json',
            keys_to_update={"I": "minecraft:iron_block"}
        )

        # 发动机 (Engine) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/engine.json',
            keys_to_update={"C": "minecraft:iron_block"}
        )

        # 风帆 (Sail) - 使用铅和羊毛地毯标签替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/sail.json',
            keys_to_update={
                "S": "minecraft:lead",
                "C": "#minecraft:wool_carpets"
            }
        )

        # 螺旋桨 (Propeller) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/propeller.json',
            keys_to_update={"I": "minecraft:iron_block"}
        )

        # 锅炉 (Boiler) - 使用铜块和水桶，并修改合成模式
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/boiler.json',
            keys_to_update={
                "C": "minecraft:copper_block",
                "W": "minecraft:water_bucket",
            },
            pattern=["CCC", "CWC", "CFC"]
        )

        # 增强型螺旋桨 (Enhanced Propeller) - 使用铜块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/enhanced_propeller.json',
            keys_to_update={"C": "minecraft:copper_block"}
        )

        # 经济型发动机 (Eco Engine) - 使用金块、粘性活塞和砖块，删除原键并修改模式
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/eco_engine.json',
            keys_to_update={
                "G": "minecraft:gold_block",
                "P": "minecraft:sticky_piston",
                "B": "minecraft:bricks",
            },
            keys_to_remove=['C', 'R', 'N'],
            pattern=["BGB", "PEP", "GBG"]
        )

        # 下界发动机 (Nether Engine) - 使用岩浆块、下界合金块和恶魂之泪，删除原键并修改模式
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/nether_engine.json',
            keys_to_update={
                "M": "minecraft:magma_block",
                "K": "minecraft:netherite_block",
                "L": "minecraft:ghast_tear",
            },
            keys_to_remove=['C', 'R', 'N'],
            pattern=["MKM", "BEB", "KLK"]
        )

        # 钢制锅炉 (Steel Boiler) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/steel_boiler.json',
            keys_to_update={"C": "minecraft:iron_block"}
        )

        # 工业齿轮 (Industrial Gears) - 使用铁块和铜块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/industrial_gears.json',
            keys_to_update={
                "I": "minecraft:iron_block",
                "C": "minecraft:copper_block",
            }
        )

        # 加固管道 (Sturdy Pipes) - 使用铁块和铜块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/sturdy_pipes.json',
            keys_to_update={
                "I": "minecraft:iron_block",
                "C": "minecraft:copper_block",
            }
        )

        # 机身加固板 (Hull Reinforcement) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/hull_reinforcement.json',
            keys_to_update={"I": "minecraft:iron_block"}
        )

        # 改良起落架 (Improved Landing Gear) - 使用铁块替代
        self.modify_recipe(
            recipe_path='./data/immersive_aircraft/recipes/improved_landing_gear.json',
            keys_to_update={"I": "minecraft:iron_block"}
        )

    def modify_lang(self):
        """修改中文语言文件。
        
        更新模组标签页的显示名称，将原名称替换为"沉浸式飞机（进阶版）"。
        """
        lang_path = './assets/immersive_aircraft/lang/zh_cn.json'
        lang_data = self.read_json(lang_path)
        lang_data["itemGroup.immersive_aircraft.immersive_aircraft_tab"] = "沉浸式飞机（进阶版）"
        self.write_json(lang_path, lang_data)
