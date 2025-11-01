from ..patcher import JarPatcher
import json5
from pathlib import Path
import json
import re
from mods.projecte.ttp import TransmutationTabletPainter
import shutil

BASE_DIR = Path(__file__).resolve().parent


class ProjectEPatcher_1122(JarPatcher):
    """等价交换模组补丁器（Minecraft 1.12.2 版本）。
    
    此类继承自 JarPatcher，用于修改等价交换模组的 JAR 文件。
    主要功能包括删除、修改和替换模组中的各种资源文件。
    
    注意：此版本与 1.20.1/1.21.1 版本的主要区别：
    1. 目录结构：使用 assets/projecte/ 而非 data/projecte/
    2. 语言文件：使用 .lang 格式（键值对）而非 .json
    3. EMC 数据：格式为 item|meta 而非 item:namespace
    4. 模组元数据：使用 mcmod.info（JSON数组）而非 mods.toml
    5. 没有战利品表（1.12.2版本不支持）
    6. 纹理路径：使用 textures/items/ 和 textures/blocks/
    
    支持的 Minecraft 版本：1.12.2
    """
    
    def run(self):
        """执行补丁流程。
        
        按顺序执行删除、修改和替换操作来完成对模组的修改。
        """
        # 删除操作
        self.delete_recipes()
        self.delete_advancements()

        # 修改操作
        self.modify_recipes()
        self.modify_emc()
        self.modify_lang()
        self.modify_mcmod_info()

        # 替换操作
        self.replace_textures()

    def delete_advancements(self):
        """删除进度文件。
        
        删除所有进度文件，但保留以下文件：
        - transmutation_table.json
        - transmutation_tablet.json
        
        注意：1.12.2 版本的进度文件在 assets/projecte/advancements/ 目录下。
        """
        rel = './assets/projecte/advancements'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

    def delete_recipes(self):
        """删除配方文件。
        
        删除所有配方文件，但保留以下文件：
        - transmutation_table.json
        - item.pe_transmutation_tablet.json（注意：1.12.2版本使用不同的文件名）
        - _constants.json（常量定义文件，用于解析 #CONSTANT 格式的配方引用）
        - _factories.json（工厂定义文件，用于条件配方）
        
        注意：1.12.2 版本的配方文件在 assets/projecte/recipes/ 目录下。
        """
        rel = './assets/projecte/recipes'
        keep = [
            'transmutation_table.json',
            'item.pe_transmutation_tablet.json',
            '_constants.json',  # 必须保留，用于解析 #GEMDIAMOND 等常量引用
            '_factories.json'   # 保留工厂定义文件
        ]
        self.remove_file(rel, keep=keep)

    def modify_recipes(self):
        """修改合成配方。
        
        修改以下配方：
        - 交易终端：将 "D" 键替换为钻石块
        - 交易台：将 "P" 键替换为钻石（使用常量引用 #GEMDIAMOND）
        
        删除 conversions 子目录及其所有内容。
        
        注意：1.12.2 版本的配方文件路径不同，且配方格式可能略有不同。
        使用 #CONSTANT 格式的常量引用时，需要确保 _constants.json 文件存在（已在 delete_recipes 中保留）。
        """
        # 修改交易终端配方（注意：1.12.2版本使用 item.pe_transmutation_tablet.json）
        # 没有下界合金块，因此替换成原版钻石块
        self.modify_recipe(
            recipe_path='./assets/projecte/recipes/item.pe_transmutation_tablet.json',
            keys_to_update={"D": "minecraft:diamond_block"}
        )
        
        # 修改交易台配方
        self.modify_recipe(
            recipe_path='./assets/projecte/recipes/transmutation_table.json',
            keys_to_update={"P": "minecraft:diamond"}
        )

        self.remove_dir('./assets/projecte/recipes/conversions')

    def modify_emc(self):
        """修改 EMC（等价交换值）配置。
        
        1.12.2 版本的 EMC 数据结构：
        - 文件路径：defaultCustomConversions/defaults.json
        - 格式：values.before 是 Dict[str, int]，键为 "item|meta" 格式
        
        处理逻辑：
        1. 删除绿宝石标签的 EMC 值（如果存在）
        2. 合并外部 EMC 数据（原版物品和农夫乐事模组）
        3. 注意：外部数据可能是新版本格式（item:namespace），需要转换为1.12.2格式（item|meta）
        """
        default_emc_path = './defaultCustomConversions/defaults.json'
        default_emc_data = self.read_json(default_emc_path)

        emc_data_dir = BASE_DIR / 'emc_data'
        # 加载原版物品的 EMC 数据
        with open(emc_data_dir / 'vanilla.json5', 'r', encoding='utf-8') as f:
            vanilla_data = json5.load(f)
        # 加载农夫乐事模组的 EMC 数据
        with open(emc_data_dir / 'farmersdelight.json5', 'r', encoding='utf-8') as f:
            farmersdelight_data = json5.load(f)

        # 删除绿宝石标签的 EMC 值（如果存在）
        # 1.12.2版本可能使用不同的标签格式，例如 #forge:gems/emerald 或 OreDictionary名称
        if 'values' in default_emc_data and 'before' in default_emc_data['values']:
            # 查找并删除绿宝石相关的标签
            keys_to_remove = []
            for key in default_emc_data['values']['before'].keys():
                if 'emerald' in key.lower() or key.startswith('#forge:gems/emerald'):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del default_emc_data['values']['before'][key]

        # 转换并合并原版物品的 EMC 值
        # 注意：外部数据可能是新版本格式（minecraft:item），需要转换为1.12.2格式（minecraft:item|0）
        for k, v in vanilla_data.items():
            # 如果键已经是 item|meta 格式，直接使用
            if '|' in k:
                default_emc_data['values']['before'][k] = v
            else:
                # 否则，添加 |0 作为默认meta值
                default_emc_data['values']['before'][f"{k}|0"] = v
        
        # 转换并合并农夫乐事模组物品的 EMC 值
        for k, v in farmersdelight_data.items():
            if '|' in k:
                default_emc_data['values']['before'][k] = v
            else:
                default_emc_data['values']['before'][f"{k}|0"] = v

        self.write_json(default_emc_path, default_emc_data)

    def modify_lang(self):
        """修改中文语言文件。
        
        将所有与 EMC 相关的文本替换为 "Coins"（硬币），并添加其他自定义翻译。
        
        注意：1.12.2 版本使用 .lang 格式而非 .json 格式。
        语言文件路径：assets/projecte/lang/zh_cn.lang
        """
        emc_name = "Coins"  # EMC 的新名称，也可以使用 "credit"
        lang_path = './assets/projecte/lang/zh_cn.lang'
        
        # 读取原始语言文件
        lang_dict = self.read_lang(lang_path)
        
        # EMC 相关的翻译键，将 EMC 替换为 Coins
        # 注意：1.12.2版本的键名格式可能不同
        emc_replacements = {
            "pe.command.remove.success": f"成功移除 %s 的{emc_name}值.",
            "pe.command.reset.success": f"成功修改\"%s\"的{emc_name}值。",
            "pe.command.set.success": f"已将 %s 的{emc_name}值设为 %s.",
            "pe.divining.avgemc": f"平均{emc_name}值为%s，共%s个方块",
            "pe.divining.maxemc": f"最高{emc_name}：%s",
            "pe.divining.secondmax": f"第二高{emc_name}：%s",
            "pe.divining.thirdmax": f"第三高{emc_name}：%s",
            "pe.emc.emc_tooltip_prefix": f"{emc_name}：",
            "pe.emc.maxgenrate_tooltip": f"最高充能效率：",
            "pe.emc.maxoutrate_tooltip": f"最高输出效率：",
            "pe.emc.maxstorage_tooltip": f"能量上限：",
            "pe.emc.name": emc_name,
            "pe.emc.rate": f"{emc_name}/s",
            "pe.emc.stackemc_tooltip_prefix": f"{emc_name}总和：",
            "pe.emc.storedemc_tooltip": f"{emc_name}存储：",
            "pe.emc.too_much": f"{emc_name}能量已达到上限！",
            "pe.evertide.tooltip4": f"使用无需消耗{emc_name}！",
            "pe.volcanite.tooltip4": f"使用需消耗32{emc_name}",
            "advancements.pe_klein": f"{emc_name}能量电池!",
            "advancements.pe_klein.desc": f"储存{emc_name}以备不时之需!",
            "advancements.pe_klein_big": f"大容量的{emc_name}能量电池",
        }
        
        # 其他自定义翻译键
        other_keys = {
            "tile.pe_transmutation_stone.name": "交易台",
            "item.pe_transmutation_tablet.name": "交易终端",
            "advancements.pe_transmutation": "交易物品！",
            "advancements.pe_transmutation.desc": "开始亦是结束",
            "advancements.pe_portable_transmutation": "更先进的交易！",
            "advancements.pe_portable_transmutation.desc": "这太美妙了!",
            "pe.transmutation.transmute": "交易台",
        }
        
        # 加载保留的翻译键（从JSON格式转换）
        try:
            with open(BASE_DIR / 'remain+i18n.json', 'r', encoding='utf-8') as f:
                remain_keys_json = json.load(f)
            # 将JSON格式的键转换为1.12.2格式的键（如果存在）
            remain_keys = {}
            for key, value in remain_keys_json.items():
                # 尝试匹配1.12.2格式的键名
                # 例如：command.projecte.emc.set.success -> pe.command.set.success
                if key.startswith("command.projecte."):
                    # 简化转换：移除 namespace 前缀
                    new_key = key.replace("command.projecte.", "pe.command.")
                    remain_keys[new_key] = value
                elif key.startswith("emc.projecte."):
                    new_key = key.replace("emc.projecte.", "pe.emc.")
                    remain_keys[new_key] = value
                elif key.startswith("advancements.projecte."):
                    new_key = key.replace("advancements.projecte.", "advancements.pe_")
                    remain_keys[new_key] = value
                elif key.startswith("block.projecte."):
                    new_key = key.replace("block.projecte.", "tile.pe_")
                    remain_keys[new_key] = value
                elif key.startswith("item.projecte."):
                    new_key = key.replace("item.projecte.", "item.pe_")
                    remain_keys[new_key] = value
                elif key.startswith("transmutation.projecte."):
                    new_key = key.replace("transmutation.projecte.", "pe.transmutation.")
                    remain_keys[new_key] = value
                else:
                    # 直接使用原键名（如果格式匹配）
                    remain_keys[key] = value
        except FileNotFoundError:
            remain_keys = {}
        
        # 合并所有翻译键
        # 先应用原始翻译，然后覆盖保留的翻译，最后覆盖EMC和其他自定义翻译
        lang_dict.update(remain_keys)
        lang_dict.update(emc_replacements)
        lang_dict.update(other_keys)
        
        # 写入更新后的语言文件
        self.write_lang(lang_path, lang_dict)

    def replace_textures(self):
        """替换材质纹理文件。
        
        使用 TransmutationTabletPainter 重新绘制以下纹理：
        - 交易终端的物品纹理
        - 交易台的方块顶部纹理
        
        同时复制自定义的 GUI 纹理文件。
        
        注意：1.12.2 版本的纹理路径：
        - 物品纹理：assets/projecte/textures/items/transmute_tablet.png
        - 方块纹理：assets/projecte/textures/blocks/transmutation_stone/top.png
        """
        # 交易终端的物品纹理和交易台的方块顶部纹理
        tablet_item_path = self.work_dir / './assets/projecte/textures/items/transmute_tablet.png'
        table_top_path = self.work_dir / './assets/projecte/textures/blocks/transmutation_stone/top.png'
        
        painter = TransmutationTabletPainter('v7', tablet_item_path)
        painter.paint(tablet_item_path)
        painter.paint(table_top_path)

        # 复制自定义的 GUI 纹理
        shutil.copy2(
            BASE_DIR / 'transmute.png',
            self.work_dir / './assets/projecte/textures/gui/transmute.png'
        )

    def modify_mcmod_info(self):
        """修改模组元数据文件（mcmod.info）。
        
        更新模组的显示名称、作者列表和描述信息。
        
        注意：1.12.2 版本使用 mcmod.info（JSON数组格式）而非 mods.toml。
        mcmod.info 文件可能包含未转义的换行符，需要先修复再解析。
        """
        mcmod_path = './mcmod.info'
        mcmod_file_path = self.work_dir / mcmod_path
        
        # 读取文件内容
        with open(mcmod_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复 credits 字段中的未转义换行符
        # credits 字段的值包含未转义的换行符，需要将它们转义为 \n
        # 使用正则表达式匹配 credits 字段的完整内容
        def fix_credits_field(match):
            """修复 credits 字段中的换行符"""
            prefix = match.group(1)  # "credits": "
            credits_content = match.group(2)  # credits 字段的内容（包含换行符）
            suffix = match.group(3)  # 结束的引号和可能的逗号/空白
            # 将换行符替换为转义的 \n，同时转义其他需要转义的字符
            fixed_content = credits_content.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')
            return f'{prefix}{fixed_content}{suffix}'
        
        # 匹配 credits 字段：从 "credits": " 开始，到下一个独立引号结束（可能跨多行）
        # 使用 DOTALL 标志使 . 匹配换行符
        pattern = r'("credits":\s*")(.*?)("\s*[,}])'
        content = re.sub(pattern, fix_credits_field, content, flags=re.DOTALL)
        
        # 现在可以使用 json5 或标准 json 解析
        mcmod_data = json5.loads(content)
        
        # mcmod.info 是一个JSON数组，包含一个对象
        if isinstance(mcmod_data, list) and len(mcmod_data) > 0:
            mod_info = mcmod_data[0]
            mod_info["name"] = "等价交换 (交易版)"
            mod_info["authorList"] = ["sinkillerj", "Moze_Intel", "dongwen"]
            mod_info["description"] = "Transaction Edition of ProjectE, modified by dongwen."
            self.write_json(mcmod_path, mcmod_data)
