from ..patcher import JarPatcher
import json5
from pathlib import Path
import json
from mods.projecte.ttp import TransmutationTabletPainter
import shutil

BASE_DIR = Path(__file__).resolve().parent


class ProjectEPatcher_1211(JarPatcher):
    """ 
    支持的版本：1.21.1
    """
    def run(self):
        # 删除
        self.delete_recipes()
        self.delete_loot_tables()
        self.delete_advancements()

        # 修改
        self.modify_recipes()
        self.modify_emc()
        self.modify_lang()
        self.modify_toml()

        # 替换
        self.replace_textures()

    def delete_advancements(self):
        rel = './data/projecte/advancement'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

        self.remove_dir('./data/projecte/advancement/recipes')

    def delete_recipes(self):
        rel = './data/projecte/recipe'
        keep = ['transmutation_table.json', 'transmutation_tablet.json']
        self.remove_file(rel, keep=keep)

    def delete_loot_tables(self):
        rel = './data/projecte/loot_table/blocks'
        keep = ['transmutation_table.json']
        self.remove_file(rel, keep=keep)

    def modify_recipes(self):
        self.modify_recipe(
            recipe_path='./data/projecte/recipe/transmutation_tablet.json',
            keys_to_update={
                "D": "minecraft:netherite_block"
            }
        )

        self.modify_recipe(
            recipe_path='./data/projecte/recipe/transmutation_table.json',
            keys_to_update={
                "P": "minecraft:diamond"
            }
        )

        self.remove_dir('./data/projecte/recipe/conversions')

    def modify_emc(self):
        default_emc_path = './data/projecte/pe_custom_conversions/defaults.json'
        default_emc_data = self.read_json(default_emc_path)

        emc_data_dir = BASE_DIR / 'emc_data'
        with open(emc_data_dir / 'vanilla.json5', 'r', encoding='utf-8') as f:
            vanilla_data = json5.load(f)
        with open(emc_data_dir / 'farmersdelight.json5', 'r', encoding='utf-8') as f:
            farmersdelight_data = json5.load(f)

        """
        1.21.1 中的data['values']['before'] 不再是一个Dict[str, Any]，而是一个List[Dict[str, Any]]，长度为209，相比1.20.1多了14个。

        经统计：
            - type一共只有3种：{'projecte:fluid', 'projecte:fake', 'projecte:item'}，其中前2种只出现1次，最后一种出现207次。
            - 统计List中每个Dict的keys组合的出现频率：
                ① ('type', 'description', 'emc_value'): 1
                ② ('type', 'emc_value', 'tag'): 27
                ③ ('type', 'emc_value', 'id'): 173
                ④ ('type', 'data', 'emc_value', 'id'): 8
        
        分析：
            - ① 和 ④需要原样保留，对于② 和 ③，先将其压缩为一个Dict，与new_emc_data合并后再进行还原
        """

        result = []
        org_emc_data = {}
        for item in default_emc_data['values']['before']:
            if 'data' in item or 'description' in item:
                result.append(item)
            else:
                if 'id' in item:
                    org_emc_data[item['id']] = item['emc_value']
                else:
                    # 不考虑绿宝石标签
                    if item['tag'] == 'c:gems/emerald':
                        continue
                    org_emc_data[f"#{item['tag']}"] = item['emc_value']
        
        """ 原版物品 """
        for k, v in vanilla_data.items():
            org_emc_data[k] = v
        
        """ 农夫乐事模组 """
        for k, v in farmersdelight_data.items():
            org_emc_data[k] = v

        for k, v in org_emc_data.items():
            base = {'type': 'projecte:item', 'emc_value': v}
            if k.startswith('#'):
                base['tag'] = k[1:]
            else:
                base['id'] = k
            result.append(base)
        
        default_emc_data['values']['before'] = result

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

        other_keys = {
            "block.projecte.transmutation_table": "交易台",
            "item.projecte.transmutation_tablet": "交易终端",
            "tooltip.projecte.tome": "放入交易台可售出全部物品（创造专属）",
            "transmutation.projecte.transmute": "交易台",
            "advancements.projecte.transmutation_table": "交易物品！",
            "advancements.projecte.transmutation_tablet": "更先进的交易！",
            "fml.menu.mods.info.description.projecte": "Transaction Edition of ProjectE, modified by dongwen.",
            "fml.menu.mods.info.displayname.projecte": "等价交换（交易版）",
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

    def modify_toml(self):
        toml_path = './META-INF/neoforge.mods.toml'
        toml_data = self.read_toml(toml_path)
        toml_data["mods"][0]["displayName"] = "等价交换 (交易版)"
        toml_data["mods"][0]["authors"] = "SinKillerJ, MaPePeR, williewillus, Lilylicious, pupnewfster, dongwen"
        toml_data["mods"][0]["description"] = "Transaction Edition of ProjectE, modified by dongwen."
        self.write_toml(toml_path, toml_data)
