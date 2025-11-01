from ..patcher import JarPatcher
import json5
from pathlib import Path
import json
from mods.projecte.ttp import TransmutationTabletPainter
import shutil

BASE_DIR = Path(__file__).resolve().parent


class ProjectEPatcher_1201(JarPatcher):
    """等价交换模组补丁器（Minecraft 1.20.1、1.19.2、1.18.2、1.16.5 版本）。
    
    此类继承自 JarPatcher，用于修改等价交换模组的 JAR 文件。
    主要功能包括删除、修改和替换模组中的各种资源文件。
    
    支持的 Minecraft 版本：1.20.1、1.19.2、1.18.2、1.16.5
    """
    
    def run(self):
        """执行补丁流程。
        
        按顺序执行删除、修改和替换操作来完成对模组的修改。
        """
        # 删除操作
        self.delete_recipes()
        self.delete_loot_tables()
        self.delete_advancements()

        # 修改操作
        self.modify_recipes()
        self.modify_emc()
        self.modify_lang()
        self.modify_toml()

        # 替换操作
        self.replace_textures()

    def delete_advancements(self):
        """删除进度文件。
        
        删除所有进度文件，但保留以下文件：
        - transmutation_table.json
        - transmutation_tablet.json
        
        同时删除 recipes 子目录及其所有内容。
        """
        rel = './data/projecte/advancements'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

        self.remove_dir('./data/projecte/advancements/recipes')

    def delete_recipes(self):
        """删除配方文件。
        
        删除所有配方文件，但保留以下文件：
        - transmutation_table.json
        - transmutation_tablet.json
        """
        rel = './data/projecte/recipes'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

    def delete_loot_tables(self):
        """删除战利品表文件。
        
        删除 blocks 目录下的所有战利品表文件，但保留 transmutation_table.json。
        """
        rel = './data/projecte/loot_tables/blocks'
        keep = ['transmutation_table.json']
        self.remove_file(rel, keep=keep)

    def modify_recipes(self):
        """修改合成配方。
        
        修改以下配方：
        - 交易终端：将 "D" 键替换为下界合金块
        - 交易台：将 "P" 键替换为钻石
        
        删除 conversions 子目录及其所有内容。
        """
        self.modify_recipe(
            recipe_path='./data/projecte/recipes/transmutation_tablet.json',
            keys_to_update={"D": "minecraft:netherite_block"}
        )

        self.modify_recipe(
            recipe_path='./data/projecte/recipes/transmutation_table.json',
            keys_to_update={"P": "minecraft:diamond"}
        )

        self.remove_dir('./data/projecte/recipes/conversions')

    def modify_emc(self):
        """修改 EMC（等价交换值）配置。
        
        从外部 JSON5 文件加载自定义的 EMC 值，并合并到模组的默认 EMC 配置中。
        具体操作：
        1. 删除绿宝石标签的 EMC 值
        2. 合并原版物品的 EMC 值（从 vanilla.json5）
        3. 合并农夫乐事模组物品的 EMC 值（从 farmersdelight.json5）
        """
        default_emc_path = './data/projecte/pe_custom_conversions/defaults.json'
        default_emc_data = self.read_json(default_emc_path)

        emc_data_dir = BASE_DIR / 'emc_data'
        # 加载原版物品的 EMC 数据
        with open(emc_data_dir / 'vanilla.json5', 'r', encoding='utf-8') as f:
            vanilla_data = json5.load(f)
        # 加载农夫乐事模组的 EMC 数据
        with open(emc_data_dir / 'farmersdelight.json5', 'r', encoding='utf-8') as f:
            farmersdelight_data = json5.load(f)

        # 删除绿宝石标签的 EMC 值
        del default_emc_data['values']['before']['#forge:gems/emerald']

        # 合并原版物品的 EMC 值
        for k, v in vanilla_data.items():
            default_emc_data['values']['before'][k] = v
        
        # 合并农夫乐事模组物品的 EMC 值
        for k, v in farmersdelight_data.items():
            default_emc_data['values']['before'][k] = v

        self.write_json(default_emc_path, default_emc_data)

    def modify_lang(self):
        """修改中文语言文件。
        
        将所有与 EMC 相关的文本替换为 "Coins"（硬币），并添加其他自定义翻译。
        合并以下来源的翻译键：
        1. 原始语言文件
        2. 保留的翻译（remain+i18n.json）
        3. EMC 相关的翻译键（替换为 Coins）
        4. 其他自定义翻译键
        """
        emc_name = "Coins"  # EMC 的新名称，也可以使用 "credit"
        lang_path = './assets/projecte/lang/zh_cn.json'
        
        # EMC 相关的翻译键，将 EMC 替换为 Coins
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
            f"emc.projecte.tooltip.with_sell": f"{emc_name}: %s (%s)",
            f"command.projecte.remove.success": f"成功移除 %s 的{emc_name}值.",
            f"command.projecte.reset.success": f"成功修改\"%s\"的{emc_name}值。",
            f"command.projecte.set.success": f"已将 %s 的{emc_name}值设为 %s.",
            f"divining_rod.projecte.avg_emc": f"平均{emc_name}值为%s，共%s个方块",
            f"divining_rod.projecte.max_emc": f"最高{emc_name}：%s",
            f"divining_rod.projecte.second_max": f"第二高{emc_name}：%s",
            f"divining_rod.projecte.third_max": f"第三高{emc_name}：%s",
            f"emc.projecte.max_gen_rate": f"最高收集效率： %s {emc_name}/s",
            f"emc.projecte.max_output_rate": f"最高输出效率： %s {emc_name}/s",
            f"emc.projecte.max_storage": f"{emc_name}上限： %s {emc_name}",
            f"emc.projecte.tooltip.stack": f"{emc_name}总和： %s",
            f"emc.projecte.stored": f"{emc_name}存储： %s",
            f"emc.projecte.too_much": f"{emc_name}已达到上限！",
            f"tooltip.projecte.evertide.4": f"使用无需消耗{emc_name}！",
            f"tooltip.projecte.volcanite.4": f"使用需消耗32 {emc_name}",
            f"advancements.projecte.klein_star": f"{emc_name} 电池!",
            f"advancements.projecte.klein_star.description": f"储存{emc_name}以备不时之需!",
            f"advancements.projecte.klein_star_big": f"大容量的{emc_name}电池",
        }

        # 其他自定义翻译键
        other_keys = {
            "block.projecte.transmutation_table": "交易台",
            "item.projecte.transmutation_tablet": "交易终端",
            "tooltip.projecte.tome": "放入交易台可售出全部物品（创造专属）",
            "transmutation.projecte.transmute": "交易台",
            "advancements.projecte.transmutation_table": "交易物品！",
            "advancements.projecte.transmutation_tablet": "更先进的交易！",
        }

        # 加载保留的翻译键
        with open(BASE_DIR / 'remain+i18n.json', 'r', encoding='utf-8') as f:
            remain_keys = json.load(f)

        # 合并所有翻译键（使用字典合并，后面的键会覆盖前面的同名键）
        org_keys = self.read_json(lang_path)
        total_keys = org_keys | remain_keys | emc_keys | other_keys
        
        self.write_json(lang_path, total_keys)

    def replace_textures(self):
        """替换材质纹理文件。
        
        使用 TransmutationTabletPainter 重新绘制以下纹理：
        - 交易终端的物品纹理
        - 交易台的方块顶部纹理
        
        同时复制自定义的 GUI 纹理文件。
        """
        # 交易终端的物品纹理和交易台的方块顶部纹理
        tablet_item_path = self.work_dir / './assets/projecte/textures/item/transmutation_tablet.png'
        table_top_path = self.work_dir / './assets/projecte/textures/block/transmutation_stone/top.png'
        
        painter = TransmutationTabletPainter('v7', tablet_item_path)
        painter.paint(tablet_item_path)
        painter.paint(table_top_path)

        # 复制自定义的 GUI 纹理
        shutil.copy2(
            BASE_DIR / 'transmute.png',
            self.work_dir / './assets/projecte/textures/gui/transmute.png'
        )

    def modify_toml(self):
        """修改模组元数据文件（mods.toml）。
        
        更新模组的显示名称、作者列表和描述信息。
        """
        toml_path = './META-INF/mods.toml'
        toml_data = self.read_toml(toml_path)
        toml_data["mods"][0]["displayName"] = "等价交换 (交易版)"
        toml_data["mods"][0]["authors"] = "SinKillerJ, MaPePeR, williewillus, Lilylicious, pupnewfster, dongwen"
        toml_data["mods"][0]["description"] = "Transaction Edition of ProjectE, modified by dongwen."
        self.write_toml(toml_path, toml_data)
