import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from kinematics import GantryRobot
from state_manager import RobotStateManager
from spray_sim import SpraySimulator
from path_planner import PathPlanner
from callbacks import register_callbacks

# 初始化模块
state = RobotStateManager()
spray_sim = SpraySimulator()
planner = PathPlanner()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
)
app.title = "龙门式喷涂机器人模拟系统"

# ========== 布局 ==========
header = dbc.Navbar(
    html.Span("龙门式喷涂机器人模拟系统", className="navbar-brand mb-0 h1"),
    color="#0f3460",
    dark=True,
    className="mb-2",
)

# 运动控制卡片
motion_card = dbc.Card([
    dbc.CardHeader("运动控制"),
    dbc.CardBody([
        html.Label("X轴 (-500 ~ 500)", className="form-label"),
        dbc.Row([
            dbc.Col(dcc.Slider(id='x-slider', min=-500, max=500, step=1, value=0,
                               marks={-500: '-500', 0: '0', 500: '500'}), width=9),
            dbc.Col(html.Span("X: 0", id='x-value', className="status-text"), width=3),
        ]),
        html.Label("Y轴 (-300 ~ 300)", className="form-label"),
        dbc.Row([
            dbc.Col(dcc.Slider(id='y-slider', min=-300, max=300, step=1, value=0,
                               marks={-300: '-300', 0: '0', 300: '300'}), width=9),
            dbc.Col(html.Span("Y: 0", id='y-value', className="status-text"), width=3),
        ]),
        html.Label("Z轴 (250 ~ 800)", className="form-label"),
        dbc.Row([
            dbc.Col(dcc.Slider(id='z-slider', min=250, max=800, step=1, value=400,
                               marks={250: '250', 400: '400', 800: '800'}), width=9),
            dbc.Col(html.Span("Z: 400", id='z-value', className="status-text"), width=3),
        ]),
        html.Label("摆动关节 (-90° ~ 90°)", className="form-label"),
        dbc.Row([
            dbc.Col(dcc.Slider(id='swing-slider', min=-90, max=90, step=1, value=0,
                               marks={-90: '-90°', 0: '0°', 90: '90°'}), width=9),
            dbc.Col(html.Span("角度: 0°", id='swing-value', className="status-text"), width=3),
        ]),
        html.Hr(),
        html.Label("步长", className="form-label"),
        dcc.Dropdown(id='step-size',
                     options=[{'label': str(v), 'value': v} for v in [1, 5, 10, 50, 100]],
                     value=10, clearable=False, style={'color': '#000'}),
        html.Div([
            dbc.Button("X+", id='btn-x-plus', color="primary", size="sm"),
            dbc.Button("X-", id='btn-x-minus', color="primary", size="sm"),
            dbc.Button("Y+", id='btn-y-plus', color="success", size="sm"),
            dbc.Button("Y-", id='btn-y-minus', color="success", size="sm"),
            dbc.Button("Z+", id='btn-z-plus', color="warning", size="sm"),
            dbc.Button("Z-", id='btn-z-minus', color="warning", size="sm"),
        ], className="d-flex flex-wrap gap-1 mt-2"),
    ]),
])

# 喷涂控制卡片
spray_card = dbc.Card([
    dbc.CardHeader("喷涂控制"),
    dbc.CardBody([
        dbc.Switch(id='spray-switch', label='喷涂开启', value=False),
        html.Label("喷涂半径 (mm)", className="form-label mt-2"),
        dcc.Slider(id='spray-radius', min=5, max=80, step=1, value=30,
                   marks={5: '5', 30: '30', 80: '80'}),
        html.Label("流量系数", className="form-label mt-2"),
        dcc.Slider(id='flow-rate', min=0.1, max=1.0, step=0.05, value=1.0,
                   marks={0.1: '0.1', 0.5: '0.5', 1.0: '1.0'}),
        html.Label("喷涂颜色", className="form-label mt-2"),
        dcc.Dropdown(id='spray-color',
                     options=[{'label': c, 'value': c} for c in ['红色', '蓝色', '绿色', '白色', '黑色']],
                     value='红色', clearable=False, style={'color': '#000'}),
    ]),
])

# 路径规划卡片
path_card = dbc.Card([
    dbc.CardHeader("路径规划"),
    dbc.CardBody([
        html.Label("路径模板", className="form-label"),
        dcc.Dropdown(id='path-template',
                     options=[{'label': t, 'value': t} for t in ['矩形', '直线', '圆形', 'Z字形', '轮廓跟随']],
                     value='矩形', clearable=False, style={'color': '#000'}),
        dbc.Button("生成路径", id='btn-gen-template', color="info", size="sm", className="mt-2 w-100"),
        dbc.Button("开始自动喷涂", id='btn-auto-start', color="success", size="sm", className="mt-2 w-100"),
        dbc.Button("暂停", id='btn-auto-pause', color="warning", size="sm", className="mt-1 w-100"),
        dbc.Button("重置位置", id='btn-reset', color="secondary", size="sm", className="mt-1 w-100"),
        dbc.Button("清除轨迹", id='btn-clear-path', color="danger", size="sm", className="mt-1 w-100"),
        dbc.Button("清除痕迹", id='btn-clear-trail', color="danger", size="sm", className="mt-1 w-100"),
    ]),
])

# 手动绘制轨迹卡片
draw_card = dbc.Card([
    dbc.CardHeader("手动绘制轨迹"),
    dbc.CardBody([
        html.Canvas(id='draw-canvas', width=300, height=200,
                    style={'width': '100%', 'border': '1px solid #555', 'cursor': 'crosshair',
                           'borderRadius': '4px', 'backgroundColor': '#1a1a2e'}),
        html.P("在画布上绘制喷涂轨迹", className="text-muted mt-1", style={'fontSize': '0.8em'}),
        dbc.Button("优化轨迹", id='btn-optimize', color="warning", size="sm", className="mt-2 w-100"),
        dbc.Button("生成路径", id='btn-gen-path', color="primary", size="sm", className="mt-1 w-100"),
        dbc.Button("开始喷漆模拟", id='btn-start-spray', color="success", size="sm", className="mt-1 w-100", disabled=True),
    ]),
])

# 状态显示卡片
status_card = dbc.Card([
    dbc.CardHeader("系统状态"),
    dbc.CardBody([
        html.Div(id='status-position', className="status-text"),
        html.Div(id='status-spray', className="status-text"),
        html.Div(id='status-swing', className="status-text"),
        dbc.Badge("手动模式", id='mode-badge', color="info", className="mt-2"),
    ]),
])

# 左侧控制面板
control_panel = html.Div([
    motion_card,
    spray_card,
    path_card,
    draw_card,
    status_card,
], style={'overflowY': 'auto', 'maxHeight': 'calc(100vh - 80px)', 'padding': '4px'})

# 右侧3D场景
scene_area = html.Div(id='scene-container')

# 主布局
app.layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([
            dbc.Col(control_panel, width=3),
            dbc.Col(scene_area, width=9),
        ], className="g-0"),
    ], fluid=True),
    # 隐藏组件
    dcc.Store(id='robot-state', data=state.to_json()),
    dcc.Store(id='path-data', data={}),
    dcc.Store(id='contour-data', data=[]),
    dcc.Store(id='draw-canvas-data', data=[]),
    dcc.Interval(id='draw-setup-interval', interval=500, n_intervals=0, max_intervals=1),
    dcc.Store(id='animation-control', data={}),
    html.Div(id='js-output', style={'display': 'none'}),
    html.Div(id='draw-canvas-persist', style={'display': 'none'}),
])

# 注册回调
register_callbacks(app, state, spray_sim, planner)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
