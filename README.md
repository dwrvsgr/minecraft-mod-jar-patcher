# minecraft-mod-jar-patcher

这是一款轻量级的 Minecraft 模组修改器，专为**习惯直接修改 `.jar` 文件的MC玩家**设计。它仅支持通过修改 jar 包内部文件的方式来实现模组修改。

目前该修改器仅支持少量的1.20.1-Forge模组修改。

用法（可通过 `python run.py -h` 查看）

```python
usage: Minecraft Mod Patcher [-h] [--jar_path str] [--output_path {str,null}] [--mod_name str] [--validate_jar bool]

options:
  -h, --help            show this help message and exit
  --jar_path str        MOD文件路径 (required)
  --output_path {str,null}
                        修改后的MOD文件的输出目录，如果不提供则覆盖原文件 (default: null)
  --mod_name str        模组名称（目前仅支持projecte，immersive_aircraft） (required)
  --validate_jar bool   修改MOD前是否进行原始文件校验（确保MOD的来源是CurseForge/Modrinth） (default: True)
```


以等价交换为例：

```shell
python run.py \
  --jar_path ~/Downloads/ProjectE-1.20.1-PE1.0.1.jar \
  --output_path ~/Desktop \
  --mod_name projecte \
```

修改器的工作流：

1. 首先会解压 `ProjectE-1.20.1-PE1.0.1.jar` 
2. 修改器会进入到解压后的缓存目录，按照预定义的规则进行修改
3. 将修改后的文件重新打包，输出到output_path中，并删除中间缓存



若想查看某个模组的修改规则，可进入到 `mods/<mod_name>/<mod_name>.py` 下进行查看。目前的修改规则都是作者基于自己的游玩体验进行定制的。你也可以按照自己的想法进行调整或重写。



## 新增模组修改

如果你想新增一个模组的修改规则，按照以下流程进行：

1. 在 `mods/` 下创建一个名为 `<modid>` 的目录，并在该目录下创建 `<modid>.py` 文件，这个文件用来实现具体的修改逻辑。如果修改逻辑需要依靠其他文件，也请都放在 `<modid>` 目录下。
2. 修改 `mods/__init__.py`，按照原先的写法修改即可。
3. 修改 `meta.py` ，按照原先的写法修改即可。



## 已实现的模组修改

### 等价交换

众所周知，**等价交换（Project E）模组在游戏前期，玩家可通过与村民交易获取绿宝石**来快速积累EMC；到了中后期，则主要依赖**能量收集器（Energy Collector）实现大规模刷取。一旦玩家获得了暗物质/红物质/宝石套装**，并配合**飞行、抗火、无限氧气、水上行走、自动恢复**等功能性饰品，角色的能力将基本等同于**创造模式**。这些机制和物品极大地**破坏了游戏的平衡性**，因此有必要对其进行**魔改与重做**。

主要调整内容：

- **绿宝石的EMC值被设定为 160。** 这一数值是基于对村民**13 种职业的全部交易**进行调研后确定的。通过此调整，**约只有 20% 的村民交易能让玩家获利**，从而有效限制了前期的EMC积累速度。

- 仅**保留转化桌和便携式转化桌**，并对它们的合成配方进行了修改。**删除了除此之外所有其他等价交换物品的合成配方**，这样在非作弊模式下，玩家就无法获取这些物品了。

- 为原版中一些**没有EMC值的物品赋予了合理的EMC值**，这些数值是根据GPT-Thinking推理确定的。
- 为**农夫乐事（Farmer's Delight）模组中的所有物品赋予了EMC值**。
