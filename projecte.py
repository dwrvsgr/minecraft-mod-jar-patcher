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

        """ 原版物品 """
        emc_data['values']['before']['#forge:gems/emerald'] = 160  # 绿宝石
        emc_data['values']['before']['minecraft:gilded_blackstone'] = 48  # 镶金黑石
        emc_data['values']['before']['minecraft:wither_skeleton_skull'] = 10240  # 凋零骷髅头
        emc_data['values']['before']['minecraft:dragon_head'] = 32768  # 龙首
        emc_data['values']['before']['minecraft:elytra'] = 65536  # 鞘翅
        emc_data['values']['before']['minecraft:totem_of_undying'] = 8192  # 不死图腾
        emc_data['values']['before']['minecraft:experience_bottle'] = 512  # 附魔之瓶

        """ 农夫乐事模组 """
        # 原子物品
        emc_data['values']['before']['farmersdelight:canvas'] = 48  # 粗布（Canvas）
        emc_data['values']['before']['farmersdelight:cabbage'] = 64  # 卷心菜（Cabbage）
        emc_data['values']['before']['farmersdelight:tomato'] = 64  # 番茄（Tomato）
        emc_data['values']['before']['farmersdelight:onion'] = 64  # 洋葱（Onion）
        emc_data['values']['before']['farmersdelight:rice_panicle'] = 28  # 稻米穗（Rice Panicle）
        emc_data['values']['before']['farmersdelight:rice'] = 16  # 稻米（Rice）
        emc_data['values']['before']['farmersdelight:straw'] = 12  # 草秆（Straw）
        emc_data['values']['before']['farmersdelight:tree_bark'] = 1  # 树皮（Tree Bark）
        emc_data['values']['before']['farmersdelight:sandy_shrub'] = 1  # 沙生灌木（Sandy Shrub）
        emc_data['values']['before']['farmersdelight:brown_mushroom_colony'] = 96  # 棕色蘑菇菌落（Brown Mushroom Colony）
        emc_data['values']['before']['farmersdelight:red_mushroom_colony'] = 96  # 红色蘑菇菌落（Red Mushroom Colony）
        emc_data['values']['before']['farmersdelight:wild_cabbages'] = 64  # 野生卷心菜（Wild Cabbage）
        emc_data['values']['before']['farmersdelight:cabbage_leaf'] = 64  # 卷心菜叶（Cabbage Leaf）
        emc_data['values']['before']['farmersdelight:ham'] = 272  # 火腿（Ham）

        # 砧板物品
        emc_data['values']['before']['farmersdelight:cabbage_seeds'] = 32  # 卷心菜种子（Cabbage Seeds）
        emc_data['values']['before']['farmersdelight:raw_pasta'] = 34  # 生意面（Raw Pasta）
        emc_data['values']['before']['farmersdelight:pumpkin_slice'] = 36  # 南瓜片（Pumpkin Slice）
        emc_data['values']['before']['farmersdelight:minced_beef'] = 32  # 牛肉馅（Minced Beef）
        emc_data['values']['before']['farmersdelight:chicken_cuts'] = 8  # 生鸡肉丁（Raw Chicken Cuts）
        emc_data['values']['before']['farmersdelight:bacon'] = 32  # 生培根（Raw Bacon）
        emc_data['values']['before']['farmersdelight:cod_slice'] = 8  # 生鳕鱼片（Raw Cod Slice）
        emc_data['values']['before']['farmersdelight:salmon_slice'] = 8  # 生鲑鱼片（Raw Salmon Slice）
        emc_data['values']['before']['farmersdelight:mutton_chops'] = 32  # 生羊排（Raw Mutton Chops）
        emc_data['values']['before']['farmersdelight:cake_slice'] = 21  # 蛋糕切片（Slice of Cake）
        emc_data['values']['before']['farmersdelight:apple_pie_slice'] = 140  # 苹果派切片（Slice of Apple Pie）
        emc_data['values']['before']['farmersdelight:sweet_berry_cheesecake_slice'] = 45  # 甜浆果芝士派切片（Slice of Sweet Berry Cheesecake）
        emc_data['values']['before']['farmersdelight:chocolate_pie_slice'] = 78  # 巧克力派切片（Slice of Chocolate Pie）
        emc_data['values']['before']['farmersdelight:kelp_roll_slice'] = 29  # 海带寿司（Kelp Roll Slice）

        # 烹饪物品
        emc_data['values']['before']['farmersdelight:hot_cocoa'] = 148  # 热可可（Hot Cocoa）
        emc_data['values']['before']['farmersdelight:apple_cider'] = 271  # 苹果酒（Apple Cider）
        emc_data['values']['before']['farmersdelight:tomato_sauce'] = 128  # 番茄酱（Tomato Sauce）
        emc_data['values']['before']['farmersdelight:glow_berry_custard'] = 68  # 发光浆果蛋奶沙司（Glow Berry Custard）
        emc_data['values']['before']['farmersdelight:dumplings'] = 97  # 饺子（Dumplings）
        emc_data['values']['before']['farmersdelight:cabbage_rolls'] = 128  # 卷心菜卷（Cabbage Rolls）
        emc_data['values']['before']['farmersdelight:cooked_rice'] = 16  # 米饭（Cooked Rice）
        emc_data['values']['before']['farmersdelight:bone_broth'] = 148  # 大骨汤（Bone Broth）
        emc_data['values']['before']['farmersdelight:beef_stew'] = 192  # 牛肉炖（Beef Stew）
        emc_data['values']['before']['farmersdelight:chicken_soup'] = 256  # 鸡肉汤（Chicken Soup）
        emc_data['values']['before']['farmersdelight:vegetable_soup'] = 256  # 蔬菜汤（Vegetable Soup）
        emc_data['values']['before']['farmersdelight:fish_stew'] = 256  # 鱼肉炖（Fish Stew）
        emc_data['values']['before']['farmersdelight:fried_rice'] = 176  # 炒饭（Fried Rice）
        emc_data['values']['before']['farmersdelight:pumpkin_soup'] = 169  # 南瓜汤（Pumpkin Soup）
        emc_data['values']['before']['farmersdelight:baked_cod_stew'] = 224  # 烘焙鳕鱼炖（Baked Cod Stew）
        emc_data['values']['before']['farmersdelight:noodle_soup'] = 131  # 面条汤（Noodle Soup）
        emc_data['values']['before']['farmersdelight:pasta_with_meatballs'] = 194  # 肉丸意面（Pasta with Meatballs）
        emc_data['values']['before']['farmersdelight:pasta_with_mutton_chop'] = 226  # 羊排意面（Pasta with Mutton Chop）
        emc_data['values']['before']['farmersdelight:mushroom_rice'] = 144  # 蘑菇饭（Mushroom Rice）
        emc_data['values']['before']['farmersdelight:vegetable_noodles'] = 258  # 蔬菜面（Vegetable Noodles）
        emc_data['values']['before']['farmersdelight:ratatouille'] = 256  # 蔬菜杂烩（Ratatouille）
        emc_data['values']['before']['farmersdelight:squid_ink_pasta'] = 178  # 鱿鱼墨面（Squid Ink Pasta）
        emc_data['values']['before']['farmersdelight:roast_chicken'] = 106  # 盘装烤鸡（Plate of Roast Chicken）
        emc_data['values']['before']['farmersdelight:stuffed_pumpkin_block'] = 256  # 填馅南瓜（Stuffed Pumpkin，盛宴方块）
        emc_data['values']['before']['farmersdelight:stuffed_pumpkin'] = 70  # 碗装填馅南瓜（Bowl of Stuffed Pumpkin）
        emc_data['values']['before']['farmersdelight:shepherds_pie'] = 119  # 盘装牧羊人派（Plate of Shepherd's Pie）
        emc_data['values']['before']['farmersdelight:dog_food'] = 104  # 狗粮（Dog Food）
        emc_data['values']['before']['farmersdelight:honey_glazed_ham'] = 71  # 盘装蜜汁火腿（Plate of Honey Glazed Ham）


        self.write_json(default_emc_path, emc_data)




if __name__ == '__main__':
    jar_path = '~/Downloads/ProjectE-1.20.1-PE1.0.1.jar'
    output_path = '~/Desktop'
    patcher = ProjectEPatcher(jar_path, output_path)
    patcher.apply()
