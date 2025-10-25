from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from meta import META


class Args(BaseSettings):
    model_config = SettingsConfigDict(
        cli_prog_name="Minecraft Mod Patcher",
        cli_parse_args=True,
        extra='forbid'
    )
    jar_path: str = Field(
        default='~/Downloads/immersive_aircraft-1.4.0+1.20.1-forge.jar',
        description="MOD文件路径",
    )
    output_dir: str | None = Field(
        description="修改后的MOD文件的输出目录，如果不提供则覆盖原文件",
        default='~/Desktop',
    )
    mod_name: str = Field(
        default='immersive_aircraft',
        description="模组名称（目前仅支持projecte，immersive_aircraft）",
    )
    validate_jar: bool = Field(
        default=True,
        description="修改MOD前是否进行原始文件校验（确保MOD的来源是CurseForge/Modrinth）"
    )



if __name__ == '__main__':
    args = Args()
    if args.mod_name not in META:
        raise ValueError("暂不支持该MOD")
    patcher = META[args.mod_name]["class"](
        mod_name=args.mod_name,
        jar_path=args.jar_path,
        output_dir=args.output_dir,
        validate_jar=args.validate_jar
    )
    patcher.apply()
