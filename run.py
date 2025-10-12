from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from meta import META


class Args(BaseSettings):
    model_config = SettingsConfigDict(
        cli_prog_name="Minecraft Mod Patcher",
        cli_parse_args=True,
        cli_kebab_case=True,
        cli_implicit_flags=True,
        extra='forbid'
    )

    jar_path: str = Field(
        description="MOD文件路径",
        default="~/Downloads/ProjectE-1.20.1-PE1.0.1.jar"
    )
    output_path: str = Field(
        description="修改后的MOD文件的输出目录",
        default="~/Desktop"
    )
    mod_name: str = Field(
        description="模组名称",
        default="projecte"
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
        output_path=args.output_path,
        validate_jar=args.validate_jar
    )
    patcher.apply()
