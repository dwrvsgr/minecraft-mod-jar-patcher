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
        jar_path: PathLike,
        output_path: PathLike | None = None,
    ) -> None:
        self.jar_path = Path(jar_path).expanduser().resolve()
        self.code = hashlib.sha256(str(self.jar_path).encode()).hexdigest()[:16]
        self.work_dir = Path.home() / ".cache" / self.code
        self.output_path = Path(output_path).expanduser().resolve() / self.jar_path.name if output_path else self.jar_path

    @abstractmethod
    def run(self) -> None:
        """ 在这里实现模组修改方法 """
        raise NotImplementedError

    def apply(self) -> Path:
        if not self.jar_path.exists():
            raise FileNotFoundError(self.jar_path)

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
    
    def write_json(self, rel: PathLike, data, encoding:str = 'utf-8'):
        with open(self.work_dir / rel, "w", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
        shutil.rmtree(self.work_dir / rel)
