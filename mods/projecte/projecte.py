from patcher import JarPatcher
import json5
from pathlib import Path
import json
from mods.projecte.ttp import TransmutationTabletPainter
import shutil

BASE_DIR = Path(__file__).resolve().parent


class ProjectEPatcher(JarPatcher):
    def run(self):
        self.delete_recipes()
        self.delete_loot_tables()
        self.modify_recipes()
        self.modify_emc()
        self.modify_lang()
        self.replace_textures()

    def delete_recipes(self):
        rel = './data/projecte/recipes'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

    def delete_loot_tables(self):
        rel = './data/projecte/loot_tables/blocks'
        keep = ['transmutation_table.json']
        self.remove_file(rel, keep=keep)

    def modify_recipes(self):
        self.modify_recipe(
            recipe_path='./data/projecte/recipes/transmutation_tablet.json',
            keys_to_update={
                "D": "minecraft:netherite_block"
            }
        )

        self.modify_recipe(
            recipe_path='./data/projecte/recipes/transmutation_table.json',
            keys_to_update={
                "P": "minecraft:diamond"
            }
        )

        self.remove_dir('./data/projecte/recipes/conversions')

    def modify_emc(self):
        default_emc_path = './data/projecte/pe_custom_conversions/defaults.json'
        default_emc_data = self.read_json(default_emc_path)

        with open(BASE_DIR / 'emc_data.json5', 'r', encoding='utf-8') as f:
            new_emc_data = json5.load(f)

        """ 原版物品 """
        for k, v in new_emc_data['vanilla'].items():
            default_emc_data['values']['before'][k] = v
        
        """ 农夫乐事模组 """
        for k, v in new_emc_data['farmersdelight'].items():
            default_emc_data['values']['before'][k] = v

        self.write_json(default_emc_path, default_emc_data)

    def modify_lang(self):
        emc_name = "Coins"  # 或credit
        lang_path = './assets/projecte/lang/zh_cn.json'
        
        emc_keys = {
            f"command.projecte.dump_missing_emc.multiple_missing": f"%s 物品缺少{emc_name}值，打印到服务器日志。",
            f"command.projecte.dump_missing_emc.none_missing": f"所有物品都有一个{emc_name}值。",
            f"command.projecte.dump_missing_emc.one_missing": f"一个物品缺少{emc_name}值，打印到服务器日志。",
            f"command.projecte.emc.add.success": f"已为 %s 增加 %s {emc_name}。",
            f"command.projecte.emc.get.success": f"%s 拥有 %s {emc_name}。",
            f"command.projecte.emc.negative": f"无法从 %s 移除 %s {emc_name}，否则其 {emc_name} 将为负数。",
            f"command.projecte.emc.remove.success": f"已从 %s 移除 %s {emc_name}。",
            f"command.projecte.emc.set.success": f"已将 %s 的 {emc_name} 设为 %s。",
            f"command.projecte.emc.test.fail": f"%s 的 {emc_name} 不足，无法移除 %s。",
            f"command.projecte.emc.test.success": f"%s 的 {emc_name} 足以移除 %s。",
            f"command.projecte.knowledge.invalid": f"物品 %s 没有 {emc_name} 值，无法售出。",
            f"config.jade.plugin_projecte.emc_provider": f"{emc_name} 提供者",
            f"emc.projecte.emc": f"%s {emc_name}",
            f"emc.projecte.tooltip": f"{emc_name}: %s",
            f"emc.projecte.tooltip.stack.with_sell": f"堆叠 {emc_name}: %s (%s)",
            f"emc.projecte.tooltip.with_sell": f"{emc_name}: %s (%s)"
        }

        other_keys = {
            "block.projecte.transmutation_table": "交易台",
            "item.projecte.transmutation_tablet": "交易终端",
            "tooltip.projecte.tome": "放入交易台可售出全部物品（创造专属）",
            "transmutation.projecte.transmute": "交易台",
            "advancements.projecte.transmutation_table": "交易物品！",
            "advancements.projecte.transmutation_tablet": "更先进的交易！",
        }

        with open(BASE_DIR / 'remain+i18n.json', 'r', encoding='utf-8') as f:
            remain_keys = json.load(f)

        org_keys = self.read_json(lang_path)
        total_keys = org_keys | remain_keys | emc_keys | other_keys
        
        self.write_json(lang_path, total_keys)

    def replace_textures(self):
        # 替换转化桌材质
        p = self.work_dir / './assets/projecte/textures/item/transmutation_tablet.png'
        p2 = self.work_dir / './assets/projecte/textures/block/transmutation_stone/top.png'
        painter = TransmutationTabletPainter('v7', p)
        painter.paint(p)
        painter.paint(p2)

        shutil.copy2(BASE_DIR / 'transmute.png', self.work_dir / './assets/projecte/textures/gui/transmute.png')
