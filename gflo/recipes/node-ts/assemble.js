// No project code or package lifecycle scripts execute during offline assembly.
const fs = require('node:fs'), cp = require('node:child_process'), path = require('node:path');
fs.mkdirSync('/work/project'); fs.mkdirSync('/work/cache');
for (const name of ['package.json', 'package-lock.json'])
  fs.copyFileSync('/approved/' + name, '/work/project/' + name);
fs.writeFileSync('/tmp/user.npmrc', ''); fs.writeFileSync('/tmp/global.npmrc', '');
const env = {PATH: process.env.PATH, HOME: '/tmp', NPM_CONFIG_CACHE: '/work/cache',
  NPM_CONFIG_USERCONFIG: '/tmp/user.npmrc', NPM_CONFIG_GLOBALCONFIG: '/tmp/global.npmrc',
  NPM_CONFIG_OFFLINE: 'true', NPM_CONFIG_IGNORE_SCRIPTS: 'true',
  NPM_CONFIG_AUDIT: 'false', NPM_CONFIG_FUND: 'false', NPM_CONFIG_UPDATE_NOTIFIER: 'false'};
function run(command, args) {
  const result = cp.spawnSync(command, args, {cwd: '/work/project', env, stdio: ['ignore', 2, 2], timeout: 90000});
  if (result.status !== 0) throw Error('Offline dependency assembly failed');
}
for (const name of fs.readdirSync('/artifacts').sort()) run('npm', ['cache', 'add', '/artifacts/' + name, '--offline', '--ignore-scripts']);
run('npm', ['ci', '--offline', '--ignore-scripts', '--no-audit', '--no-fund']);
for (const name of ['package.json', 'package-lock.json'])
  if (!fs.readFileSync('/approved/' + name).equals(fs.readFileSync('/work/project/' + name))) throw Error('Approved lock changed');
const root = '/work/project/node_modules';
// npm's two known convenience links are unnecessary: invoke the compiler by its path.
for (const [name, target] of [['tsc', '../typescript/bin/tsc'], ['tsserver', '../typescript/bin/tsserver']]) {
  const link = root + '/.bin/' + name;
  if (!fs.lstatSync(link).isSymbolicLink() || fs.readlinkSync(link) !== target) throw Error('Unexpected npm bin layout');
  fs.unlinkSync(link);
}
fs.rmdirSync(root + '/.bin');
function validate(directory) {
  for (const name of fs.readdirSync(directory)) {
    const item = path.join(directory, name), info = fs.lstatSync(item);
    if (info.isDirectory()) validate(item);
    else if (!info.isFile()) throw Error('Unsupported dependency file type');
  }
}
validate(root);
const result = cp.spawnSync('tar', ['--format=ustar', '--owner=0', '--group=0', '--mtime=@0',
  '-C', root, '-cf', '-', '--', ...fs.readdirSync(root).sort()], {stdio: ['ignore', 1, 2], timeout: 30000});
if (result.status !== 0) throw Error('Dependency archive failed');
