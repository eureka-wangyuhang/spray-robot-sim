import json
from kinematics import GantryRobot


class RobotStateManager:
    """中心化状态管理，Dash回调通过dcc.Store交互"""

    def __init__(self):
        self.robot = GantryRobot()
        self.spray_on = False
        self.mode = 'manual'
        self.path_progress = 0
        self.current_path = []
        self.spray_trail = []
        self.spray_params = {
            'radius': 30,
            'flow_rate': 1.0,
            'speed': 50,
            'swing_angle': 0,
        }
        self.uploaded_image = None
        self.contour_points = []
        self.auto_path = []

    def to_json(self) -> str:
        return json.dumps({
            'position': self.robot.get_position(),
            'spray_on': self.spray_on,
            'mode': self.mode,
            'path_progress': self.path_progress,
            'spray_params': self.spray_params,
            'spray_trail_count': len(self.spray_trail),
        })

    def update_from_json(self, data: dict):
        if 'position' in data:
            pos = data['position']
            self.robot.x = pos['x']
            self.robot.y = pos['y']
            self.robot.z = pos['z']
            if 'swing_angle' in pos:
                self.robot.swing_angle = pos['swing_angle']
        if 'spray_on' in data:
            self.spray_on = data['spray_on']
        if 'mode' in data:
            self.mode = data['mode']
        if 'path_progress' in data:
            self.path_progress = data['path_progress']
