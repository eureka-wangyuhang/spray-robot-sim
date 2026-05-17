import numpy as np
from typing import List, Tuple, Dict, Any


class PathPlanner:
    """喷涂路径规划器 - 基于分段的严格顺序运动"""

    def __init__(self, work_area: Tuple[float, float, float, float] = (-450, -250, 450, 250)):
        self.x_min, self.y_min, self.x_max, self.y_max = work_area
        self.spray_z = 250.0
        self.safe_z = 300.0

    def _seg(self, seg_type: str, x: float, y: float, z: float, axes: List[str]) -> Dict[str, Any]:
        """创建一个运动分段"""
        return {
            'type': seg_type,
            'target': {'x': round(x, 2), 'y': round(y, 2), 'z': round(z, 2)},
            'axes': axes,
        }

    def generate_rect_path(self, rows: int = 5, cols: int = 8,
                           start_x: float = 0, start_y: float = 0) -> List[Dict[str, Any]]:
        """矩形路径：沿矩形周界喷涂，形成完整矩形"""
        x0, x1 = self.x_min, self.x_max
        y0, y1 = self.y_min, self.y_max

        segments = []

        # X到位到左下角
        segments.append(self._seg('single_axis', x0, start_y, self.safe_z, ['x']))
        # Y到位到左下角
        segments.append(self._seg('single_axis', x0, y0, self.safe_z, ['y']))
        # Z下降
        segments.append(self._seg('single_axis', x0, y0, self.spray_z, ['z']))

        # 底边: 左→右
        segments.append(self._seg('xy_interp', x1, y0, self.spray_z, ['x', 'y']))
        # 右边: 下→上
        segments.append(self._seg('xy_interp', x1, y1, self.spray_z, ['x', 'y']))
        # 顶边: 右→左
        segments.append(self._seg('xy_interp', x0, y1, self.spray_z, ['x', 'y']))
        # 左边: 上→下
        segments.append(self._seg('xy_interp', x0, y0, self.spray_z, ['x', 'y']))

        # Z抬升
        segments.append(self._seg('single_axis', x0, y0, self.safe_z, ['z']))

        return segments

    def generate_line_path(self, start_x: float = -400, start_y: float = 0,
                           end_x: float = 400, start_pos_x: float = 0,
                           start_pos_y: float = 0) -> List[Dict[str, Any]]:
        """直线路径：单条直线喷涂"""
        segments = []
        # X到位
        segments.append(self._seg('single_axis', start_x, start_pos_y, self.safe_z, ['x']))
        # Z下降
        segments.append(self._seg('single_axis', start_x, start_pos_y, self.spray_z, ['z']))
        # XY插补喷涂
        segments.append(self._seg('xy_interp', end_x, start_y, self.spray_z, ['x', 'y']))
        # Z抬升
        segments.append(self._seg('single_axis', end_x, start_y, self.safe_z, ['z']))
        return segments

    def generate_circle_path(self, center: Tuple[float, float] = (0, 0), radius: float = 200,
                             turns: int = 5, start_x: float = 0, start_y: float = 0) -> List[Dict[str, Any]]:
        """圆形路径：接近→XY插补画圆"""
        x0 = center[0] + radius
        y0 = center[1]
        segments = []
        # X到位
        segments.append(self._seg('single_axis', x0, start_y, self.safe_z, ['x']))
        # Z下降
        segments.append(self._seg('single_axis', x0, start_y, self.spray_z, ['z']))
        # XY插补画圆
        total_points = turns * 60
        prev_x, prev_y = x0, start_y
        for i in range(1, total_points + 1):
            t = i / total_points
            r = radius * (1 - t * 0.8)
            angle = t * turns * 2 * np.pi
            x = center[0] + r * np.cos(angle)
            y = center[1] + r * np.sin(angle)
            if abs(x - prev_x) > 0.01 or abs(y - prev_y) > 0.01:
                segments.append(self._seg('xy_interp', x, y, self.spray_z, ['x', 'y']))
                prev_x, prev_y = x, y
        # Z抬升
        last = segments[-1]['target'] if segments else {'x': x0, 'y': y0}
        segments.append(self._seg('single_axis', last['x'], last['y'], self.safe_z, ['z']))
        return segments

    def generate_zigzag_path(self, direction: str = 'x', lines: int = 10,
                             start_x: float = 0, start_y: float = 0) -> List[Dict[str, Any]]:
        """Z字形路径：两个大Z"""
        x0, x1 = self.x_min, self.x_max
        y0, y1 = self.y_min, self.y_max
        x_mid = (x0 + x1) / 2

        segments = []
        # X到位到左上角
        segments.append(self._seg('single_axis', x0, start_y, self.safe_z, ['x']))
        # Y到位
        segments.append(self._seg('single_axis', x0, y1, self.safe_z, ['y']))
        # Z下降
        segments.append(self._seg('single_axis', x0, y1, self.spray_z, ['z']))

        # 第一个Z: 左上→右上→左中→右中
        segments.append(self._seg('xy_interp', x1, y1, self.spray_z, ['x', 'y']))    # 横
        segments.append(self._seg('xy_interp', x0, (y0 + y1) / 2, self.spray_z, ['x', 'y']))  # 撇
        segments.append(self._seg('xy_interp', x1, (y0 + y1) / 2, self.spray_z, ['x', 'y']))  # 横

        # 第二个Z: 右中→左中→左下→右下
        segments.append(self._seg('xy_interp', x0, y0, self.spray_z, ['x', 'y']))    # 撇
        segments.append(self._seg('xy_interp', x1, y0, self.spray_z, ['x', 'y']))    # 横

        # Z抬升
        segments.append(self._seg('single_axis', x1, y0, self.safe_z, ['z']))

        return segments

    def generate_contour_path(self, contour_points: List[Tuple[float, float]],
                              offset: float = 20, layers: int = 3,
                              height: float = 100) -> List[Tuple[float, float, float]]:
        """轮廓路径（保持原始返回格式，用于视觉引导）"""
        path = []
        for layer in range(layers):
            offset_dist = offset * (layer + 1)
            offset_contour = self._offset_contour(contour_points, -offset_dist)
            if len(offset_contour) < 3:
                break
            for i in range(len(offset_contour)):
                x, y = offset_contour[i]
                path.append((float(x), float(y), float(height)))
            path.append((float(offset_contour[0][0]), float(offset_contour[0][1]), float(height)))
        return path

    def contour_to_segments(self, contour_points: List[Tuple[float, float]],
                            offset: float = 20, layers: int = 3,
                            start_x: float = 0, start_y: float = 0) -> List[Dict[str, Any]]:
        """将轮廓路径转换为分段格式"""
        raw = self.generate_contour_path(contour_points, offset, layers, self.spray_z)
        if not raw:
            return []
        segments = []
        # 接近第一个点
        first = raw[0]
        segments.append(self._seg('single_axis', first[0], start_y, self.safe_z, ['x']))
        segments.append(self._seg('single_axis', first[0], start_y, self.spray_z, ['z']))
        # XY插补遍历轮廓
        prev_x, prev_y = first[0], start_y
        for px, py, pz in raw:
            if abs(px - prev_x) > 0.01 or abs(py - prev_y) > 0.01:
                segments.append(self._seg('xy_interp', px, py, self.spray_z, ['x', 'y']))
                prev_x, prev_y = px, py
        # Z抬升
        last = segments[-1]['target'] if segments else {'x': first[0], 'y': first[1]}
        segments.append(self._seg('single_axis', last['x'], last['y'], self.safe_z, ['z']))
        return segments

    def _offset_contour(self, points: List[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
        points = np.array(points, dtype=np.float64)
        n = len(points)
        offset_points = []
        for i in range(n):
            prev = points[(i - 1) % n]
            curr = points[i]
            next_pt = points[(i + 1) % n]
            edge1 = curr - prev
            edge2 = next_pt - curr
            n1 = np.array([-edge1[1], edge1[0]])
            n2 = np.array([-edge2[1], edge2[0]])
            n1 = n1 / (np.linalg.norm(n1) + 1e-10)
            n2 = n2 / (np.linalg.norm(n2) + 1e-10)
            normal = (n1 + n2) / 2
            normal = normal / (np.linalg.norm(normal) + 1e-10)
            cross = edge1[0] * edge2[1] - edge1[1] * edge2[0]
            sign = 1 if cross > 0 else -1
            offset_point = curr + normal * offset * sign
            offset_points.append(tuple(offset_point))
        return offset_points

    def optimize_path(self, path: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        if len(path) <= 2:
            return path
        optimized = [path[0]]
        remaining = list(range(1, len(path)))
        current = path[0]
        while remaining:
            distances = [
                np.sqrt((path[i][0] - current[0])**2 + (path[i][1] - current[1])**2)
                for i in remaining
            ]
            nearest_idx = remaining[np.argmin(distances)]
            current = path[nearest_idx]
            optimized.append(current)
            remaining.remove(nearest_idx)
        return optimized
