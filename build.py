from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from typing import List
import sys

from meta import META


class BuildArgs(BaseSettings):
    """批量构建命令行参数配置类。
    
    参数说明：
        mod_name: 要批量处理的模组名称，必须在 META 中定义
        validate_jar: 是否在修改前验证 JAR 文件的 MD5 校验值
    """
    model_config = SettingsConfigDict(
        cli_prog_name="Minecraft Mod Batch Patcher",
        cli_parse_args=True,
        extra='forbid'
    )
    
    mod_name: str = Field(
        default='projecte',
        description="模组名称（目前仅支持 projecte、immersive_aircraft）"
    )
    
    validate_jar: bool = Field(
        default=True,
        description="修改 MOD 前是否进行原始文件校验（确保 MOD 的来源是 CurseForge/Modrinth）"
    )


def find_jar_files(mod_name: str) -> List[Path]:
    """查找指定模组目录下的所有 JAR 文件。
    
    Args:
        mod_name: 模组名称
        
    Returns:
        JAR 文件路径列表
    """
    src_dir = Path(__file__).parent / "src" / mod_name
    
    if not src_dir.exists():
        print(f"❌ 错误：源目录不存在 {src_dir}")
        return []
    
    jar_files = list(src_dir.glob("*.jar"))
    
    if not jar_files:
        print(f"⚠️  警告：在 {src_dir} 中没有找到任何 JAR 文件")
        return []
    
    return sorted(jar_files)


def process_jar(mod_name: str, jar_path: Path, output_dir: Path, validate_jar: bool) -> bool:
    """处理单个 JAR 文件。
    
    Args:
        mod_name: 模组名称
        jar_path: JAR 文件路径
        output_dir: 输出目录路径
        validate_jar: 是否验证 JAR 文件
        
    Returns:
        处理是否成功
    """
    jar_filename = jar_path.name
    
    # 检查 META 中是否有对应的配置
    if mod_name not in META:
        print(f"  ❌ 跳过：模组 '{mod_name}' 未在 META 中定义")
        return False
    
    mod_meta = META[mod_name]
    
    if jar_filename not in mod_meta:
        print(f"  ⚠️  跳过：{jar_filename} - META 中没有提供对应的补丁器配置")
        return False
    
    # 获取补丁器类
    _, patcher_class = mod_meta[jar_filename]
    
    try:
        print(f"  🔧 处理：{jar_filename}")
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 实例化补丁器并执行补丁操作
        patcher = patcher_class(
            mod_name=mod_name,
            jar_path=str(jar_path),
            output_dir=str(output_dir),
            validate_jar=validate_jar
        )
        patcher.apply()
        
        print(f"  ✅ 完成：{jar_filename} -> {output_dir / jar_filename}")
        return True
        
    except Exception as e:
        print(f"  ❌ 失败：{jar_filename}")
        print(f"     错误信息：{e}")
        return False


def main() -> None:
    """批量构建主程序入口。
    
    执行流程：
        1. 解析命令行参数
        2. 验证模组名称是否支持
        3. 扫描 src/{mod_name}/ 目录下的所有 JAR 文件
        4. 对每个 JAR 文件应用对应的补丁器
        5. 输出处理结果统计
    """
    args = BuildArgs()
    
    print(f"📦 批量构建模组：{args.mod_name}")
    print(f"🔍 MD5 校验：{'启用' if args.validate_jar else '禁用'}")
    print("=" * 60)
    
    # 验证模组名称
    if args.mod_name not in META:
        supported_mods = ", ".join(META.keys())
        print(f"❌ 错误：暂不支持模组 '{args.mod_name}'")
        print(f"支持的模组：{supported_mods}")
        sys.exit(1)
    
    # 查找所有 JAR 文件
    jar_files = find_jar_files(args.mod_name)
    
    if not jar_files:
        print(f"❌ 没有找到可处理的 JAR 文件")
        sys.exit(1)
    
    print(f"找到 {len(jar_files)} 个 JAR 文件\n")
    
    # 设置输出目录
    output_dir = Path(__file__).parent / "out" / args.mod_name
    
    # 处理每个 JAR 文件
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for jar_path in jar_files:
        result = process_jar(args.mod_name, jar_path, output_dir, args.validate_jar)
        
        if result:
            success_count += 1
        elif result is False:
            # 明确处理失败或跳过
            # 检查是否是因为 META 中没有配置
            jar_filename = jar_path.name
            if jar_filename not in META[args.mod_name]:
                skip_count += 1
            else:
                fail_count += 1
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("📊 处理结果统计：")
    print(f"  ✅ 成功：{success_count} 个")
    print(f"  ⚠️  跳过：{skip_count} 个 (META 中无配置)")
    print(f"  ❌ 失败：{fail_count} 个")
    print(f"  📁 输出目录：{output_dir}")
    print("=" * 60)
    
    # 设置退出码
    if fail_count > 0:
        sys.exit(1)
    elif success_count == 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

