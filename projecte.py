from patcher import JarPatcher


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
        emc_data = self.read_json(default_emc_path)

        # 修改EMC
        emc_data['values']['before']['#forge:gems/emerald'] = 144  # 绿宝石


        self.write_json(default_emc_path, emc_data)




if __name__ == '__main__':
    jar_path = '~/Downloads/ProjectE-1.20.1-PE1.0.1.jar'
    output_path = '~/Desktop'
    patcher = ProjectEPatcher(jar_path, output_path)
    patcher.apply()
