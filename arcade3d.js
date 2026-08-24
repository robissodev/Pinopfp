// ============================================================
// PINORATOR ARCADE 3D — cabinet built from planes and shapes,
// proportions taken from the reference GLB (Ms Pac-Man machine).
// The live HTML screen (.crt) mounts on the reclined monitor
// plane via CSS3D. Same DOM, same script.js, zero logic changes.
// ============================================================
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';

// ================= SUAS TEXTURAS AQUI =================
// Coloque imagens (png/jpg) no projeto e aponte o caminho.
// Deixe null para usar o visual padrão ($PINO amarelo/roxo).
const TEXTURES = {
  side: null,     // arte lateral (os dois lados)     ex.: 'images/arcade/side.png'
  marquee: null,  // letreiro do topo                 ex.: 'images/arcade/marquee.png'
  front: null,    // painel frontal (coin door)       ex.: 'images/arcade/front.png'
  deck: null,     // superfície do painel de controle ex.: 'images/arcade/deck.png'
};
// ======================================================

const ROOM_COLOR = 0x05030c;
const UI_WIDTH = 640; // CSS px width of the .crt element (see arcade3d.css)
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

// cabinet blueprint, in world px (from the reference GLB, ~909 px/m)
const CAB = {
  innerW: 648,          // gap between the side panels
  sideT: 36,            // side panel thickness
  height: 1660,
  back: -390,
  top: 1660,
  marqueeFrontZ: 230,
  marqueeTopY: 1655,
  marqueeBottomY: 1375,
  monTop: { z: -300, y: 1160 },   // monitor surface, upper/back edge
  monBottom: { z: 220, y: 955 },  // monitor surface, lower/front edge
  deckFrontZ: 445,
  deckTopY: 935,
  deckLipBottomY: 868,
  frontZ: 330,
  frontTopY: 845,
  kickZ: 300,
};

const webglRoot = document.getElementById('webgl-root');
const cssRoot = document.getElementById('css3d-root');
const crtEl = document.querySelector('.crt');

// the action buttons join the screen UI, like an in-game menu
crtEl.querySelector('.customization').after(document.getElementById('buttons-container'));

const scene = new THREE.Scene();
scene.background = new THREE.Color(ROOM_COLOR);
scene.fog = new THREE.Fog(ROOM_COLOR, 2200, 5200);

const cssScene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 1, 14000);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
webglRoot.appendChild(renderer.domElement);

const cssRenderer = new CSS3DRenderer();
cssRenderer.setSize(innerWidth, innerHeight);
cssRoot.appendChild(cssRenderer.domElement);

const screenObj = new CSS3DObject(crtEl);
cssScene.add(screenObj);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enablePan = false;
controls.minAzimuthAngle = -0.6;
controls.maxAzimuthAngle = 0.6;
controls.minPolarAngle = Math.PI / 2 - 0.6;
controls.maxPolarAngle = Math.PI / 2 + 0.15;

// ---------- texture helpers ----------
const texLoader = new THREE.TextureLoader();

function imageTexture(path) {
  const t = texLoader.load(path);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

function neonTexture(text, color, px = 90) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 256;
  const x = c.getContext('2d');
  x.fillStyle = '#160d2a';
  x.fillRect(0, 0, 1024, 256);
  x.font = `${px}px "Press Start 2P", monospace`;
  x.textAlign = 'center';
  x.textBaseline = 'middle';
  x.shadowColor = color;
  x.shadowBlur = 42;
  x.fillStyle = color;
  for (let i = 0; i < 4; i++) x.fillText(text, 512, 134);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function signTexture(text, color, px = 90) {
  // like neonTexture but on a transparent background (room signs)
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 256;
  const x = c.getContext('2d');
  x.font = `${px}px "Press Start 2P", monospace`;
  x.textAlign = 'center';
  x.textBaseline = 'middle';
  x.shadowColor = color;
  x.shadowBlur = 42;
  x.fillStyle = color;
  for (let i = 0; i < 4; i++) x.fillText(text, 512, 134);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// ---------- room ----------
const flickering = [];

function addSign(text, color, x, y, z, ry = 0, scale = 1) {
  const mat = new THREE.MeshBasicMaterial({
    map: signTexture(text, color),
    transparent: true,
    depthWrite: false,
    fog: false,
  });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(760 * scale, 190 * scale), mat);
  m.position.set(x, y, z);
  m.rotation.y = ry;
  m.userData.base = 0.8 + Math.random() * 0.2;
  m.userData.seed = Math.random() * 100;
  flickering.push(m);
  scene.add(m);
}

function buildRoom(floorY) {
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(10000, 10000),
    new THREE.MeshStandardMaterial({ color: 0x0a0616, roughness: 0.35, metalness: 0.55 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = floorY;
  scene.add(floor);

  const grid = new THREE.GridHelper(10000, 100, 0x2ee6ff, 0x2ee6ff);
  grid.material.transparent = true;
  grid.material.opacity = 0.16;
  grid.position.y = floorY + 2;
  scene.add(grid);

  const backWall = new THREE.Mesh(
    new THREE.PlaneGeometry(10000, 4600),
    new THREE.MeshStandardMaterial({ color: 0x0b0618, roughness: 0.95 })
  );
  backWall.position.set(0, floorY + 2300, -2600);
  scene.add(backWall);

  addSign('$PINO', '#f7ca16', -1050, 700, -2500, 0.12, 1.5);
  addSign('WAGMI', '#2ee6ff', 1100, 850, -2520, -0.1, 1);
  addSign('DEGEN', '#39ff6a', 1250, 180, -2540, -0.06, 0.9);
  addSign('HODL', '#ff6300', -1250, 90, -2540, 0.08, 0.9);
  addSign('GM', '#ff3ea5', -1650, 420, -1750, 0.5, 0.8);
  addSign('TO THE MOON', '#8f7bd8', 1700, 470, -1650, -0.5, 0.7);
}

function buildLights(h) {
  scene.add(new THREE.AmbientLight(0x9080cc, 0.7));

  const key = new THREE.DirectionalLight(0xfff2d8, 1.3);
  key.position.set(400, 700, 900);
  scene.add(key);

  const screenGlow = new THREE.PointLight(0x39ff6a, 0.8, 0, 0);
  screenGlow.position.set(0, h * 0.1, 300);
  scene.add(screenGlow);

  const magenta = new THREE.PointLight(0xff3ea5, 0.5, 0, 0);
  magenta.position.set(-1400, 300, -1000);
  scene.add(magenta);

  const cyan = new THREE.PointLight(0x2ee6ff, 0.5, 0, 0);
  cyan.position.set(1400, 300, -1000);
  scene.add(cyan);
}

// ---------- the machine, from planes and shapes ----------
function buildCabinet() {
  const g = new THREE.Group();
  const C = CAB;
  const halfIn = C.innerW / 2;

  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xf4f2f7, roughness: 0.75, metalness: 0.05 });
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x140b26, roughness: 0.9 });
  const sideMat = new THREE.MeshStandardMaterial({ color: 0xf7ca16, roughness: 0.6 });

  // side silhouette taken from the reference profile (z = depth, y = up)
  const profile = new THREE.Shape();
  profile.moveTo(C.back, 0);
  profile.lineTo(C.back, C.top);
  profile.lineTo(C.marqueeFrontZ, C.top);
  profile.lineTo(C.marqueeFrontZ, C.marqueeBottomY);
  profile.lineTo(C.monTop.z, C.monTop.y);
  profile.lineTo(C.monBottom.z, C.monBottom.y);
  profile.lineTo(C.deckFrontZ, C.deckTopY);
  profile.lineTo(C.deckFrontZ, C.deckLipBottomY);
  profile.lineTo(C.frontZ, C.frontTopY);
  profile.lineTo(C.frontZ, 85);
  profile.lineTo(C.kickZ, 0);
  profile.closePath();

  const sideGeo = new THREE.ExtrudeGeometry(profile, { depth: C.sideT, bevelEnabled: false });
  const sideL = new THREE.Mesh(sideGeo, sideMat);
  sideL.rotation.y = Math.PI / 2;              // extrusion now runs along +X
  sideL.position.x = -halfIn - C.sideT;
  g.add(sideL);

  const sideR = sideL.clone();
  sideR.position.x = halfIn;
  g.add(sideR);

  // optional side art planes, hugging the outside of each panel
  if (TEXTURES.side) {
    const artMat = new THREE.MeshBasicMaterial({ map: imageTexture(TEXTURES.side), transparent: true });
    const artW = C.deckFrontZ - C.back;
    const art = new THREE.Mesh(new THREE.PlaneGeometry(artW, C.height), artMat);
    art.rotation.y = -Math.PI / 2;
    art.position.set(-halfIn - C.sideT - 2, C.height / 2, (C.back + C.deckFrontZ) / 2);
    g.add(art);
    const art2 = art.clone();
    art2.rotation.y = Math.PI / 2;
    art2.position.x = halfIn + C.sideT + 2;
    g.add(art2);
  }

  function panel(w, h, mat) {
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  }

  // marquee (top sign)
  const marqueeMat = TEXTURES.marquee
    ? new THREE.MeshBasicMaterial({ map: imageTexture(TEXTURES.marquee) })
    : new THREE.MeshBasicMaterial({ map: neonTexture('PINORATOR', '#f7ca16', 96) });
  const marqueeH = C.marqueeTopY - C.marqueeBottomY;
  const marquee = panel(C.innerW, marqueeH, marqueeMat);
  marquee.position.set(0, C.marqueeBottomY + marqueeH / 2, C.marqueeFrontZ);
  g.add(marquee);
  flickering.push(Object.assign(marquee, { userData: { base: 1, seed: 7 } }));

  // top lid + back
  const lid = panel(C.innerW, C.marqueeFrontZ - C.back, bodyMat);
  lid.rotation.x = -Math.PI / 2;
  lid.position.set(0, C.top, (C.back + C.marqueeFrontZ) / 2);
  g.add(lid);

  const backP = panel(C.innerW, C.height, darkMat);
  backP.rotation.y = Math.PI;
  backP.position.set(0, C.height / 2, C.back);
  g.add(backP);

  // monitor bay: dark glass behind the UI
  const monDZ = C.monBottom.z - C.monTop.z;
  const monDY = C.monTop.y - C.monBottom.y;
  const monLen = Math.hypot(monDZ, monDY);
  const monCenter = new THREE.Vector3(0, (C.monTop.y + C.monBottom.y) / 2, (C.monTop.z + C.monBottom.z) / 2);
  const monUp = new THREE.Vector3(0, monDY, -monDZ).normalize();
  const monNormal = new THREE.Vector3().crossVectors(new THREE.Vector3(1, 0, 0), monUp).normalize();
  const monQuat = new THREE.Quaternion().setFromRotationMatrix(
    new THREE.Matrix4().makeBasis(new THREE.Vector3(1, 0, 0), monUp, monNormal)
  );

  const glass = panel(C.innerW, monLen, new THREE.MeshBasicMaterial({ color: 0x020204 }));
  glass.quaternion.copy(monQuat);
  glass.position.copy(monCenter).addScaledVector(monNormal, -3);
  g.add(glass);

  // control deck surface
  const deckLen = C.deckFrontZ - C.monBottom.z;
  const deckMat = TEXTURES.deck
    ? new THREE.MeshBasicMaterial({ map: imageTexture(TEXTURES.deck) })
    : bodyMat;
  const deck = panel(C.innerW, deckLen, deckMat);
  deck.rotation.x = -Math.PI / 2 + Math.atan2(C.monBottom.y - C.deckTopY, deckLen);
  deck.position.set(0, (C.monBottom.y + C.deckTopY) / 2, (C.monBottom.z + C.deckFrontZ) / 2);
  g.add(deck);

  // deck lip + front panel + kick
  const lip = panel(C.innerW, C.deckTopY - C.deckLipBottomY, darkMat);
  lip.position.set(0, (C.deckTopY + C.deckLipBottomY) / 2, C.deckFrontZ);
  g.add(lip);

  const frontH = C.frontTopY - 85;
  const frontMat = TEXTURES.front
    ? new THREE.MeshBasicMaterial({ map: imageTexture(TEXTURES.front) })
    : bodyMat;
  const front = panel(C.innerW, frontH, frontMat);
  front.position.set(0, 85 + frontH / 2, C.frontZ);
  g.add(front);

  const shelf = panel(C.innerW, C.frontZ - C.deckFrontZ ? 130 : 130, darkMat);
  shelf.rotation.x = 0.55;
  shelf.position.set(0, (C.deckLipBottomY + C.frontTopY) / 2, (C.deckFrontZ + C.frontZ) / 2);
  g.add(shelf);

  const kick = panel(C.innerW, 92, darkMat);
  kick.rotation.x = 0.32;
  kick.position.set(0, 42, (C.kickZ + C.frontZ) / 2);
  g.add(kick);

  if (!TEXTURES.front) {
    // simple coin door when no front art is given
    const door = new THREE.Mesh(new THREE.BoxGeometry(190, 150, 8),
      new THREE.MeshStandardMaterial({ color: 0x1b1b24, roughness: 0.4, metalness: 0.7 }));
    door.position.set(0, 420, C.frontZ + 5);
    g.add(door);
  }

  if (!TEXTURES.deck) {
    // decorative joystick + buttons on the deck
    const deckMid = new THREE.Vector3(0, (C.monBottom.y + C.deckTopY) / 2 + 8, (C.monBottom.z + C.deckFrontZ) / 2 + 40);
    const baseDome = new THREE.Mesh(new THREE.SphereGeometry(26, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: 0x14141c, roughness: 0.5 }));
    baseDome.position.set(-170, deckMid.y - 6, deckMid.z);
    g.add(baseDome);
    const stick = new THREE.Mesh(new THREE.CylinderGeometry(7, 9, 90, 10),
      new THREE.MeshStandardMaterial({ color: 0x22222c, roughness: 0.35, metalness: 0.4 }));
    stick.position.set(-170, deckMid.y + 40, deckMid.z);
    stick.rotation.z = 0.12;
    g.add(stick);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(24, 20, 16),
      new THREE.MeshStandardMaterial({ color: 0xe2003c, roughness: 0.25 }));
    ball.position.set(-176, deckMid.y + 88, deckMid.z);
    g.add(ball);

    const btnColors = [0xf7ca16, 0xff3ea5, 0x39ff6a];
    btnColors.forEach((col, i) => {
      const btn = new THREE.Mesh(new THREE.SphereGeometry(20, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2),
        new THREE.MeshStandardMaterial({ color: col, roughness: 0.3 }));
      btn.scale.y = 0.55;
      btn.position.set(90 + i * 68, deckMid.y - 4, deckMid.z);
      g.add(btn);
    });
  }

  scene.add(g);

  // hand back the monitor mount so the UI can take its place
  return { group: g, monCenter, monQuat, monNormal, monLen };
}

// ---------- boot ----------
async function init() {
  try {
    await Promise.race([
      Promise.all([document.fonts.load('16px "Press Start 2P"'), document.fonts.ready]),
      new Promise(r => setTimeout(r, 2500)),
    ]);
  } catch { /* fonts are cosmetic; the scene still builds */ }

  const { group, monCenter, monQuat, monNormal, monLen } = buildCabinet();

  // shift the machine so the monitor centers at the origin
  group.position.copy(monCenter).multiplyScalar(-1);
  group.updateMatrixWorld(true);

  screenObj.quaternion.copy(monQuat);
  screenObj.position.copy(monNormal).multiplyScalar(6);

  // first CSS render mounts the element; then it can be measured
  cssRenderer.render(cssScene, camera);
  document.querySelector('.cabinet').style.display = 'none';
  const uiH = crtEl.offsetHeight || 900;
  screenObj.scale.setScalar(Math.min(CAB.innerW / UI_WIDTH, monLen / uiH));

  const mBox = new THREE.Box3().setFromObject(group);
  const mSize = mBox.getSize(new THREE.Vector3());

  buildRoom(mBox.min.y);
  buildLights(mSize.y);

  // player's point of view: standing at the machine, looking down
  const dist = (mSize.y / 2) / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.15;
  camera.position.set(0, dist * 0.42, dist * 0.95);
  controls.target.set(0, 0, 0);
  controls.minDistance = dist * 0.35;
  controls.maxDistance = dist * 1.6;
  controls.update();

  renderer.setAnimationLoop(tick);
  tick(); // paint the first frame synchronously, even in a throttled tab
}

const clock = new THREE.Clock();

function tick() {
  const t = clock.getElapsedTime();
  controls.update();

  if (!REDUCED) {
    for (const m of flickering) {
      const s = m.userData.seed;
      const flick = Math.sin(t * 9 + s) * Math.sin(t * 23 + s * 3);
      m.material.opacity = m.userData.base - (flick > 0.93 ? 0.5 : 0) - 0.06 * Math.sin(t * 2 + s);
      m.material.transparent = true;
    }
  }

  renderer.render(scene, camera);
  cssRenderer.render(cssScene, camera);
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  cssRenderer.setSize(innerWidth, innerHeight);
});

init();
