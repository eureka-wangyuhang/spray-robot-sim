import numpy as np
import base64
import io
from PIL import Image
from typing import Tuple, Dict


class SpraySimulator:
    """喷涂效果模拟器 - 厚度分布与颜色"""

    def __init__(self, table_width: float = 1000, table_height: float = 600, resolution: float = 2):
        self.resolution = resolution
        self.tex_w = int(table_width * resolution)
        self.tex_h = int(table_height * resolution)
        self.thickness_map = np.zeros((self.tex_h, self.tex_w), dtype=np.float32)
        self.color_map = np.zeros((self.tex_h, self.tex_w, 4), dtype=np.uint8)
        self.dirty = False

    def apply_spray(self, x: float, y: float, z: float, radius: float, flow_rate: float, color_rgb: Tuple[int, int, int]):
        tex_x = int((x + 500) * self.resolution)
        tex_y = int((-y + 300) * self.resolution)

        if not (0 <= tex_x < self.tex_w and 0 <= tex_y < self.tex_h):
            return

        r_px = int(radius * self.resolution)
        y_start = max(0, tex_y - r_px)
        y_end = min(self.tex_h, tex_y + r_px)
        x_start = max(0, tex_x - r_px)
        x_end = min(self.tex_w, tex_x + r_px)

        # 向量化计算，替代逐像素循环
        yy, xx = np.mgrid[y_start:y_end, x_start:x_end]
        dist = np.sqrt((xx - tex_x)**2 + (yy - tex_y)**2) / self.resolution
        mask = dist <= radius
        if not np.any(mask):
            return

        cos_factor = np.cos(dist[mask] / radius * np.pi / 2)
        thickness_delta = flow_rate * cos_factor * 0.1

        self.thickness_map[y_start:y_end, x_start:x_end][mask] += thickness_delta
        t = np.minimum(self.thickness_map[y_start:y_end, x_start:x_end][mask], 1.0)

        region = self.color_map[y_start:y_end, x_start:x_end]
        old = region[mask].astype(np.float32)
        cr, cg, cb = color_rgb
        new_r = (cr * t + old[:, 0] * (1 - t)).astype(np.uint8)
        new_g = (cg * t + old[:, 1] * (1 - t)).astype(np.uint8)
        new_b = (cb * t + old[:, 2] * (1 - t)).astype(np.uint8)
        new_a = np.minimum((t * 255).astype(np.uint8), 255)
        region[mask] = np.column_stack([new_r, new_g, new_b, new_a])
        self.dirty = True

    def get_texture_png_base64(self) -> str:
        self.dirty = False
        img = Image.fromarray(self.color_map, 'RGBA')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def get_heatmap_png_base64(self) -> str:
        nonzero = self.thickness_map[self.thickness_map > 0]
        if len(nonzero) == 0:
            img = Image.fromarray(np.zeros((self.tex_h, self.tex_w, 4), dtype=np.uint8), 'RGBA')
        else:
            t_max = float(nonzero.max())
            v = self.thickness_map / max(t_max, 1e-6)
            heatmap = np.zeros((self.tex_h, self.tex_w, 4), dtype=np.uint8)
            mask = v > 0
            # 蓝→绿→黄→红 向量化
            r = np.zeros_like(v)
            g = np.zeros_like(v)
            b = np.zeros_like(v)
            m1 = mask & (v < 0.25)
            g[m1] = v[m1] * 4 * 255; b[m1] = 255
            m2 = mask & (v >= 0.25) & (v < 0.5)
            t2 = (v[m2] - 0.25) * 4; g[m2] = 255; b[m2] = (1 - t2) * 255
            m3 = mask & (v >= 0.5) & (v < 0.75)
            t2 = (v[m3] - 0.5) * 4; r[m3] = t2 * 255; g[m3] = 255
            m4 = mask & (v >= 0.75)
            t2 = (v[m4] - 0.75) * 4; r[m4] = 255; g[m4] = (1 - t2) * 255
            heatmap[mask, 0] = r[mask].astype(np.uint8)
            heatmap[mask, 1] = g[mask].astype(np.uint8)
            heatmap[mask, 2] = b[mask].astype(np.uint8)
            heatmap[mask, 3] = np.minimum((v[mask] * 255).astype(np.uint8), 255)
            img = Image.fromarray(heatmap, 'RGBA')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def clear(self):
        self.thickness_map[:] = 0
        self.color_map[:] = 0
        self.dirty = False

    def get_thickness_stats(self) -> Dict[str, float]:
        nonzero = self.thickness_map[self.thickness_map > 0]
        if len(nonzero) == 0:
            return {'min': 0, 'max': 0, 'mean': 0, 'coverage': 0}
        return {
            'min': float(nonzero.min()),
            'max': float(nonzero.max()),
            'mean': float(nonzero.mean()),
            'coverage': len(nonzero) / self.thickness_map.size * 100
        }
