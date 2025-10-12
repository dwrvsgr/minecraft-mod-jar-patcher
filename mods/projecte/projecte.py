from patcher import JarPatcher
import json5
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class ProjectEPatcher(JarPatcher):
    def run(self):
        self.delete_recipes()
        self.delete_loot_tables()
        self.modify_recipes()
        self.modify_emc()

    def delete_recipes(self):
        rel = './data/projecte/recipes'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

    def delete_loot_tables(self):
        rel = './data/projecte/loot_tables/blocks'
        keep = ['transmutation_table.json']
        self.remove_file(rel, keep=keep)

    def modify_recipes(self):
        tablet_path = './data/projecte/recipes/transmutation_tablet.json'
        tablet_data = self.read_json(tablet_path)
        tablet_data['key']['D']['item'] = 'minecraft:netherite_block'
        self.write_json(tablet_path, tablet_data)

        table_path = './data/projecte/recipes/transmutation_table.json'
        table_data = self.read_json(table_path)
        table_data['key']['P']['item'] = 'minecraft:diamond'
        self.write_json(table_path, table_data)

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


