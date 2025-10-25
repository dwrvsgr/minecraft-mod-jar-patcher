from PIL import Image
import colorsys
from pathlib import Path


class TransmutationTabletPainter:
    """
    初始化参数：
        - version: 版本字符串，如 "v2" / "v3" / "v4" / "v5"
        - input_path: 输入图片文件路径
    使用：
        painter = TransmutationTabletPainter("v5", "/path/to/transmutation_tablet.png")
        painter.paint("/path/to/output.png")
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
        "v6": {  # NEW: v4
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
        "v7": {  # NEW: v4
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
        return int(round(a + (b - a) * t))

    @classmethod
    def gradient_color(cls, stops, t):
        # t ∈ [0,1]，5段分段线性插值
        t = max(0.0, min(1.0, t))
        seg = min(int(t * 4), 3)      # 0..3
        t0 = seg / 4.0
        local_t = (t - t0) * 4.0
        c1, c2 = stops[seg], stops[seg + 1]
        return (
            cls.lerp(c1[0], c2[0], local_t),
            cls.lerp(c1[1], c2[1], local_t),
            cls.lerp(c1[2], c2[2], local_t),
        )

    @staticmethod
    def is_reddish_or_pink(r, g, b):
        # HSV 抓红/洋红/粉；RGB 补捉低饱和浅粉
        rf, gf, bf = r/255.0, g/255.0, b/255.0
        h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)
        red_hue = (h <= 0.06) or (h >= 0.85)     # 0~21° 或 306°~360°
        magenta_hue = (0.78 <= h <= 0.85)        # 281°~306°
        hsv_hit = (red_hue or magenta_hue) and s >= 0.08 and v >= 0.15
        rgb_hit = (r >= 140 and r >= g + 8 and r >= b + 8) or (r >= 200 and (g >= 150 or b >= 150))
        return hsv_hit or rgb_hit

    @staticmethod
    def luminance(r, g, b):
        # 感知亮度
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def __init__(self, version, input_path):
        self.version = version
        self.input_path = Path(input_path).expanduser().resolve()

    def paint(self, output_path):
        version = self.version
        if version not in self.PALETTES:
            raise ValueError(f"未知版本：{version}，可选：{list(self.PALETTES.keys())}")

        cfg = self.PALETTES[version]
        stops   = cfg["stops"]
        t_scale = cfg["t_scale"]
        t_bias  = cfg["t_bias"]
        t_gamma = cfg["t_gamma"]

        img = Image.open(self.input_path).convert("RGBA")
        w, h = img.size
        px = img.load()
        out = Image.new("RGBA", (w, h))
        hit = 0

        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    out.putpixel((x, y), (0, 0, 0, 0))
                    continue

                if self.is_reddish_or_pink(r, g, b):
                    hit += 1
                    # 原始映射：亮像素更接近高光蓝，暗像素更接近阴影蓝
                    Y = self.luminance(r, g, b)
                    t = 1.0 - (Y / 255.0)

                    # 版本化的整体偏移/缩放 + 可选对比
                    t = min(1.0, max(0.0, t * t_scale + t_bias))
                    if t_gamma != 1.0:
                        t = max(0.0, min(1.0, t ** t_gamma))

                    nr, ng, nb = self.gradient_color(stops, t)
                    out.putpixel((x, y), (nr, ng, nb, a))
                else:
                    out.putpixel((x, y), (r, g, b, a))

        out_path = str(Path(output_path).expanduser().resolve())
        out.save(out_path)


if __name__ == '__main__':
    for i in range(6, 7):
        if not i:
            continue
        painter = TransmutationTabletPainter(f"v{i + 1}", "~/Desktop/transmutation_tablet.png")
        painter.paint(f"~/Desktop/transmutation_tablet_v{i + 1}.png")
