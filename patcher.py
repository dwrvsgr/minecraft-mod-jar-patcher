from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
import zipfile
import shutil
import os
import hashlib
import json

PathLike = Union[str, Path]

class JarPatcher(ABC):
    def __init__(
        self,
        mod_name: str,
        jar_path: PathLike,
        output_path: PathLike | None = None,
        validate_jar: bool = True,
    ) -> None:
        """
        Args:

        mod_name (str):
        模组名（通常是modid）

        jar_path (PathLike):
        需要被修改的 JAR 文件路径。可为 str 或 pathlib.Path。会被展开为绝对路径并用于计算工作目录。

        output_path (PathLike | None, optional):
        输出目录（文件夹）路径。若为 None，则在原始 JAR 上就地覆盖；
        若提供目录，则在该目录下以源文件同名生成新的 JAR（不会改动源文件）。默认 None。

        validate_jar (bool, optional):
        是否在执行补丁前进行原始文件 MD5 校验。为 True 时，会读取当前模块目录下的 md5.json，
        以类名作为键比对目标 JAR 的 MD5；不匹配将抛出断言错误。默认 True。
        """
        self.mod_name = mod_name
        self.jar_path = Path(jar_path).expanduser().resolve()
        self.code = hashlib.sha256(str(self.jar_path).encode()).hexdigest()[:16]
        self.work_dir = Path.home() / ".cache" / self.code
        self.output_path = Path(output_path).expanduser().resolve() / self.jar_path.name if output_path else self.jar_path
        self.validate_jar = validate_jar

    @abstractmethod
    def run(self) -> None:
        """ 在这里实现模组修改方法 """
        raise NotImplementedError

    def apply(self) -> Path:
        from meta import META

        if not self.jar_path.exists():
            raise FileNotFoundError(self.jar_path)
        if self.jar_path.stem not in META[self.mod_name]['files'] or self.jar_path.suffix != '.jar':
            raise ValueError("文件格式不符合规范")
        
        if self.validate_jar:
            assert META[self.mod_name]['files'][self.jar_path.stem] == self.md5(), "MD5校验失败！"

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

    def read_json(self, rel: PathLike, encoding:str = 'utf-8'):
        with open(self.work_dir / rel, "r", encoding=encoding) as f:
            data = json.load(f)
        return data
    
    def write_json(self, rel: PathLike, data, encoding:str = 'utf-8', ensure_ascii=False):
        with open(self.work_dir / rel, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=2)

    def remove_file(
        self,
        rel: PathLike,
        *,
        keep: list[PathLike] | None = None,
        delete: list[PathLike] | None = None,
    ) -> list[Path]:
        if (keep is None) == (delete is None):
            raise ValueError("remove_file: 需在 keep 与 delete 之间二选一（且只能传一个）。")

        dir_path = (self.work_dir / rel).resolve()

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
        p = self.work_dir / rel
        if p.exists():
            shutil.rmtree(self.work_dir / rel)

    def md5(self):
        with open(self.jar_path, "rb") as f:
            return hashlib.file_digest(f, hashlib.md5).hexdigest()
