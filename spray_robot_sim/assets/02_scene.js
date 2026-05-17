
// ============== Three.js 场景初始化 ==============
(function initScene(retries) {
    const sceneContainer = document.getElementById('scene-container');
    if (!sceneContainer || typeof THREE === 'undefined') {
        if (retries > 200) { console.error('Scene init timeout'); return; }
        setTimeout(function(){ initScene(retries + 1); }, 100);
        return;
    }

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const containerWidth = sceneContainer.clientWidth || 800;
const containerHeight = sceneContainer.clientHeight || 600;
const camera = new THREE.PerspectiveCamera(45, containerWidth / containerHeight, 1, 5000);
camera.position.set(1000, 800, 1000);
camera.lookAt(0, 400, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(containerWidth, containerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
sceneContainer.appendChild(renderer.domElement);

// OrbitControls (inline, no ES module import needed for simple setup)
const controls = {
    target: new THREE.Vector3(0, 400, 0),
    enableDamping: true,
    dampingFactor: 0.05,
    minDistance: 300,
    maxDistance: 3000,
    isDragging: false,
    previousMousePosition: { x: 0, y: 0 },
    spherical: new THREE.Spherical(),
};

// 手动实现 OrbitControls
(function() {
    const canvas = renderer.domElement;
    let spherical = new THREE.Spherical();
    spherical.setFromVector3(camera.position.clone().sub(controls.target));

    canvas.addEventListener('mousedown', (e) => {
        controls.isDragging = true;
        controls.previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener('mousemove', (e) => {
        if (!controls.isDragging) return;
        const dx = e.clientX - controls.previousMousePosition.x;
        const dy = e.clientY - controls.previousMousePosition.y;
        spherical.theta -= dx * 0.005;
        spherical.phi -= dy * 0.005;
        spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
        const pos = new THREE.Vector3().setFromSpherical(spherical).add(controls.target);
        camera.position.copy(pos);
        camera.lookAt(controls.target);
        controls.previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    canvas.addEventListener('mouseup', () => { controls.isDragging = false; });
    canvas.addEventListener('mouseleave', () => { controls.isDragging = false; });
    canvas.addEventListener('wheel', (e) => {
        spherical.radius += e.deltaY * 0.5;
        spherical.radius = Math.max(300, Math.min(3000, spherical.radius));
        const pos = new THREE.Vector3().setFromSpherical(spherical).add(controls.target);
        camera.position.copy(pos);
        camera.lookAt(controls.target);
        e.preventDefault();
    }, { passive: false });

    // 初始设置
    const pos = new THREE.Vector3().setFromSpherical(spherical).add(controls.target);
    camera.position.copy(pos);
    camera.lookAt(controls.target);
})();

// ============== 灯光 ==============
const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
scene.add(ambientLight);
const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight1.position.set(500, 800, 500);
scene.add(dirLight1);
const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
dirLight2.position.set(-300, 500, -200);
scene.add(dirLight2);

// 地面网格
const gridHelper = new THREE.GridHelper(2000, 40, 0x444444, 0x333333);
scene.add(gridHelper);

// ============== 材质定义 ==============
const frameMaterial = new THREE.MeshStandardMaterial({ color: 0xA0A0A0, metalness: 0.7, roughness: 0.25 });
const bracketMaterial = new THREE.MeshStandardMaterial({ color: 0x1A1A1A, metalness: 0.5, roughness: 0.4 });
const motorMaterial = new THREE.MeshStandardMaterial({ color: 0x2E7D32, metalness: 0.4, roughness: 0.5 });
const railMaterial = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8, roughness: 0.15 });
const zSliderMaterial = new THREE.MeshStandardMaterial({ color: 0x1565C0, metalness: 0.5, roughness: 0.3 });
const xSliderMaterial = new THREE.MeshStandardMaterial({ color: 0xFFD600, metalness: 0.5, roughness: 0.3 });
const jointMaterial = new THREE.MeshStandardMaterial({ color: 0x4FC3F7, metalness: 0.4, roughness: 0.4 });
const gunMaterial = new THREE.MeshStandardMaterial({ color: 0x212121, metalness: 0.3, roughness: 0.6 });
const nozzleMaterial = new THREE.MeshStandardMaterial({ color: 0x424242, metalness: 0.7, roughness: 0.2 });
const yDriveMaterial = new THREE.MeshStandardMaterial({ color: 0xFFD600, metalness: 0.5, roughness: 0.3 });
const gearMaterial = new THREE.MeshStandardMaterial({ color: 0x5D4037, metalness: 0.6, roughness: 0.4 });
const tableMaterial = new THREE.MeshStandardMaterial({ color: 0x795548, roughness: 0.8, metalness: 0.1 });
const holeMaterial = new THREE.MeshStandardMaterial({ color: 0x3E2723, roughness: 0.9, metalness: 0.05 });
const cabinetMaterial = new THREE.MeshStandardMaterial({ color: 0x4CAF50, metalness: 0.3, roughness: 0.5 });
const silverMaterial = new THREE.MeshStandardMaterial({ color: 0xC0C0C0, metalness: 0.8, roughness: 0.2 });

// ============== 机器人主Group ==============
const robotGroup = new THREE.Group();
scene.add(robotGroup);

// ============== 底座框架 ==============
const baseFrame = new THREE.Group();
robotGroup.add(baseFrame);

// 4根底座型材
const baseBar1 = new THREE.Mesh(new THREE.BoxGeometry(1200, 40, 40), frameMaterial);
baseBar1.position.set(0, 20, 380);
baseFrame.add(baseBar1);
const baseBar2 = new THREE.Mesh(new THREE.BoxGeometry(1200, 40, 40), frameMaterial);
baseBar2.position.set(0, 20, -380);
baseFrame.add(baseBar2);
const baseBar3 = new THREE.Mesh(new THREE.BoxGeometry(40, 40, 800), frameMaterial);
baseBar3.position.set(-580, 20, 0);
baseFrame.add(baseBar3);
const baseBar4 = new THREE.Mesh(new THREE.BoxGeometry(40, 40, 800), frameMaterial);
baseBar4.position.set(580, 20, 0);
baseFrame.add(baseBar4);

// 4个黑色地脚
const footPositions = [[-580, 0, 380], [580, 0, 380], [-580, 0, -380], [580, 0, -380]];
footPositions.forEach(pos => {
    const foot = new THREE.Mesh(new THREE.CylinderGeometry(15, 15, 30), bracketMaterial);
    foot.position.set(pos[0], 15, pos[2]);
    baseFrame.add(foot);
});

// 黑色角码
const bracketPositions = [[-560, 30, 360], [560, 30, 360], [-560, 30, -360], [560, 30, -360]];
bracketPositions.forEach(pos => {
    const bracket = new THREE.Mesh(new THREE.BoxGeometry(50, 50, 5), bracketMaterial);
    bracket.position.set(pos[0], pos[1], pos[2]);
    baseFrame.add(bracket);
});

// ============== 立柱 ==============
const leftColumn = new THREE.Group();
robotGroup.add(leftColumn);
const leftPillar = new THREE.Mesh(new THREE.BoxGeometry(40, 1000, 40), frameMaterial);
leftPillar.position.set(-580, 520, 0);
leftColumn.add(leftPillar);

const rightColumn = new THREE.Group();
robotGroup.add(rightColumn);
const rightPillar = new THREE.Mesh(new THREE.BoxGeometry(40, 1000, 40), frameMaterial);
rightPillar.position.set(580, 520, 0);
rightColumn.add(rightPillar);

// 顶部横梁
const topBeam = new THREE.Mesh(new THREE.BoxGeometry(1200, 40, 40), frameMaterial);
topBeam.position.set(0, 1020, 0);
robotGroup.add(topBeam);

// ============== Z轴（左右对称） ==============
// 左Z轴
const leftZAxis = new THREE.Group();
leftColumn.add(leftZAxis);

const leftMotor = new THREE.Mesh(new THREE.CylinderGeometry(25, 25, 50), motorMaterial);
leftMotor.position.set(-580, 80, 40);
leftZAxis.add(leftMotor);

const leftReducer = new THREE.Mesh(new THREE.CylinderGeometry(20, 20, 30), motorMaterial);
leftReducer.position.set(-580, 115, 40);
leftZAxis.add(leftReducer);

const leftScrew = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 900), silverMaterial);
leftScrew.position.set(-580, 520, 40);
leftZAxis.add(leftScrew);

const leftRail1 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 900), railMaterial);
leftRail1.position.set(-580, 520, 60);
leftZAxis.add(leftRail1);
const leftRail2 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 900), railMaterial);
leftRail2.position.set(-580, 520, 20);
leftZAxis.add(leftRail2);

// 左Z滑台
const leftZSliderGroup = new THREE.Group();
leftZSliderGroup.position.y = 400;
leftColumn.add(leftZSliderGroup);
const leftZSlider = new THREE.Mesh(new THREE.BoxGeometry(80, 60, 40), zSliderMaterial);
leftZSlider.position.set(-580, 0, 40);
leftZSliderGroup.add(leftZSlider);

// 右Z轴
const rightZAxis = new THREE.Group();
rightColumn.add(rightZAxis);

const rightMotor = new THREE.Mesh(new THREE.CylinderGeometry(25, 25, 50), motorMaterial);
rightMotor.position.set(580, 80, 40);
rightZAxis.add(rightMotor);

const rightReducer = new THREE.Mesh(new THREE.CylinderGeometry(20, 20, 30), motorMaterial);
rightReducer.position.set(580, 115, 40);
rightZAxis.add(rightReducer);

const rightScrew = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 900), silverMaterial);
rightScrew.position.set(580, 520, 40);
rightZAxis.add(rightScrew);

const rightRail1 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 900), railMaterial);
rightRail1.position.set(580, 520, 60);
rightZAxis.add(rightRail1);
const rightRail2 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 900), railMaterial);
rightRail2.position.set(580, 520, 20);
rightZAxis.add(rightRail2);

// 右Z滑台
const rightZSliderGroup = new THREE.Group();
rightZSliderGroup.position.y = 400;
rightColumn.add(rightZSliderGroup);
const rightZSlider = new THREE.Mesh(new THREE.BoxGeometry(80, 60, 40), zSliderMaterial);
rightZSlider.position.set(580, 0, 40);
rightZSliderGroup.add(rightZSlider);

// ============== X轴 ==============
const xAxisAssembly = new THREE.Group();
xAxisAssembly.position.y = 400;
robotGroup.add(xAxisAssembly);

const xRail1 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 1100), zSliderMaterial);
xRail1.rotation.z = Math.PI / 2;
xRail1.position.set(0, 0, 60);
xAxisAssembly.add(xRail1);
const xRail2 = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 1100), zSliderMaterial);
xRail2.rotation.z = Math.PI / 2;
xRail2.position.set(0, 0, 20);
xAxisAssembly.add(xRail2);

// X轴滑块
const xSliderGroup = new THREE.Group();
xAxisAssembly.add(xSliderGroup);
const xSlider = new THREE.Mesh(new THREE.BoxGeometry(60, 50, 50), xSliderMaterial);
xSliderGroup.add(xSlider);

// ============== 末端执行器 ==============
const endEffectorGroup = new THREE.Group();
xSliderGroup.add(endEffectorGroup);

// 连接座
const connectingBase = new THREE.Mesh(new THREE.BoxGeometry(40, 30, 40), xSliderMaterial);
connectingBase.position.y = -40;
endEffectorGroup.add(connectingBase);

// 摆动关节
const swingJoint = new THREE.Mesh(new THREE.CylinderGeometry(12, 12, 20), jointMaterial);
swingJoint.position.y = -65;
endEffectorGroup.add(swingJoint);

// 锁紧手柄
const handle = new THREE.Mesh(new THREE.BoxGeometry(5, 8, 15), jointMaterial);
handle.position.set(18, -65, 0);
endEffectorGroup.add(handle);

// 喷枪
const sprayGun = new THREE.Group();
sprayGun.position.y = -65;
endEffectorGroup.add(sprayGun);

const gunBody = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 80), gunMaterial);
gunBody.position.y = -50;
sprayGun.add(gunBody);

const nozzleCone = new THREE.Mesh(new THREE.ConeGeometry(8, 20), nozzleMaterial);
nozzleCone.position.y = -100;
nozzleCone.rotation.x = Math.PI;
sprayGun.add(nozzleCone);

const gunClamp = new THREE.Mesh(new THREE.BoxGeometry(20, 10, 15), silverMaterial);
gunClamp.position.y = -20;
sprayGun.add(gunClamp);

// 雾化锥（朝前方）
const mistGeometry = new THREE.ConeGeometry(30, 80, 16, 1, true);
const mistMaterial = new THREE.MeshBasicMaterial({
    color: 0xFFFFFF, transparent: true, opacity: 0.05,
    side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
});
const mistCone = new THREE.Mesh(mistGeometry, mistMaterial);
mistCone.position.y = -150;
mistCone.rotation.x = Math.PI;
mistCone.visible = false;
sprayGun.add(mistCone);

// 线缆曲线
const cableCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, -20, 0),
    new THREE.Vector3(10, -40, 10),
    new THREE.Vector3(5, -80, 5),
    new THREE.Vector3(0, -120, 0),
]);
const cableGeometry = new THREE.TubeGeometry(cableCurve, 20, 2, 8, false);
const cable = new THREE.Mesh(cableGeometry, gunMaterial);
sprayGun.add(cable);

// ============== Y轴（工件平台） ==============
const yPlatformAssembly = new THREE.Group();
robotGroup.add(yPlatformAssembly);

// 3个驱动支座
const yDrivePositions = [[-300, 20, 0], [0, 20, 0], [300, 20, 0]];
yDrivePositions.forEach(pos => {
    const drive = new THREE.Mesh(new THREE.BoxGeometry(60, 40, 60), yDriveMaterial);
    drive.position.set(pos[0], pos[1], pos[2]);
    yPlatformAssembly.add(drive);
    // 齿轮
    const gear = new THREE.Mesh(new THREE.CylinderGeometry(15, 15, 10), gearMaterial);
    gear.position.set(pos[0], 45, pos[2]);
    yPlatformAssembly.add(gear);
});

// 齿条
const rack = new THREE.Mesh(new THREE.BoxGeometry(1000, 8, 8), gearMaterial);
rack.position.set(0, 14, 0);
yPlatformAssembly.add(rack);

// 工作台
const workTable = new THREE.Mesh(new THREE.BoxGeometry(1000, 10, 600), tableMaterial);
workTable.position.set(0, 55, 0);
yPlatformAssembly.add(workTable);

// 定位孔 5x3 网格
for (let ix = -2; ix <= 2; ix++) {
    for (let iy = -1; iy <= 1; iy++) {
        const hole = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 12), holeMaterial);
        hole.position.set(ix * 180, 55, iy * 180);
        yPlatformAssembly.add(hole);
    }
}

// 喷涂痕迹平面
const sprayPlaneGeometry = new THREE.PlaneGeometry(1000, 600);
const sprayPlaneMaterial = new THREE.MeshBasicMaterial({
    transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false,
});
const sprayPlane = new THREE.Mesh(sprayPlaneGeometry, sprayPlaneMaterial);
sprayPlane.rotation.x = -Math.PI / 2;
sprayPlane.position.set(0, 61, 0);
yPlatformAssembly.add(sprayPlane);

// 客户端Canvas喷漆纹理（实时绘制，不依赖服务器）
const sprayCanvas = document.createElement('canvas');
sprayCanvas.width = 1000;
sprayCanvas.height = 600;
const sprayCtx = sprayCanvas.getContext('2d');
const sprayCanvasTexture = new THREE.CanvasTexture(sprayCanvas);
sprayCanvasTexture.flipY = false;
sprayPlaneMaterial.map = sprayCanvasTexture;

// 喷漆到Canvas（机器人坐标 → Canvas像素）
window.sprayOnCanvas = function(x, y, radius, r, g, b) {
    var cx = (x + 500);
    var cy = (-y + 300);
    var grad = sprayCtx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    grad.addColorStop(0, 'rgba(' + r + ',' + g + ',' + b + ',0.3)');
    grad.addColorStop(1, 'rgba(' + r + ',' + g + ',' + b + ',0)');
    sprayCtx.fillStyle = grad;
    sprayCtx.beginPath();
    sprayCtx.arc(cx, cy, radius, 0, Math.PI * 2);
    sprayCtx.fill();
    sprayCanvasTexture.needsUpdate = true;
    sprayPlaneMaterial.opacity = 0.85;
    sprayPlaneMaterial.transparent = true;
    sprayPlaneMaterial.needsUpdate = true;
};

// 清除Canvas喷漆
window.clearSprayCanvas = function() {
    sprayCtx.clearRect(0, 0, sprayCanvas.width, sprayCanvas.height);
    sprayCanvasTexture.needsUpdate = true;
    sprayPlaneMaterial.map = null;
    sprayPlaneMaterial.opacity = 0;
    sprayPlaneMaterial.needsUpdate = true;
};

// ============== 电气控制柜 ==============
const leftCabinet = new THREE.Mesh(new THREE.BoxGeometry(80, 400, 60), cabinetMaterial);
leftCabinet.position.set(-560, 240, 60);
robotGroup.add(leftCabinet);
// 散热格栅
for (let i = 0; i < 5; i++) {
    const grill = new THREE.Mesh(new THREE.BoxGeometry(60, 2, 40), new THREE.MeshStandardMaterial({ color: 0x2E7D32, metalness: 0.3, roughness: 0.5 }));
    grill.position.set(-560, 420, 60);
    grill.position.y += i * 8;
    robotGroup.add(grill);
}

const rightCabinet = new THREE.Mesh(new THREE.BoxGeometry(80, 400, 60), cabinetMaterial);
rightCabinet.position.set(560, 240, 60);
robotGroup.add(rightCabinet);
for (let i = 0; i < 5; i++) {
    const grill = new THREE.Mesh(new THREE.BoxGeometry(60, 2, 40), new THREE.MeshStandardMaterial({ color: 0x2E7D32, metalness: 0.3, roughness: 0.5 }));
    grill.position.set(560, 420, 60);
    grill.position.y += i * 8;
    robotGroup.add(grill);
}

// ============== 坐标系标识 ==============
const axisHelper = new THREE.Group();
const xArrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 80, 0xFF0000, 15, 8);
const yArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0, 0), 80, 0x00FF00, 15, 8);
const zArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 0), 80, 0x0000FF, 15, 8);
axisHelper.add(xArrow, yArrow, zArrow);
axisHelper.position.set(0, -30, 0);
xSliderGroup.add(axisHelper);

// 轴标签 (简单用sprite)
function makeLabel(text, color) {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = color;
    ctx.font = 'bold 20px monospace';
    ctx.fillText(text, 4, 24);
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(40, 20, 1);
    return sprite;
}
const xLabel = makeLabel('XC', '#FF0000');
xLabel.position.set(90, 0, 0);
axisHelper.add(xLabel);
const yLabel = makeLabel('YC', '#00FF00');
yLabel.position.set(0, 0, 90);
axisHelper.add(yLabel);
const zLabel = makeLabel('ZC', '#0000FF');
zLabel.position.set(0, 90, 0);
axisHelper.add(zLabel);

// ============== 粒子系统 ==============
const MAX_PARTICLES = 2000;
const particleGeometry = new THREE.BufferGeometry();
const positions = new Float32Array(MAX_PARTICLES * 3);
const colors = new Float32Array(MAX_PARTICLES * 3);
const sizes = new Float32Array(MAX_PARTICLES);

for (let i = 0; i < MAX_PARTICLES; i++) {
    positions[i * 3] = 0;
    positions[i * 3 + 1] = 0;
    positions[i * 3 + 2] = 0;
    sizes[i] = 0;
    colors[i * 3] = 1;
    colors[i * 3 + 1] = 1;
    colors[i * 3 + 2] = 1;
}

particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
particleGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

const particleMaterial = new THREE.PointsMaterial({
    size: 3,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    sizeAttenuation: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
});

const particleSystem = new THREE.Points(particleGeometry, particleMaterial);
scene.add(particleSystem);

let particleStates = [];
let particleIndex = 0;
let sprayEnabled = false;
let sprayColorR = 1, sprayColorG = 0, sprayColorB = 0;
let sprayRadius = 30;

function getGunWorldPosition() {
    const pos = new THREE.Vector3();
    nozzleCone.getWorldPosition(pos);
    return pos;
}

function emitParticle(gunWorldPos) {
    const spread = sprayRadius * 0.3;
    const state = {
        x: gunWorldPos.x + (Math.random() - 0.5) * spread,
        y: gunWorldPos.y,
        z: gunWorldPos.z + (Math.random() - 0.5) * spread,
        vx: (Math.random() - 0.5) * 2,
        vy: -3 - Math.random() * 2,
        vz: (Math.random() - 0.5) * 2,
        life: 1.0,
        decay: 0.02 + Math.random() * 0.02,
        r: sprayColorR + (Math.random() - 0.5) * 0.1,
        g: sprayColorG + (Math.random() - 0.5) * 0.1,
        b: sprayColorB + (Math.random() - 0.5) * 0.1,
    };
    particleStates[particleIndex] = state;
    particleIndex = (particleIndex + 1) % MAX_PARTICLES;
}

function updateParticles() {
    const posAttr = particleGeometry.getAttribute('position');
    const sizeAttr = particleGeometry.getAttribute('size');
    const colorAttr = particleGeometry.getAttribute('color');

    if (sprayEnabled) {
        for (let i = 0; i < 10; i++) {
            const gunPos = getGunWorldPosition();
            emitParticle(gunPos);
        }
    }

    for (let i = 0; i < MAX_PARTICLES; i++) {
        const s = particleStates[i];
        if (!s || s.life <= 0) {
            sizes[i] = 0;
            continue;
        }
        s.x += s.vx;
        s.y += s.vy;
        s.z += s.vz;
        // 碰到板子表面（Y=61）立即消失
        if (s.y <= TABLE_SURFACE_Y) {
            s.life = 0;
            sizes[i] = 0;
            continue;
        }
        s.life -= s.decay;

        positions[i * 3] = s.x;
        positions[i * 3 + 1] = s.y;
        positions[i * 3 + 2] = s.z;
        sizes[i] = s.life * 3;
        colors[i * 3] = Math.max(0, Math.min(1, s.r));
        colors[i * 3 + 1] = Math.max(0, Math.min(1, s.g));
        colors[i * 3 + 2] = Math.max(0, Math.min(1, s.b));
    }
    posAttr.needsUpdate = true;
    sizeAttr.needsUpdate = true;
    colorAttr.needsUpdate = true;
}

// ============== 轨迹线 ==============
let trajectoryGroup = null;

function clearTrajectories() {
    if (trajectoryGroup) {
        scene.remove(trajectoryGroup);
        trajectoryGroup.traverse(child => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
        });
        trajectoryGroup = null;
    }
    // 清除桌子上的绿线和起点标记
    if (window._greenLine) {
        yPlatformAssembly.remove(window._greenLine);
        if (window._greenLine.geometry) window._greenLine.geometry.dispose();
        if (window._greenLine.material) window._greenLine.material.dispose();
        window._greenLine = null;
    }
    window._sprayTrajRef = null;
}

// 桌面表面Y坐标（Three.js）
const TABLE_SURFACE_Y = 61;

window.drawTrajectories = function(gunTraj, tableTraj, sprayTraj, currentPos, segments, tableYOffset) {
    clearTrajectories();
    if (!gunTraj || gunTraj.length === 0) return;

    trajectoryGroup = new THREE.Group();
    const currentY = currentPos ? currentPos.y : 0;
    const tblOff = tableYOffset || 0;

    // 保存数据供绿线单独更新用
    window._trajData = { gunTraj, tableTraj, sprayTraj, currentPos, segments };

    // === 红色线：喷枪轨迹（ZX平面折线，从喷枪位置出发） ===
    var gunOffX = 0, gunOffZ = 0;
    if (currentPos && gunTraj.length > 0) {
        gunOffX = currentPos.x - gunTraj[0].x;
        gunOffZ = currentPos.z - gunTraj[0].z;
    }
    // 从喷枪当前位置到路径起点的过渡段
    const gunVerts = [];
    if (currentPos) {
        gunVerts.push(currentPos.x, currentPos.z, 0);
    }
    for (const p of gunTraj) {
        gunVerts.push(p.x + gunOffX, p.z + gunOffZ, 0);
    }
    const gunGeo = new THREE.BufferGeometry();
    gunGeo.setAttribute('position', new THREE.Float32BufferAttribute(gunVerts, 3));
    const gunLine = new THREE.Line(gunGeo, new THREE.LineBasicMaterial({ color: 0xff3333, linewidth: 2 }));
    trajectoryGroup.add(gunLine);

    // 红色轨迹箭头（每段一个箭头，在红线上）
    if (segments && segments.length > 0) {
        const upDir = new THREE.Vector3(0, 1, 0);
        let cx = currentPos ? currentPos.x : 0;
        let cz = currentPos ? currentPos.z : 400;
        for (let i = 0; i < segments.length; i++) {
            const seg = segments[i];
            const t = seg.target;
            const ex = t.x + gunOffX, ez = t.z + gunOffZ;
            // 箭头方向：单轴只沿该轴，插补沿实际XY方向
            let dx = 0, dz = 0;
            if (seg.type === 'single_axis') {
                const ax = seg.axes[0];
                if (ax === 'x') { dx = ex - cx; dz = 0; }
                else if (ax === 'y') { dx = 0; dz = 0; } // Y轴在ZX平面无变化
                else if (ax === 'z') { dx = 0; dz = ez - cz; }
            } else {
                dx = ex - cx;
                dz = ez - cz;
            }
            const len = Math.sqrt(dx * dx + dz * dz);
            if (len > 1) {
                const dir = new THREE.Vector3(dx / len, dz / len, 0);
                const arrow = new THREE.Mesh(
                    new THREE.ConeGeometry(5, 14, 8),
                    new THREE.MeshBasicMaterial({ color: 0xff3333 })
                );
                arrow.position.set(cx + dx * 0.5, cz + dz * 0.5, 0);
                arrow.quaternion.setFromUnitVectors(upDir, dir);
                trajectoryGroup.add(arrow);
            }
            cx = ex; cz = ez;
        }
    }

    // === 紫色线：工作台Y轴轨迹（侧面） ===
    if (tableTraj && tableTraj.length > 0) {
        var tblOffY = currentPos ? currentPos.y - tableTraj[0].y : 0;
        const tableVerts = [];
        for (const p of tableTraj) {
            tableVerts.push(-650, 400, -(p.y + tblOffY));
        }
        const tableGeo = new THREE.BufferGeometry();
        tableGeo.setAttribute('position', new THREE.Float32BufferAttribute(tableVerts, 3));
        const tableLine = new THREE.Line(tableGeo, new THREE.LineBasicMaterial({ color: 0xaa44ff, linewidth: 2 }));
        trajectoryGroup.add(tableLine);

        // 紫色箭头（每段一个）
        if (segments && segments.length > 0) {
            const upDir = new THREE.Vector3(0, 1, 0);
            let prevY = currentPos ? currentPos.y : 0;
            for (let i = 0; i < segments.length; i++) {
                const seg = segments[i];
                const ty = seg.target.y + tblOffY;
                const dy = ty - prevY;
                if (Math.abs(dy) > 0.5) {
                    const dir = new THREE.Vector3(0, 0, -dy / Math.abs(dy));
                    const arrow = new THREE.Mesh(
                        new THREE.ConeGeometry(5, 12, 8),
                        new THREE.MeshBasicMaterial({ color: 0xaa44ff })
                    );
                    arrow.position.set(-650, 400, -(prevY + tblOffY + dy * 0.5));
                    arrow.quaternion.setFromUnitVectors(upDir, dir);
                    trajectoryGroup.add(arrow);
                }
                prevY = ty;
            }
        }
    }

    // === 绿色线：喷涂效果（作为桌子子对象，跟着桌子移动） ===
    window._greenLine = null;
    window._sprayTrajRef = sprayTraj;
    if (sprayTraj && sprayTraj.length > 0) {
        const sprayVerts = [];
        for (const p of sprayTraj) {
            // 桌子本地坐标：x不变，y=桌面高度，z=spray_traj的y（已含table_y偏移）
            sprayVerts.push(p.x, TABLE_SURFACE_Y + 1, p.y);
        }
        const sprayGeo = new THREE.BufferGeometry();
        sprayGeo.setAttribute('position', new THREE.Float32BufferAttribute(sprayVerts, 3));
        const sprayLine = new THREE.Line(sprayGeo, new THREE.LineBasicMaterial({ color: 0x00ff00, transparent: true, opacity: 0.7 }));
        yPlatformAssembly.add(sprayLine);
        window._greenLine = sprayLine;
    }

    // === 喷枪当前位置（红球） ===
    if (currentPos) {
        const gunDot = new THREE.Mesh(
            new THREE.SphereGeometry(12, 16, 16),
            new THREE.MeshBasicMaterial({ color: 0xff0000 })
        );
        gunDot.position.set(currentPos.x, currentPos.z, -currentPos.y);
        trajectoryGroup.add(gunDot);
    }

    // === 起点标记（绿色球，喷涂轨迹起点在桌面，跟着桌子移动） ===
    if (sprayTraj && sprayTraj.length > 0) {
        const startDot = new THREE.Mesh(
            new THREE.SphereGeometry(8, 12, 12),
            new THREE.MeshBasicMaterial({ color: 0x00ff00 })
        );
        startDot.position.set(sprayTraj[0].x, TABLE_SURFACE_Y + 2, sprayTraj[0].y);
        yPlatformAssembly.add(startDot);
    }

    scene.add(trajectoryGroup);
}

// 仅更新绿线Z偏移（桌面Y轴移动时调用，不重绘红/紫线）
window.updateGreenLineOffset = function(tblOff) {
    if (!window._greenLine || !window._sprayTrajRef) return;
    var posAttr = window._greenLine.geometry.getAttribute('position');
    var sprayTraj = window._sprayTrajRef;
    for (var i = 0; i < sprayTraj.length; i++) {
        posAttr.setZ(i, -(sprayTraj[i].y + tblOff));
    }
    posAttr.needsUpdate = true;
};

// ============== 全局控制函数（暴露到window供Python回调调用） ==============
window.updateRobotPosition = function(x, y, z) {
    leftZSliderGroup.position.y = z;
    rightZSliderGroup.position.y = z;
    xAxisAssembly.position.y = z;
    xSliderGroup.position.x = x;
    yPlatformAssembly.position.z = -y;
};

window.updateSwingAngle = function(angleDeg) {
    sprayGun.rotation.z = angleDeg * Math.PI / 180;
};

window.setSprayEnabled = function(on) {
    sprayEnabled = on;
    mistCone.visible = on;
    // 关闭喷漆时立即清除所有残留粒子
    if (!on) {
        for (let i = 0; i < MAX_PARTICLES; i++) {
            particleStates[i] = null;
            sizes[i] = 0;
        }
        particleGeometry.getAttribute('size').needsUpdate = true;
    }
};

// 强制清除所有粒子+喷漆纹理（供清除痕迹调用）
window.clearAllSpray = function() {
    sprayEnabled = false;
    mistCone.visible = false;
    for (let i = 0; i < MAX_PARTICLES; i++) {
        particleStates[i] = null;
        sizes[i] = 0;
    }
    particleGeometry.getAttribute('size').needsUpdate = true;
    if (typeof clearSprayCanvas === 'function') clearSprayCanvas();
};

window.setSprayColor = function(r, g, b) {
    sprayColorR = r;
    sprayColorG = g;
    sprayColorB = b;
};

window.updateSprayTexture = function(base64Data, width, height) {
    if (!base64Data) {
        sprayPlaneMaterial.map = null;
        sprayPlaneMaterial.opacity = 0;
        sprayPlaneMaterial.needsUpdate = true;
        return;
    }
    const img = new Image();
    img.onload = function() {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const texture = new THREE.CanvasTexture(canvas);
        texture.flipY = false;
        texture.needsUpdate = true;
        sprayPlaneMaterial.map = texture;
        sprayPlaneMaterial.needsUpdate = true;
        sprayPlaneMaterial.transparent = true;
        sprayPlaneMaterial.opacity = 0.85;
    };
    img.src = 'data:image/png;base64,' + base64Data;
}

// ============== 动画循环 ==============
function animate() {
    requestAnimationFrame(animate);
    updateParticles();
    renderer.render(scene, camera);
}
animate();

// 窗口大小调整
window.addEventListener('resize', () => {
    const w = sceneContainer.clientWidth;
    const h = sceneContainer.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
});

})(0);
