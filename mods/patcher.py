from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Dict, List, Optional, Any
import zipfile
import shutil
import os
import hashlib
import json
import toml

PathLike = Union[str, Path]


_JSON_INDENT = 4


def _get_meta():
    """延迟导入 meta 模块以避免循环依赖。"""
    from meta import META
    return META


class JarPatcher(ABC):
    """JAR 文件补丁器基类。

    此类提供了一个框架，用于修改 Minecraft 模组 JAR 文件。子类需要实现 `run()` 方法
    来定义具体的修改逻辑。

    工作流程：
        1. 初始化时指定源 JAR 文件路径和输出路径
        2. 调用 `apply()` 方法执行补丁流程：
           - 验证并校验源文件
           - 解压 JAR 到临时工作目录
           - 调用 `run()` 方法执行修改
           - 重新打包并输出
           - 清理临时文件

    注意：
        工作目录位于 `~/.cache/<hash>/`，其中 hash 是基于 JAR 文件路径计算的。
        每次 `apply()` 调用都会创建新的工作目录并清理旧目录。
    """
    def __init__(
        self,
        mod_name: str,
        jar_path: PathLike,
        output_dir: PathLike | None = None,
        validate_jar: bool = True,
    ) -> None:
        """初始化 JAR 文件补丁器。

        Args:
            mod_name: 模组名称（通常是 modid），用于标识模组和查找元数据。
            jar_path: 需要被修改的 JAR 文件路径。可为字符串或 pathlib.Path 对象。
                路径会被展开为绝对路径并用于计算工作目录。
            output_dir: 输出目录路径。若为 None，则在原始 JAR 上就地覆盖；
                若提供目录，则在该目录下以源文件同名生成新的 JAR（不会改动源文件）。
                默认为 None。
            validate_jar: 是否在执行补丁前进行原始文件 MD5 校验。为 True 时，会读取
                当前模块目录下的元数据，以类名作为键比对目标 JAR 的 MD5；不匹配将抛出
                断言错误。默认为 True。
        """
        self.mod_name = mod_name
        self.jar_path = Path(jar_path).expanduser().resolve()
        self.code = hashlib.sha256(str(self.jar_path).encode()).hexdigest()[:16]
        self.work_dir = Path.home() / ".cache" / self.code
        self.output_path = Path(output_dir).expanduser().resolve() / self.jar_path.name if output_dir else self.jar_path
        self.validate_jar = validate_jar

    @abstractmethod
    def run(self) -> None:
        """在此方法中实现具体的模组修改逻辑。

        该方法在 JAR 文件解压到工作目录后、重新打包前被调用。
        子类必须实现此方法以执行所需的文件修改操作。
        """
        raise NotImplementedError

    def apply(self) -> None:
        """执行 JAR 文件的补丁流程。

        该方法执行以下步骤：
        1. 验证源 JAR 文件是否存在以及是否符合元数据规范
        2. 执行 MD5 校验（如果启用）
        3. 创建并清理工作目录
        4. 解压 JAR 文件到工作目录
        5. 调用 run() 方法执行具体的修改逻辑
        6. 将修改后的文件重新打包为 JAR
        7. 清理工作目录

        Returns:
            无返回值。

        Raises:
            FileNotFoundError: 当源 JAR 文件不存在时。
            ValueError: 当文件格式不符合规范或 MD5 校验失败时。
        """
        META = _get_meta()

        if not self.jar_path.exists():
            raise FileNotFoundError(f"JAR 文件不存在: {self.jar_path}")
        
        if self.jar_path.name not in META.get(self.mod_name, {}):
            raise ValueError(f"文件格式不符合规范: {self.jar_path.name}")
        
        if self.validate_jar:
            expected_md5 = META[self.mod_name][self.jar_path.name][0]
            actual_md5 = self.md5()
            if expected_md5 != actual_md5:
                raise ValueError(
                    f"MD5 校验失败！期望: {expected_md5}, 实际: {actual_md5}"
                )

        # 1) 准备工作目录
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 2) 解压
        with zipfile.ZipFile(self.jar_path, "r") as z:
            z.extractall(self.work_dir)

        # 3) 修改模组
        self.run()

        # 4) 重打包（覆盖原文件时先写到旁边的临时新文件，再原子替换）
        writing_to_source = (self.output_path == self.jar_path)
        out_path = (
            self.jar_path.with_suffix(self.jar_path.suffix + ".__new__")
            if writing_to_source else self.output_path
        )
        
        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in self.work_dir.rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(self.work_dir).as_posix())

        if writing_to_source:
            os.replace(out_path, self.output_path)

        # 5) 删除工作目录
        shutil.rmtree(self.work_dir)

    def read_json(self, rel: PathLike, encoding: str = 'utf-8') -> Any:
        """从工作目录读取 JSON 文件。

        Args:
            rel: 相对于工作目录的文件路径。可为字符串或 pathlib.Path 对象。
            encoding: 文件编码格式，默认为 'utf-8'。

        Returns:
            解析后的 JSON 数据（字典、列表等）。

        Raises:
            FileNotFoundError: 当指定的文件不存在时。
            json.JSONDecodeError: 当文件内容不是有效的 JSON 格式时。
        """
        with open(self.work_dir / rel, "r", encoding=encoding) as f:
            data = json.load(f)
        return data
    
    def write_json(self, rel: PathLike, data: Any, encoding: str = 'utf-8') -> None:
        """将数据写入工作目录的 JSON 文件。

        Args:
            rel: 相对于工作目录的文件路径。可为字符串或 pathlib.Path 对象。
            data: 要写入的 JSON 数据（字典、列表等可序列化对象）。
            encoding: 文件编码格式，默认为 'utf-8'。

        注意：
            文件会被格式化为带缩进的 JSON（4 个空格），并保留非 ASCII 字符。
        """
        with open(self.work_dir / rel, "w", encoding=encoding) as f:
            json.dump(data, f, indent=_JSON_INDENT, ensure_ascii=False)

    def read_toml(self, rel: PathLike) -> Dict[str, Any]:
        """从工作目录读取 TOML 文件。

        Args:
            rel: 相对于工作目录的文件路径。可为字符串或 pathlib.Path 对象。

        Returns:
            解析后的 TOML 数据（字典形式）。

        Raises:
            FileNotFoundError: 当指定的文件不存在时。
            toml.TomlDecodeError: 当文件内容不是有效的 TOML 格式时。
        """
        data = toml.load(self.work_dir / rel)
        return data
    
    def write_toml(self, rel: PathLike, data: Dict[str, Any], encoding: str = 'utf-8') -> None:
        """将数据写入工作目录的 TOML 文件。

        Args:
            rel: 相对于工作目录的文件路径。可为字符串或 pathlib.Path 对象。
            data: 要写入的 TOML 数据（字典形式）。
            encoding: 文件编码格式，默认为 'utf-8'。
        """
        with open(self.work_dir / rel, "w", encoding=encoding) as f:
            toml.dump(data, f)

    def remove_file(
        self,
        rel: PathLike,
        *,
        keep: list[PathLike] | None = None,
        delete: list[PathLike] | None = None,
    ) -> None:
        """从工作目录的指定文件夹中删除文件。

        可以通过两种方式指定要删除的文件：
        - 使用 `keep` 参数：保留指定文件，删除其余所有文件
        - 使用 `delete` 参数：删除指定的文件

        Args:
            rel: 相对于工作目录的目录路径。可为字符串或 pathlib.Path 对象。
            keep: 要保留的文件名列表（相对于指定目录）。仅当 `delete` 为 None 时使用。
            delete: 要删除的文件名列表（相对于指定目录）。仅当 `keep` 为 None 时使用。

        Returns:
            无返回值。

        Raises:
            ValueError: 当 `keep` 和 `delete` 同时提供或同时为 None 时。
            NotADirectoryError: 当 `rel` 指定的路径不是目录时。

        注意：
            `keep` 和 `delete` 参数必须且仅能提供一个。文件名的匹配基于文件名（不包括路径）。
        """
        if (keep is None) == (delete is None):
            raise ValueError("remove_file: 需在 keep 与 delete 之间二选一（且只能传一个）。")

        dir_path = (self.work_dir / rel).resolve()
        if not dir_path.is_dir():
            raise NotADirectoryError(f"指定的路径不是目录: {dir_path}")

        files = [p for p in dir_path.iterdir() if p.is_file()]

        if delete is not None:
            targets = {Path(x).name for x in delete}
            to_delete = [p for p in files if p.name in targets]
        else:
            keep_set = {Path(x).name for x in keep or []}
            to_delete = [p for p in files if p.name not in keep_set]

        for p in to_delete:
            if p.is_file():
                p.unlink()

    def remove_dir(self, rel: PathLike) -> None:
        """删除工作目录中的指定目录及其所有内容。

        Args:
            rel: 相对于工作目录的目录路径。可为字符串或 pathlib.Path 对象。

        注意：
            如果目录不存在，此方法不会抛出异常，而是静默跳过。
        """
        dir_path = self.work_dir / rel
        if dir_path.exists() and dir_path.is_dir():
            shutil.rmtree(dir_path)

    def md5(self) -> str:
        """计算源 JAR 文件的 MD5 校验值。

        Returns:
            JAR 文件的 MD5 哈希值（十六进制字符串，32 个字符）。

        Raises:
            FileNotFoundError: 当源 JAR 文件不存在时。
        """
        with open(self.jar_path, "rb") as f:
            return hashlib.file_digest(f, hashlib.md5).hexdigest()

    def modify_recipe(
        self,
        recipe_path: PathLike,
        keys_to_update: Dict[str, str],
        keys_to_remove: Optional[List[str]] = None,
        pattern: Optional[List[str]] = None,
    ) -> None:
        """修改 Minecraft 合成配方 JSON 文件。

        该方法用于修改工作目录中的配方文件（recipe.json），支持更新配方键、
        删除配方键以及修改合成模式。

        Args:
            recipe_path: 相对于工作目录的配方文件路径。可为字符串或 pathlib.Path 对象。
                文件将被读取并在原地写回。
            keys_to_update: 配方键到物品/标签的映射字典。键为配方中的字符键（如 "W"、"C" 等），
                值为字符串形式的物品 ID 或标签。值的规范：
                - 以 "#" 开头：视为标签，如 "#minecraft:logs" 会被规范化为
                  `[{"tag": "minecraft:logs"}]`
                - 其他情况：视为具体物品，如 "minecraft:crossbow" 会被规范化为
                  `[{"item": "minecraft:crossbow"}]`
                每个值都会被规范化为只含一个元素的列表。字符串前后的空白会被去除。
            keys_to_remove: 要从配方 "key" 字段中删除的字符键列表。若提供，将逐个删除。
                默认为 None（不执行删除）。注意：不能与 `keys_to_update` 中的键重叠。
            pattern: 可选的合成模式列表（对应配方的 "pattern" 字段）。每个字符串代表一行。
                若提供，将覆盖原有的 pattern。默认为 None（不修改 pattern）。
                例如：["WWW", "W W", "WWW"] 表示一个 3x3 的合成模式。

        Returns:
            无返回值，配方文件会被直接修改。

        Raises:
            ValueError: 当以下情况发生时：
                - `keys_to_update` 和 `keys_to_remove` 存在键冲突时
                - 更新后的配方键与 pattern 中的字符不匹配时
                - `keys_to_update` 中的值不是有效的字符串格式时
            FileNotFoundError: 当配方文件不存在时。
            json.JSONDecodeError: 当配方文件不是有效的 JSON 格式时。

        示例：
            >>> patcher.modify_recipe(
            ...     "data/minecraft/recipes/crafting_table.json",
            ...     keys_to_update={"W": "#minecraft:planks"},
            ...     pattern=["WW", "WW"]
            ... )
        """
        def _normalize_value(v):
            if isinstance(v, str):
                v = v.strip()
                if v.startswith("#"):
                    return [{"tag": v[1:]}]
                return [{"item": v}]
            else:
                raise ValueError("keys 的值必须为字符串（形如 'minecraft:foo' 或 '#namespace:tag'）。")
            
        if keys_to_remove is not None and set(keys_to_remove) & set(keys_to_update.keys()):
            raise ValueError("更新键和删除键出现冲突，请检查")

        recipe_data = self.read_json(recipe_path)
        keys_to_update = {k: _normalize_value(v) for k, v in keys_to_update.items()}

        # 执行删除键
        if keys_to_remove is not None:
            for k in keys_to_remove:
                if k in recipe_data['key']:
                    del recipe_data['key'][k]
                else:
                    print(f"无法删除键{k}，因为它不存在")

        # 执行更新和覆盖
        recipe_data['key'].update(keys_to_update)

        # 更新合成表
        if pattern is not None:
            recipe_data['pattern'] = pattern

        # 校验
        if set(''.join(pattern or recipe_data['pattern']).replace(' ', '')) != set(recipe_data['key'].keys()):
            raise ValueError(
                "合成配方存在未知键，请检查："
                f"{recipe_path}"
            )

        self.write_json(recipe_path, recipe_data)
