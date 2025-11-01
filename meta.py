from mods import *

# 模组元数据字典
# 键：模组名称
# 值：字典，键为 JAR 文件名，值为 (MD5 校验值, 补丁器类) 元组
META: dict[str, dict[str, tuple[str, type]]] = {
    "projecte": {
        # Minecraft 1.21.1
        "ProjectE-1.21.1-PE1.1.0.jar": (
            "a0f0f11aea6c636b2652ea42f773c0b2",
            ProjectEPatcher_1211
        ),
        # Minecraft 1.20.1 系列（使用相同的补丁器）
        "ProjectE-1.20.1-PE1.0.1.jar": (
            "1d62009c904dbd367820ceeadaabefac",
            ProjectEPatcher_1201
        ),
        "ProjectE-1.19.2-PE1.1.0.jar": (
            "ae09bb6b2345da071204a790360609b1",
            ProjectEPatcher_1201
        ),
        "ProjectE-1.18.2-PE1.0.2.jar": (
            "3a73ae740ee7cf05bd38872c12baa2c1",
            ProjectEPatcher_1201
        ),
        "ProjectE-1.16.5-PE1.0.2.jar": (
            "848dc3a796f9723c49e14bf374b2ba58",
            ProjectEPatcher_1201
        ),
        # Minecraft 1.12.2
        "ProjectE-1.12.2-PE1.4.1.jar": (
            "4601ba2741f192bcd01d132aa3e219b5",
            ProjectEPatcher_1122
        ),
    },
    "immersive_aircraft": {
        "immersive_aircraft-1.4.0+1.20.1-forge.jar": (
            "f49ff767f611a95f9bd29a0e9977d9d5",
            ImmersiveAircraftPatcher_1201
        )
    }
}
