import numpy as np
from typing import List, Dict, Tuple


class GantryRobot:
    """三轴龙门式喷涂机器人运动学模型"""

    def __init__(self):
        self.x_range = (-500.0, 500.0)
        self.y_range = (-300.0, 300.0)
        self.z_range = (250.0, 800.0)  # z_min=250 防止喷枪穿过桌面

        self.x = 0.0
        self.y = 0.0
        self.z = 400.0
        self.swing_angle = 0.0

        self.max_speed = 100.0
        self.acceleration = 500.0

    def get_position(self) -> Dict[str, float]:
        return {
            'x': round(self.x, 2),
            'y': round(self.y, 2),
            'z': round(self.z, 2),
            'swing_angle': round(self.swing_angle, 2)
        }

    def set_position(self, x: float, y: float, z: float) -> Dict[str, float]:
        x = max(self.x_range[0], min(self.x_range[1], x))
        y = max(self.y_range[0], min(self.y_range[1], y))
        z = max(self.z_range[0], min(self.z_range[1], z))
        return {'x': x, 'y': y, 'z': z}

    def move_incremental(self, dx: float, dy: float, dz: float) -> Dict[str, float]:
        new_x = self.x + dx
        new_y = self.y + dy
        new_z = self.z + dz
        pos = self.set_position(new_x, new_y, new_z)
        self.x, self.y, self.z = pos['x'], pos['y'], pos['z']
        return self.get_position()

    def move_to(self, target_x: float, target_y: float, target_z: float, steps: int = 20) -> List[Dict[str, float]]:
        target = self.set_position(target_x, target_y, target_z)
        path = []
        for i in range(steps + 1):
            t = i / steps
            if t < 0.25:
                s = 2 * t * t * 4
            elif t < 0.75:
                s = 0.5 + (t - 0.25) * 2
            else:
                t_dec = (t - 0.75) * 4
                s = 1.0 - 2 * (1 - t_dec) * (1 - t_dec) * 0.5

            px = self.x + (target['x'] - self.x) * s
            py = self.y + (target['y'] - self.y) * s
            pz = self.z + (target['z'] - self.z) * s
            path.append({'x': round(px, 2), 'y': round(py, 2), 'z': round(pz, 2)})

        self.x, self.y, self.z = target['x'], target['y'], target['z']
        return path

    def is_in_workspace(self, x: float, y: float, z: float) -> bool:
        return (self.x_range[0] <= x <= self.x_range[1] and
                self.y_range[0] <= y <= self.y_range[1] and
                self.z_range[0] <= z <= self.z_range[1])
