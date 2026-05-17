import json
import math
import dash
from dash import html, Input, Output, State, clientside_callback, ClientsideFunction
from state_manager import RobotStateManager
from spray_sim import SpraySimulator
from path_planner import PathPlanner

def register_callbacks(app, state: RobotStateManager,
                       spray_sim: SpraySimulator, planner: PathPlanner):

    # 回调1: 滑块变化 → 更新位置 + 状态显示 + 路径重新规划（仅模板路径）
    @app.callback(
        [Output('robot-state', 'data'),
         Output('x-value', 'children'),
         Output('y-value', 'children'),
         Output('z-value', 'children'),
         Output('swing-value', 'children'),
         Output('path-data', 'data', allow_duplicate=True)],
        [Input('x-slider', 'value'),
         Input('y-slider', 'value'),
         Input('z-slider', 'value'),
         Input('swing-slider', 'value')],
        [State('path-template', 'value'),
         State('path-data', 'data')],
        prevent_initial_call=True
    )
    def update_from_sliders(x, y, z, swing, template, current_path):
        if x is None: x = 0
        if y is None: y = 0
        if z is None: z = 400
        if swing is None: swing = 0
        state.robot.x = x
        state.robot.y = y
        state.robot.z = z
        state.robot.swing_angle = swing
        pos = {'x': x, 'y': y, 'z': z}
        # 仅已有模板路径才重新规划，无路径或自定义路径不自动生成
        if isinstance(current_path, dict) and current_path.get('segments') and current_path.get('source') == 'template':
            path_data = _regenerate_path(template or '矩形', pos)
        else:
            path_data = dash.no_update
        return (state.to_json(),
                f'X: {x}', f'Y: {y}', f'Z: {z}',
                f'角度: {swing}°',
                path_data)

    # 回调2: 方向按钮 → 增量移动 + 路径重新规划
    @app.callback(
        [Output('robot-state', 'data', allow_duplicate=True),
         Output('path-data', 'data', allow_duplicate=True)],
        [Input('btn-x-plus', 'n_clicks'),
         Input('btn-x-minus', 'n_clicks'),
         Input('btn-y-plus', 'n_clicks'),
         Input('btn-y-minus', 'n_clicks'),
         Input('btn-z-plus', 'n_clicks'),
         Input('btn-z-minus', 'n_clicks')],
        [State('step-size', 'value'),
         State('robot-state', 'data'),
         State('path-template', 'value'),
         State('path-data', 'data')],
        prevent_initial_call=True
    )
    def update_from_buttons(xp, xm, yp, ym, zp, zm, step, state_json, template, current_path):
        if step is None:
            step = 10
        ctx = dash.callback_context
        if not ctx.triggered:
            return state_json, dash.no_update
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        delta_map = {
            'btn-x-plus': (step, 0, 0),
            'btn-x-minus': (-step, 0, 0),
            'btn-y-plus': (0, step, 0),
            'btn-y-minus': (0, -step, 0),
            'btn-z-plus': (0, 0, step),
            'btn-z-minus': (0, 0, -step),
        }
        dx, dy, dz = delta_map.get(button_id, (0, 0, 0))
        state.robot.move_incremental(dx, dy, dz)
        pos = {'x': state.robot.x, 'y': state.robot.y, 'z': state.robot.z}
        # 仅已有模板路径才重新规划，无路径或自定义路径不自动生成
        if isinstance(current_path, dict) and current_path.get('segments') and current_path.get('source') == 'template':
            path_data = _regenerate_path(template or '矩形', pos)
        else:
            path_data = dash.no_update
        return state.to_json(), path_data

    # 回调3: 喷涂开关
    @app.callback(
        Output('robot-state', 'data', allow_duplicate=True),
        Input('spray-switch', 'value'),
        State('robot-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_spray(value, state_json):
        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        data['spray_on'] = bool(value)
        state.spray_on = bool(value)
        return json.dumps(data)

    # 回调5: 开始自动喷涂 → 生成frames + 启动动画
    @app.callback(
        [Output('robot-state', 'data', allow_duplicate=True),
         Output('path-data', 'data', allow_duplicate=True),
         Output('animation-control', 'data', allow_duplicate=True)],
        Input('btn-auto-start', 'n_clicks'),
        [State('path-template', 'value'),
         State('robot-state', 'data'),
         State('spray-radius', 'value'),
         State('spray-color', 'value'),
         State('flow-rate', 'value'),
         State('contour-data', 'data'),
         State('path-data', 'data')],
        prevent_initial_call=True
    )
    def start_auto_spray(n, template, state_json, radius, spray_color_name, flow_rate, contour_data, path_data):
        if n is None:
            return dash.no_update, dash.no_update, dash.no_update

        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        pos = data.get('position', {'x': 0, 'y': 0, 'z': 400})
        sx, sy = pos.get('x', 0), pos.get('y', 0)

        # 生成分段路径
        segments = None
        if path_data and isinstance(path_data, dict) and path_data.get('segments'):
            segments = path_data['segments']

        if not segments:
            if isinstance(contour_data, str):
                try:
                    contour_data = json.loads(contour_data) if contour_data.strip() else []
                except (json.JSONDecodeError, ValueError):
                    contour_data = []

            if template == '矩形':
                segments = planner.generate_rect_path(rows=5, cols=8, start_x=sx, start_y=sy)
            elif template == '直线':
                segments = planner.generate_line_path(start_x=-400, start_y=sy,
                                                      end_x=400, start_pos_x=sx, start_pos_y=sy)
            elif template == '圆形':
                segments = planner.generate_circle_path(start_x=sx, start_y=sy)
            elif template == 'Z字形':
                segments = planner.generate_zigzag_path(start_x=sx, start_y=sy)
            elif template == '轮廓跟随' and contour_data:
                all_segments = []
                for contour in contour_data:
                    pts = [(p['x'], p['y']) for p in contour]
                    segs = planner.contour_to_segments(
                        pts, offset=(radius or 30) * 0.7, layers=5,
                        start_x=sx, start_y=sy
                    )
                    all_segments.extend(segs)
                segments = all_segments

        if not segments:
            return dash.no_update, dash.no_update, dash.no_update

        # 构建path_data（含segments和可视化轨迹）
        new_path_data = _build_path_data_from_segments(segments, start_pos=pos, table_y=sy)

        # 生成动画帧序列
        speed = data.get('spray_speed', 50)
        frames = _build_animation_frames(segments, start_pos=pos, speed=speed)
        new_path_data['frames'] = frames
        new_path_data['initial_table_y'] = sy

        data['mode'] = 'auto'
        data['spray_on'] = False

        return json.dumps(data), new_path_data, {'cmd': 'start'}

    # 回调6: 暂停
    @app.callback(
        [Output('robot-state', 'data', allow_duplicate=True),
         Output('animation-control', 'data', allow_duplicate=True)],
        Input('btn-auto-pause', 'n_clicks'),
        State('robot-state', 'data'),
        prevent_initial_call=True
    )
    def pause_auto_spray(n, state_json):
        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        data['mode'] = 'manual'
        data['spray_on'] = False
        state.mode = 'manual'
        state.spray_on = False
        return json.dumps(data), {'cmd': 'stop'}

    # 回调7: 重置位置 + 清除路径
    @app.callback(
        [Output('robot-state', 'data', allow_duplicate=True),
         Output('path-data', 'data', allow_duplicate=True)],
        Input('btn-reset', 'n_clicks'),
        prevent_initial_call=True
    )
    def reset_position(n):
        state.robot.x = 0
        state.robot.y = 0
        state.robot.z = 400
        state.robot.swing_angle = 0
        state.spray_on = False
        state.mode = 'manual'
        return state.to_json(), {}

    # 回调8: 清除喷涂痕迹
    @app.callback(
        [Output('robot-state', 'data', allow_duplicate=True),
         Output('spray-texture-data', 'data', allow_duplicate=True),
         Output('animation-control', 'data', allow_duplicate=True)],
        Input('btn-clear-trail', 'n_clicks'),
        State('robot-state', 'data'),
        prevent_initial_call=True
    )
    def clear_trail(n, state_json):
        spray_sim.clear()
        state.spray_trail = []
        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        return json.dumps(data), {}, {'cmd': 'stop'}

    # 回调8b: 清除轨迹
    @app.callback(
        Output('path-data', 'data', allow_duplicate=True),
        Input('btn-clear-path', 'n_clicks'),
        prevent_initial_call=True
    )
    def clear_path(n):
        return {}

    # 回调9: Canvas绘图+优化（全部客户端处理）
    app.clientside_callback(
        """
        function(n) {
            var canvas = document.getElementById('draw-canvas');
            if (!canvas || canvas._init) return '';
            canvas._init = true;

            var ctx = canvas.getContext('2d');
            var drawing = false;
            var rawPts = [];
            var optPts = [];
            var lastX = -1, lastY = -1;
            var CX = canvas.width / 2, CY = canvas.height / 2, SCALE = 3;

            function getPos(e) {
                var r = canvas.getBoundingClientRect();
                return {
                    x: Math.round((e.clientX - r.left) * (canvas.width / r.width)),
                    y: Math.round((e.clientY - r.top) * (canvas.height / r.height))
                };
            }
            function toWorld(p) { return {x: (p.x - CX) * SCALE, y: (p.y - CY) * SCALE}; }
            function toCanvas(p) { return {x: Math.round(p.x / SCALE + CX), y: Math.round(p.y / SCALE + CY)}; }

            function redraw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.strokeStyle = '#333'; ctx.lineWidth = 0.5;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(CX, 0); ctx.lineTo(CX, canvas.height);
                ctx.moveTo(0, CY); ctx.lineTo(canvas.width, CY);
                ctx.stroke(); ctx.setLineDash([]);
                if (rawPts.length > 1) {
                    ctx.strokeStyle = '#888'; ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(rawPts[0].x, rawPts[0].y);
                    for (var i = 1; i < rawPts.length; i++) ctx.lineTo(rawPts[i].x, rawPts[i].y);
                    ctx.stroke();
                }
                if (optPts.length > 1) {
                    ctx.strokeStyle = '#ff8c00'; ctx.lineWidth = 2.5;
                    ctx.beginPath(); ctx.moveTo(optPts[0].x, optPts[0].y);
                    for (var i = 1; i < optPts.length; i++) ctx.lineTo(optPts[i].x, optPts[i].y);
                    ctx.stroke();
                    // 端点标记
                    ctx.fillStyle = '#ff8c00';
                    [optPts[0], optPts[optPts.length-1]].forEach(function(p) {
                        ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI*2); ctx.fill();
                    });
                }
            }

            canvas.addEventListener('mousedown', function(e) {
                drawing = true; optPts = [];
                var p = getPos(e); rawPts = [p]; lastX = p.x; lastY = p.y; redraw();
            });
            canvas.addEventListener('mousemove', function(e) {
                if (!drawing) return;
                var p = getPos(e);
                if ((p.x-lastX)*(p.x-lastX)+(p.y-lastY)*(p.y-lastY) >= 25) {
                    rawPts.push(p); lastX = p.x; lastY = p.y; redraw();
                }
            });
            function finish() { if (drawing) drawing = false; }
            canvas.addEventListener('mouseup', finish);
            canvas.addEventListener('mouseleave', finish);

            // === RDP简化 ===
            function ptLineDist(p, a, b) {
                var dx = b.x-a.x, dy = b.y-a.y;
                if (dx===0 && dy===0) return Math.hypot(p.x-a.x, p.y-a.y);
                var t = Math.max(0, Math.min(1, ((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy)));
                return Math.hypot(p.x-(a.x+t*dx), p.y-(a.y+t*dy));
            }
            function rdp(pts, eps) {
                if (pts.length < 3) return pts.slice();
                var maxD=0, maxI=0;
                for (var i=1; i<pts.length-1; i++) {
                    var d = ptLineDist(pts[i], pts[0], pts[pts.length-1]);
                    if (d > maxD) { maxD=d; maxI=i; }
                }
                if (maxD > eps) {
                    var left = rdp(pts.slice(0, maxI+1), eps);
                    var right = rdp(pts.slice(maxI), eps);
                    return left.slice(0,-1).concat(right);
                }
                return [pts[0], pts[pts.length-1]];
            }
            // === 直线检测+拉直 ===
            function straighten(pts, angleThr) {
                if (pts.length < 3) return pts.slice();
                var res = [pts[0]], i = 0;
                while (i < pts.length-1) {
                    var j = i+1;
                    while (j < pts.length-1) {
                        var v1x=pts[j].x-pts[j-1].x, v1y=pts[j].y-pts[j-1].y;
                        var v2x=pts[j+1].x-pts[j].x, v2y=pts[j+1].y-pts[j].y;
                        var dot=v1x*v2x+v1y*v2y, m1=Math.hypot(v1x,v1y), m2=Math.hypot(v2x,v2y);
                        if (m1<1e-6||m2<1e-6) { j++; continue; }
                        var ang = Math.acos(Math.max(-1, Math.min(1, dot/(m1*m2))))*180/Math.PI;
                        if (ang > 180-angleThr) j++; else break;
                    }
                    res.push(pts[j]); i = j;
                }
                return res;
            }

            // 优化按钮：JS端优化 → canvas回显 + set_props发server
            var optBtn = document.getElementById('btn-optimize');
            if (optBtn) {
                optBtn.addEventListener('click', function() {
                    if (rawPts.length < 3) return;
                    var world = rawPts.map(toWorld);
                    var simplified = rdp(world, 15);
                    var optimized = straighten(simplified, 10);
                    optPts = optimized.map(toCanvas);
                    rawPts = [];  // 清除原始轨迹，只保留优化结果
                    redraw();
                    // 发送优化后的世界坐标到server（用于生成路径）
                    if (typeof dash_clientside !== 'undefined' && dash_clientside.set_props) {
                        dash_clientside.set_props('contour-data', {data: [optimized]});
                    }
                });
            }

            // 生成路径按钮：发送contour-data到server
            var genBtn = document.getElementById('btn-gen-path');
            if (genBtn) {
                genBtn.addEventListener('click', function() {
                    if (optPts.length < 2) return;
                    var world = optPts.map(toWorld);
                    if (typeof dash_clientside !== 'undefined' && dash_clientside.set_props) {
                        dash_clientside.set_props('contour-data', {data: [world]});
                    }
                });
            }

            redraw();
            return '';
        }
        """,
        Output('js-output', 'children', allow_duplicate=True),
        Input('draw-setup-interval', 'n_intervals'),
        prevent_initial_call='initial_duplicate',
    )

    def _build_path_data_from_segments(segments, start_pos=None, table_y=0):
        """从分段列表构建path_data（含segments和可视化轨迹）"""
        gun_traj = []
        table_traj = []
        spray_traj = []

        # 起始位置
        if start_pos:
            prev_x = start_pos.get('x', 0)
            prev_y = start_pos.get('y', 0)
            prev_z = start_pos.get('z', 400)
        elif segments:
            prev_x = segments[0]['target']['x']
            prev_y = segments[0]['target']['y']
            prev_z = segments[0]['target']['z']
        else:
            prev_x, prev_y, prev_z = 0, 0, 400

        for seg in segments:
            t = seg['target']
            seg_type = seg.get('type', 'single_axis')
            axes = seg.get('axes', ['x'])

            if seg_type == 'single_axis':
                axis = axes[0]
                n_pts = 10
                for i in range(1, n_pts + 1):
                    frac = i / n_pts
                    px = prev_x + (t['x'] - prev_x) * frac if axis == 'x' else prev_x
                    py = prev_y + (t['y'] - prev_y) * frac if axis == 'y' else prev_y
                    pz = prev_z + (t['z'] - prev_z) * frac if axis == 'z' else prev_z
                    gun_traj.append({'x': round(px, 2), 'z': round(pz, 2)})
                    table_traj.append({'y': round(py, 2)})
                prev_x, prev_y, prev_z = t['x'], t['y'], t['z']

            elif seg_type == 'xy_interp':
                n_pts = 20
                for i in range(1, n_pts + 1):
                    frac = i / n_pts
                    px = prev_x + (t['x'] - prev_x) * frac
                    py = prev_y + (t['y'] - prev_y) * frac
                    pz = t['z']
                    gun_traj.append({'x': round(px, 2), 'z': round(pz, 2)})
                    table_traj.append({'y': round(py, 2)})
                    spray_traj.append({'x': round(px, 2), 'y': round(py + table_y, 2)})
                prev_x, prev_y, prev_z = t['x'], t['y'], t['z']

        return {
            'segments': segments,
            'gun_traj': gun_traj,
            'table_traj': table_traj,
            'spray_traj': spray_traj,
        }

    def _build_animation_frames(segments, start_pos=None, speed=50):
        """从分段列表生成动画帧序列（客户端播放用）"""
        frames = []
        dt = 0.1  # 100ms per frame
        move_per_frame = speed * dt

        if start_pos:
            cx = start_pos.get('x', 0)
            cy = start_pos.get('y', 0)
            cz = start_pos.get('z', 400)
        else:
            cx, cy, cz = 0, 0, 400

        for seg in segments:
            t = seg['target']
            seg_type = seg.get('type', 'single_axis')
            axes = seg.get('axes', ['x'])

            if seg_type == 'single_axis':
                axis = axes[0]
                target_val = t[axis]
                while abs(target_val - (cx if axis == 'x' else cy if axis == 'y' else cz)) > 0.1:
                    cur = cx if axis == 'x' else cy if axis == 'y' else cz
                    diff = target_val - cur
                    if abs(diff) <= move_per_frame:
                        if axis == 'x': cx = target_val
                        elif axis == 'y': cy = target_val
                        else: cz = target_val
                    else:
                        step = move_per_frame if diff > 0 else -move_per_frame
                        if axis == 'x': cx += step
                        elif axis == 'y': cy += step
                        else: cz += step
                    frames.append({'x': round(cx, 2), 'y': round(cy, 2), 'z': round(cz, 2), 'spray': False})

            elif seg_type == 'xy_interp':
                dx = t['x'] - cx
                dy = t['y'] - cy
                dist = (dx**2 + dy**2) ** 0.5
                while dist > 0.1:
                    if dist <= move_per_frame:
                        cx, cy = t['x'], t['y']
                    else:
                        ux, uy = dx / dist, dy / dist
                        cx += ux * move_per_frame
                        cy += uy * move_per_frame
                    cz = t['z']
                    frames.append({'x': round(cx, 2), 'y': round(cy, 2), 'z': round(cz, 2), 'spray': True})
                    dx = t['x'] - cx
                    dy = t['y'] - cy
                    dist = (dx**2 + dy**2) ** 0.5

        return frames

    def _regenerate_path(template, pos):
        """根据当前位置重新生成路径"""
        sx, sy = pos.get('x', 0), pos.get('y', 0)
        segments = []
        if template == '矩形':
            segments = planner.generate_rect_path(start_x=sx, start_y=sy)
        elif template == '直线':
            segments = planner.generate_line_path(start_x=-400, start_y=sy,
                                                  end_x=400, start_pos_x=sx, start_pos_y=sy)
        elif template == '圆形':
            segments = planner.generate_circle_path(start_x=sx, start_y=sy)
        elif template == 'Z字形':
            segments = planner.generate_zigzag_path(start_x=sx, start_y=sy)
        if not segments:
            return {}
        pd = _build_path_data_from_segments(segments, start_pos=pos, table_y=sy)
        pd['source'] = 'template'
        return pd

    # 回调11: 生成路径（基于优化轨迹）→ 分段格式
    @app.callback(
        Output('path-data', 'data', allow_duplicate=True),
        Input('contour-data', 'data'),
        [State('spray-radius', 'value'),
         State('robot-state', 'data')],
        prevent_initial_call=True
    )
    def generate_spray_path(contour_data, spray_radius, state_json):
        if not contour_data or contour_data == '':
            return {}
        if isinstance(contour_data, str):
            try:
                contour_data = json.loads(contour_data)
            except (json.JSONDecodeError, ValueError):
                return {}
        if not contour_data:
            return {}

        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        pos = data.get('position', {'x': 0, 'y': 0, 'z': 400})
        sx, sy = pos.get('x', 0), pos.get('y', 0)

        # 取第一个轮廓（优化后的单条轨迹）
        points = contour_data[0]
        if len(points) < 2:
            return {}

        # 直接转为分段：approach → xy_interp序列 → lift
        segments = []
        first = points[0]
        # X到位
        segments.append(planner._seg('single_axis', first['x'], sy, planner.safe_z, ['x']))
        # Z下降
        segments.append(planner._seg('single_axis', first['x'], sy, planner.spray_z, ['z']))
        # 逐点喷涂
        for p in points[1:]:
            segments.append(planner._seg('xy_interp', p['x'], p['y'], planner.spray_z, ['x', 'y']))
        # Z抬升
        last = points[-1]
        segments.append(planner._seg('single_axis', last['x'], last['y'], planner.safe_z, ['z']))

        pd = _build_path_data_from_segments(segments, start_pos=pos, table_y=sy)
        pd['source'] = 'drawing'
        return pd

    # 回调12: 路径模板选择时更新路径数据 → 分段格式
    @app.callback(
        Output('path-data', 'data', allow_duplicate=True),
        Input('btn-gen-template', 'n_clicks'),
        [State('path-template', 'value'),
         State('spray-radius', 'value'),
         State('robot-state', 'data')],
        prevent_initial_call=True
    )
    def generate_template_path(n, template, radius, state_json):
        if n is None:
            return {}
        data = json.loads(state_json) if isinstance(state_json, str) else state_json
        pos = data.get('position', {'x': 0, 'y': 0, 'z': 400})
        sx, sy = pos.get('x', 0), pos.get('y', 0)
        segments = []
        if template == '矩形':
            segments = planner.generate_rect_path(rows=5, cols=8, start_x=sx, start_y=sy)
        elif template == '直线':
            segments = planner.generate_line_path(start_x=-400, start_y=sy,
                                                  end_x=400, start_pos_x=sx, start_pos_y=sy)
        elif template == '圆形':
            segments = planner.generate_circle_path(start_x=sx, start_y=sy)
        elif template == 'Z字形':
            segments = planner.generate_zigzag_path(start_x=sx, start_y=sy)
        pd = _build_path_data_from_segments(segments, start_pos=pos, table_y=sy)
        pd['source'] = 'template'
        return pd

    # 客户端回调: robot-state变化时更新3D场景
    app.clientside_callback(
        """
        function(stateData) {
            if (!stateData) return '';
            var data = (typeof stateData === 'string') ? JSON.parse(stateData) : stateData;
            if (!data || !data.position) return '';

            var pos = data.position;

            if (typeof updateRobotPosition === 'function') {
                updateRobotPosition(pos.x, pos.y, pos.z);
            }
            if (typeof updateSwingAngle === 'function') {
                updateSwingAngle(pos.swing_angle || 0);
            }
            if (typeof setSprayEnabled === 'function') {
                setSprayEnabled(!!data.spray_on);
            }

            return '';
        }
        """,
        Output('js-output', 'children'),
        Input('robot-state', 'data'),
    )

    # 客户端回调: path-data变化时绘制三条轨迹线
    app.clientside_callback(
        """
        function(pathData, stateData) {
            if (!pathData || !pathData.gun_traj || pathData.gun_traj.length === 0) {
                if (typeof drawTrajectories === 'function') drawTrajectories([], [], [], null, []);
                return '';
            }
            var gun_traj = pathData.gun_traj;
            var table_traj = pathData.table_traj;
            var spray_traj = pathData.spray_traj;

            var currentPos = null;
            if (stateData) {
                var data = (typeof stateData === 'string') ? JSON.parse(stateData) : stateData;
                if (data && data.position) currentPos = data.position;
            }
            if (typeof drawTrajectories === 'function') {
                drawTrajectories(gun_traj, table_traj, spray_traj, currentPos, pathData.segments);
            }
            return '';
        }
        """,
        Output('js-output', 'children', allow_duplicate=True),
        [Input('path-data', 'data'),
         Input('robot-state', 'data')],
        prevent_initial_call=True,
    )

    # 客户端回调: 帧动画播放（requestAnimationFrame，无服务器通信）
    app.clientside_callback(
        """
        function(ctrlData, pathData) {
            if (!ctrlData || !ctrlData.cmd) return '';

            if (ctrlData.cmd === 'stop') {
                if (window._frameAnimId) { cancelAnimationFrame(window._frameAnimId); window._frameAnimId = null; }
                window._animFrames = null;
                if (typeof clearAllSpray === 'function') clearAllSpray();
                return '';
            }

            if (ctrlData.cmd === 'start' && pathData && pathData.frames && pathData.frames.length > 0) {
                if (window._frameAnimId) { cancelAnimationFrame(window._frameAnimId); }

                var frames = pathData.frames;
                var idx = 0;
                window._animFrames = frames;

                var colorMap = {'红色': [255,0,0], '蓝色': [0,0,255], '绿色': [0,200,0], '白色': [255,255,255], '黑色': [30,30,30]};
                var colorEl = document.getElementById('spray-color');
                var radiusEl = document.getElementById('spray-radius');
                var sc = colorMap[colorEl ? colorEl.value : '红色'] || [255,0,0];
                var sr = radiusEl ? parseFloat(radiusEl.value) || 30 : 30;

                var lastTime = 0;
                function step(ts) {
                    if (!window._animFrames || idx >= frames.length) {
                        window._frameAnimId = null;
                        window._animFrames = null;
                        if (frames.length > 0) {
                            var last = frames[frames.length - 1];
                            if (typeof updateRobotPosition === 'function') updateRobotPosition(last.x, last.y, last.z);
                            if (typeof setSprayEnabled === 'function') setSprayEnabled(false);
                        }
                        return;
                    }
                    if (ts - lastTime >= 100) {
                        lastTime = ts;
                        var f = frames[idx];
                        if (typeof updateRobotPosition === 'function') updateRobotPosition(f.x, f.y, f.z);
                        if (typeof setSprayEnabled === 'function') setSprayEnabled(f.spray);
                        if (f.spray && f.z <= 280 && typeof sprayOnCanvas === 'function') {
                            sprayOnCanvas(f.x, f.y, sr, sc[0], sc[1], sc[2]);
                        }
                        idx++;
                    }
                    window._frameAnimId = requestAnimationFrame(step);
                }
                window._frameAnimId = requestAnimationFrame(step);
            }
            return '';
        }
        """,
        Output('js-output', 'children', allow_duplicate=True),
        [Input('animation-control', 'data'),
         Input('path-data', 'data')],
        prevent_initial_call=True,
    )
