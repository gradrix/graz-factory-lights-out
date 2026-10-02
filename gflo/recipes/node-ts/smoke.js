const fs = require('node:fs'), cp = require('node:child_process');
if (process.getuid() === 0 || fs.readdirSync('/dev').some(n => n.startsWith('nvidia')) || fs.existsSync('/var/run/docker.sock')) throw Error('Unexpected executor privilege/device');
const status = Object.fromEntries(fs.readFileSync('/proc/self/status', 'utf8').trim().split('\n').map(line => { const i=line.indexOf(':'); return [line.slice(0,i),line.slice(i+1).trim()]; }));
if (BigInt('0x'+status.CapEff) !== 0n || status.NoNewPrivs !== '1' || fs.readFileSync('/proc/net/route','utf8').includes('eth0')) throw Error('Unexpected capability/network');
if (!process.version.startsWith('v22.')) throw Error('Node 22 required');
fs.writeFileSync('/work/smoke.ts', `import { Buffer } from 'node:buffer';
import type { Dispatcher } from 'undici-types';
const method: Dispatcher.HttpMethod = 'GET';
console.log(method + ':' + Buffer.from('cpu-only').toString('utf8'));
`);
const compiled = cp.spawnSync('node', ['/node_modules/typescript/bin/tsc', '/work/smoke.ts',
  '--strict', '--target', 'ES2022', '--module', 'commonjs', '--moduleResolution', 'node',
  '--types', 'node', '--outDir', '/work/out'], {encoding: 'utf8', timeout: 30000, maxBuffer: 65536});
if (compiled.status !== 0) throw Error(compiled.stdout + compiled.stderr);
const executed = cp.spawnSync('node', ['/work/out/smoke.js'], {encoding: 'utf8', timeout: 10000, maxBuffer: 65536});
if (executed.status !== 0 || executed.stdout.trim() !== 'GET:cpu-only') throw Error('Wrong TypeScript result');
const npm = cp.spawnSync('npm', ['--version'], {encoding: 'utf8', timeout: 10000, maxBuffer: 65536});
if (npm.status !== 0) throw Error('npm probe failed');
console.log(JSON.stringify({node: process.version, npm: npm.stdout.trim(), platform: process.platform,
  machine: process.arch, uid: String(process.getuid()), capabilities: status.CapEff, gpu_devices: 'absent', docker_socket: 'absent', typescript: require('/node_modules/typescript/package.json').version,
  node_types: require('/node_modules/@types/node/package.json').version,
  undici_types: require('/node_modules/undici-types/package.json').version}));
