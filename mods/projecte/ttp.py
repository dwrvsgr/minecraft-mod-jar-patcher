from PIL import Image
import colorsys
from pathlib import Path


class TransmutationTabletPainter:
    """交易终端材质绘制器。
    
    此类用于将图像中的红色/粉色像素重新着色为蓝色渐变，生成自定义的交易终端材质。
    
    初始化参数：
        version (str): 版本字符串，可选值："v2", "v3", "v4", "v5", "v6", "v7"
        input_path (str | Path): 输入图片文件路径
    
    使用示例：
        >>> painter = TransmutationTabletPainter("v7", "/path/to/transmutation_tablet.png")
        >>> painter.paint("/path/to/output.png")
    
    工作原理：
        1. 读取输入图像并转换为 RGBA 格式
        2. 遍历每个像素，判断是否为红色/粉色系
        3. 对红色/粉色像素：
           - 计算感知亮度 Y
           - 生成渐变参数 t = 1 - Y/255
           - 应用版本化的缩放、偏移和伽马校正
           - 使用蓝色渐变调色板进行颜色映射
        4. 非红色/粉色像素保持原样
        5. 保存处理后的图像
    """

    # ===== 调色盘与映射参数 =====
    # 说明（这部分解释 paint() 如何使用下方参数）：
    # 1) 仅当像素被 is_reddish_or_pink() 判定为“红/洋红/粉系”时才会重着色；其它像素保持原样。
    # 2) 对命中的像素，先以感知亮度 Y 生成 t = 1 - Y/255（亮像素→t 小、靠高光；暗像素→t 大、靠阴影）。
    # 3) 然后依次应用：
    #    • t_scale：缩放深浅；>1 整体更深，<1 整体更浅。
    #    • t_bias ：线性偏移；>0 再向阴影推一点，<0 向高光推一点。以上两步后都会夹紧到 [0,1]。
    #    • t_gamma：幂函数对比；<1 提升中间调（数值变大，整体更深），>1 压低中间调（整体更浅），=1 不变。
    # 4) gradient_color() 用 5 个 stop 做 4 段线性插值。若相邻两个 stop 完全相同，则该 1/4 t 区间为平台（恒色段）。
    # 5) t 越大，越取向 stops 末端（更深色）。
    PALETTES = {
        # v2：浅调的蓝色梯度；映射略向阴影侧偏（因为 0.95* t + 0.05，整体比 t 稍大）
        "v2": {
            "stops": [
                (180, 233, 255),  # 高光：最浅的蓝青
                (125, 225, 255),  # 亮蓝：接近高光的亮部
                (85,  205, 255),  # 主体蓝：中亮区
                (55,  170, 220),  # 次阴影：偏暗
                (25,  120, 180),  # 深阴影：最深
            ],
            # t = 1 - Y/255 → t' = clamp(t*0.95 + 0.05)
            # 结果：整体略偏深；t_gamma=1 无额外对比变化
            "t_scale": 0.95,
            "t_bias":  0.05,
            "t_gamma": 1.00,
        },

        # v3：更深的蓝色梯度；映射强力压向阴影（>1 的 scale、正 bias、且 gamma<1 推高中间调）
        "v3": {
            "stops": [
                (150, 215, 245),  # 高光（较 v2 更深）
                (100, 200, 240),  # 亮蓝
                (70,  175, 235),  # 主体蓝（中段）
                (42,  145, 205),  # 次阴影
                (18,   95, 155),  # 深阴影（最深）
            ],
            # t' = clamp(t*1.18 + 0.08)；t_gamma=0.92（<1）进一步加深中间调 → 整体明显更深
            "t_scale": 1.18,
            "t_bias":  0.08,
            "t_gamma": 0.92,
        },

        # v4：B1, B2沿用v3，B3沿用v2（B1,B2,B3是三挡蓝色，由深到浅）
        "v4": {  # NEW: v4
            "stops": [
                (180, 233, 255),  # B3（最浅）取自 v2 的高光
                (180, 233, 255),  # 与上相同 → 第 0 段为平台（恒色）
                (70,  175, 235),  # B2（中间）取自 v3 的主体蓝
                (70,  175, 235),  # 与上相同 → 第 2 段为平台（恒色）
                (18,   95, 155),  # B1（最深）取自 v3 的深阴影
            ],
            # 平台分布：t∈[0,0.25) 恒 B3；[0.25,0.5) 由 B3 过渡到 B2；[0.5,0.75) 恒 B2；[0.75,1] 由 B2 过渡到 B1
            # 映射参数沿用 v3 → 整体更深、对比略加强（中间调推深）
            "t_scale": 1.18,     # 采用 v3 的整体深度映射
            "t_bias":  0.08,
            "t_gamma": 0.92,
        },

        # v5：B1沿用v3，B2，B3沿用v2
        "v5": {  # NEW: v5
            "stops": [
                (180, 233, 255),  # B3（最浅）= v2 的高光
                (180, 233, 255),  # 平台：恒 B3
                (85,  205, 255),  # B2（中间）= v2 的主体蓝（注意：不是 v3 的 70,175,235）
                (85,  205, 255),  # 平台：恒 B2
                (18,   95, 155),  # B1（最深）= v3 的深阴影
            ],
            # 平台/过渡结构与 v4 相同，但由于 B2 更亮，整体观感较 v4 稍浅；映射仍承袭 v3（总体偏深）
            "t_scale": 1.18,     # 沿用 v3 的深度映射
            "t_bias":  0.08,
            "t_gamma": 0.92,
        },

        # v6：沿用v5，但是把B1改成了介于v2和v3的B1
        "v6": {
            "stops": [
                (180, 233, 255),  # B3（最浅）取自 v2 的高光
                (180, 233, 255),  # 与上相同 → 第 0 段为平台（恒色）
                (85,  205, 255),  # B2（中间）= v2 的主体蓝（注意：不是 v3 的 70,175,235）
                (85,  205, 255),  # 平台：恒 B2
                (22,  110, 170),  # B1（最深）取自 v3 的深阴影
            ],
            # 平台分布：t∈[0,0.25) 恒 B3；[0.25,0.5) 由 B3 过渡到 B2；[0.5,0.75) 恒 B2；[0.75,1] 由 B2 过渡到 B1
            # 映射参数沿用 v3 → 整体更深、对比略加强（中间调推深）
            "t_scale": 1.18,     # 采用 v3 的整体深度映射
            "t_bias":  0.08,
            "t_gamma": 0.92,
        },

        # v7：沿用v6，但是把B2改成了介于v2和v3的B2
        "v7": {
            "stops": [
                (180, 233, 255),  # B3（最浅）取自 v2 的高光
                (180, 233, 255),  # 与上相同 → 第 0 段为平台（恒色）
                (76,  187, 243),  # B2（中间）= v2 的主体蓝（注意：不是 v3 的 70,175,235）
                (76,  187, 243),  # 平台：恒 B2
                (22,  110, 170),  # B1（最深）取自 v3 的深阴影
            ],
            # 平台分布：t∈[0,0.25) 恒 B3；[0.25,0.5) 由 B3 过渡到 B2；[0.5,0.75) 恒 B2；[0.75,1] 由 B2 过渡到 B1
            # 映射参数沿用 v3 → 整体更深、对比略加强（中间调推深）
            "t_scale": 1.18,     # 采用 v3 的整体深度映射
            "t_bias":  0.08,
            "t_gamma": 0.92,
        },
    }

    @staticmethod
    def lerp(a, b, t):
        """线性插值。
        
        在 a 和 b 之间进行线性插值。
        
        Args:
            a (int): 起始值
            b (int): 结束值
            t (float): 插值参数，取值范围 [0, 1]
                - t=0 时返回 a
                - t=1 时返回 b
                - t=0.5 时返回 a 和 b 的中点
        
        Returns:
            int: 插值结果（四舍五入到最近的整数）
        """
        return int(round(a + (b - a) * t))

    @classmethod
    def gradient_color(cls, stops, t):
        """根据渐变参数 t 计算渐变颜色。
        
        使用 5 个颜色停止点（stops）进行 4 段分段线性插值。
        若相邻两个停止点相同，则该段为平台（恒色段）。
        
        Args:
            stops (list[tuple[int, int, int]]): 5 个 RGB 颜色停止点
            t (float): 渐变参数，取值范围 [0, 1]
                - t=0 对应 stops[0]（最浅色）
                - t=1 对应 stops[4]（最深色）
                - 中间值在相邻停止点之间线性插值
        
        Returns:
            tuple[int, int, int]: RGB 颜色值 (r, g, b)
        
        注意：
            - t 会被夹紧到 [0, 1] 范围
            - 5 个停止点被分为 4 段：[0,0.25), [0.25,0.5), [0.5,0.75), [0.75,1]
        """
        # 将 t 夹紧到 [0, 1] 范围
        t = max(0.0, min(1.0, t))
        # 计算 t 所在的段索引（0..3）
        seg = min(int(t * 4), 3)
        # 计算段的起始位置
        t0 = seg / 4.0
        # 计算段内的局部插值参数
        local_t = (t - t0) * 4.0
        # 获取该段的两个停止点
        c1, c2 = stops[seg], stops[seg + 1]
        # 对 RGB 三个通道分别进行线性插值
        return (
            cls.lerp(c1[0], c2[0], local_t),
            cls.lerp(c1[1], c2[1], local_t),
            cls.lerp(c1[2], c2[2], local_t),
        )

    @staticmethod
    def is_reddish_or_pink(r, g, b):
        """判断像素是否为红色/粉色系。
        
        使用 HSV 和 RGB 两种颜色空间进行判断，以提高识别准确性。
        - HSV 空间：捕捉高饱和度的红色/洋红色
        - RGB 空间：捕捉低饱和度的浅粉色
        
        Args:
            r (int): 红色通道值，范围 [0, 255]
            g (int): 绿色通道值，范围 [0, 255]
            b (int): 蓝色通道值，范围 [0, 255]
        
        Returns:
            bool: 如果像素被判定为红色/粉色系，返回 True；否则返回 False
        
        HSV 判断条件：
            - 色相（hue）在红色范围：0~21° 或 306°~360°
            - 或色相在洋红色范围：281°~306°
            - 且饱和度（saturation）>= 0.08
            - 且明度（value）>= 0.15
        
        RGB 判断条件：
            - r >= 140 且 r 明显大于 g 和 b（差值 >= 8）
            - 或 r >= 200 且 g 或 b >= 150（高亮粉色）
        """
        # 归一化到 [0, 1] 范围
        rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)
        
        # HSV 空间判断：红色（0~21° 或 306°~360°）和洋红色（281°~306°）
        red_hue = (h <= 0.06) or (h >= 0.85)  # 0~21° 或 306°~360°
        magenta_hue = (0.78 <= h <= 0.85)  # 281°~306°
        hsv_hit = (red_hue or magenta_hue) and s >= 0.08 and v >= 0.15
        
        # RGB 空间判断：捕捉低饱和度的浅粉色
        rgb_hit = (
            (r >= 140 and r >= g + 8 and r >= b + 8) or
            (r >= 200 and (g >= 150 or b >= 150))
        )
        
        return hsv_hit or rgb_hit

    @staticmethod
    def luminance(r, g, b):
        """计算感知亮度（Perceptual Luminance）。
        
        使用 ITU-R BT.709 标准权重计算 RGB 颜色的感知亮度。
        这个公式考虑了人眼对不同颜色通道的敏感度差异。
        
        Args:
            r (int): 红色通道值，范围 [0, 255]
            g (int): 绿色通道值，范围 [0, 255]
            b (int): 蓝色通道值，范围 [0, 255]
        
        Returns:
            float: 感知亮度值，范围 [0, 255]
        
        权重说明：
            - 绿色权重最高（0.7152），因为人眼对绿色最敏感
            - 红色权重中等（0.2126）
            - 蓝色权重最低（0.0722），因为人眼对蓝色最不敏感
        """
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def __init__(self, version, input_path):
        """初始化绘制器。
        
        Args:
            version (str): 版本字符串，必须在 PALETTES 中存在
            input_path (str | Path): 输入图片文件路径
        
        Raises:
            FileNotFoundError: 当输入文件不存在时
        """
        self.version = version
        self.input_path = Path(input_path).expanduser().resolve()

    def paint(self, output_path):
        """执行像素重着色并保存结果。
        
        遍历输入图像的所有像素，将红色/粉色像素重新着色为蓝色渐变，
        其他像素和透明度通道保持不变。
        
        Args:
            output_path (str | Path): 输出图片文件路径
        
        Raises:
            ValueError: 当版本字符串不在支持的版本列表中时
            FileNotFoundError: 当输入文件不存在时
            IOError: 当无法保存输出文件时
        
        处理流程：
            1. 验证版本并加载对应的调色板配置
            2. 打开输入图像并转换为 RGBA 格式
            3. 遍历每个像素：
               - 透明像素：直接输出透明
               - 红色/粉色像素：计算渐变参数并应用蓝色渐变
               - 其他像素：保持原样
            4. 保存处理后的图像
        """
        if self.version not in self.PALETTES:
            raise ValueError(
                f"未知版本：{self.version}，可选：{list(self.PALETTES.keys())}"
            )

        # 加载版本对应的调色板配置
        cfg = self.PALETTES[self.version]
        stops = cfg["stops"]
        t_scale = cfg["t_scale"]
        t_bias = cfg["t_bias"]
        t_gamma = cfg["t_gamma"]

        # 打开输入图像并转换为 RGBA 格式
        img = Image.open(self.input_path).convert("RGBA")
        w, h = img.size
        px = img.load()
        out = Image.new("RGBA", (w, h))

        # 遍历所有像素进行重着色
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                
                # 透明像素直接输出透明
                if a == 0:
                    out.putpixel((x, y), (0, 0, 0, 0))
                    continue

                # 判断是否为红色/粉色像素
                if self.is_reddish_or_pink(r, g, b):
                    # 计算感知亮度
                    Y = self.luminance(r, g, b)
                    # 生成初始渐变参数：亮像素→t 小（接近高光），暗像素→t 大（接近阴影）
                    t = 1.0 - (Y / 255.0)

                    # 应用版本化的缩放和偏移
                    # t_scale: 缩放深浅（>1 整体更深，<1 整体更浅）
                    # t_bias: 线性偏移（>0 向阴影推，<0 向高光推）
                    t = min(1.0, max(0.0, t * t_scale + t_bias))
                    
                    # 应用伽马校正（调整对比度）
                    # t_gamma < 1: 提升中间调（整体更深）
                    # t_gamma > 1: 压低中间调（整体更浅）
                    # t_gamma = 1: 无变化
                    if t_gamma != 1.0:
                        t = max(0.0, min(1.0, t ** t_gamma))

                    # 根据渐变参数计算新的 RGB 颜色
                    nr, ng, nb = self.gradient_color(stops, t)
                    out.putpixel((x, y), (nr, ng, nb, a))
                else:
                    # 非红色/粉色像素保持原样
                    out.putpixel((x, y), (r, g, b, a))

        # 保存处理后的图像
        out_path = str(Path(output_path).expanduser().resolve())
        out.save(out_path)


if __name__ == '__main__':
    # 测试代码：生成 v7 版本的材质
    # 用于开发和测试目的，生成交易终端材质的不同版本
    painter = TransmutationTabletPainter(
        "v7",
        "~/Desktop/transmutation_tablet.png"
    )
    painter.paint("~/Desktop/transmutation_tablet_v7.png")
