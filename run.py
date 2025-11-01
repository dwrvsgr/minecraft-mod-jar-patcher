from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

from meta import META


class Args(BaseSettings):
    """命令行参数配置类。
    
    使用 Pydantic Settings 自动解析命令行参数，支持环境变量和配置文件。
    所有参数都可以通过命令行、环境变量或配置文件进行配置。
    
    参数说明：
        mod_name: 要处理的模组名称，必须在 META 中定义
        jar_path: 输入的 JAR 文件路径（支持 ~ 展开）
        output_dir: 输出目录，如果为 None 则覆盖原文件
        validate_jar: 是否在修改前验证 JAR 文件的 MD5 校验值
    """
    model_config = SettingsConfigDict(
        cli_prog_name="Minecraft Mod Patcher",
        cli_parse_args=True,
        extra='forbid'  # 禁止额外的未定义参数
    )
    
    mod_name: str = Field(
        default='projecte',
        description="模组名称（目前仅支持 projecte、immersive_aircraft）"
    )
    
    jar_path: str = Field(
        default='~/Downloads/ProjectE-1.12.2-PE1.4.1.jar',
        description="MOD 文件路径（支持 ~ 展开为用户主目录）"
    )
    
    output_dir: str | None = Field(
        default='~/Desktop',
        description="修改后的 MOD 文件的输出目录，如果不提供则覆盖原文件"
    )
    
    validate_jar: bool = Field(
        default=True,
        description="修改 MOD 前是否进行原始文件校验（确保 MOD 的来源是 CurseForge/Modrinth）"
    )


def main() -> None:
    """主程序入口。
    
    执行流程：
        1. 解析命令行参数
        2. 验证模组名称是否支持
        3. 从 META 中获取对应的补丁器类
        4. 实例化补丁器并执行补丁操作
    
    Raises:
        ValueError: 当模组名称不支持或 JAR 文件名不在 META 中时
        KeyError: 当 JAR 文件名在 META 中找不到时
    """
    args = Args()
    
    # 验证模组名称
    if args.mod_name not in META:
        supported_mods = ", ".join(META.keys())
        raise ValueError(
            f"暂不支持模组 '{args.mod_name}'。"
            f"支持的模组：{supported_mods}"
        )
    
    # 获取 JAR 文件名
    jar_filename = Path(args.jar_path).name
    
    # 从 META 中获取补丁器配置
    mod_meta = META[args.mod_name]
    if jar_filename not in mod_meta:
        supported_jars = ", ".join(mod_meta.keys())
        raise ValueError(
            f"模组 '{args.mod_name}' 不支持 JAR 文件 '{jar_filename}'。"
            f"支持的 JAR 文件：{supported_jars}"
        )
    
    # 获取补丁器类（元组的第二个元素）
    _, patcher_class = mod_meta[jar_filename]
    
    # 实例化补丁器并执行补丁操作
    patcher = patcher_class(
        mod_name=args.mod_name,
        jar_path=args.jar_path,
        output_dir=args.output_dir,
        validate_jar=args.validate_jar
    )
    patcher.apply()


if __name__ == '__main__':
    main()
