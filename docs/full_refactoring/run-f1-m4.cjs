// Run the existing M4 suite without replacing historical sprint evidence.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const evidence = path.join(root, 'docs/sprint_2/evidence/s2-x01');
const output = path.join(__dirname, 'evidence/f1');
const backup = path.join(__dirname, 'evidence/f1-original-backup');
function files(dir) { return fs.existsSync(dir) ? fs.readdirSync(dir, {withFileTypes:true}).flatMap(e => e.isDirectory() ? files(path.join(dir,e.name)) : [path.join(dir,e.name)]) : []; }
const original = new Map(files(evidence).map(p=>[path.relative(evidence,p), fs.readFileSync(p)]));
const modifiedAt = new Map(files(evidence).map(p=>[path.relative(evidence,p),fs.statSync(p).mtimeMs]));
const extra = new Map([1440,390].map(width=>{
 const rel=`work-orders-errors-${width}.png`;
 return [rel,fs.readFileSync(path.join(__dirname,'evidence',rel))];
}));
function write(base, rel, data) { const p=path.join(base,rel); fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,data); }
for(const [rel,data] of original) write(backup,rel,data);
const child = spawn(process.execPath, ['run.mjs', ...process.argv.slice(2)], {cwd:path.join(root,'infra/m4'), stdio:'inherit', windowsHide:true});
let restored=false;
function finish(code) {
 if(restored)return; restored=true;
 for(const p of files(evidence)) {
   const rel=path.relative(evidence,p),data=fs.readFileSync(p);
   if(!original.has(rel)||!original.get(rel).equals(data)||modifiedAt.get(rel)!==fs.statSync(p).mtimeMs) write(output,rel,data);
   if(!original.has(rel)) fs.unlinkSync(p);
 }
 for(const [rel,data] of original) write(evidence,rel,data);
 for(const [rel,data] of extra) {
   const current=fs.readFileSync(path.join(__dirname,'evidence',rel));
   if(!current.equals(data)) write(output,rel,current);
   write(path.join(__dirname,'evidence'),rel,data);
 }
 const hashes = [...original].map(([rel,data])=>({file:rel,restored:fs.readFileSync(path.join(evidence,rel)).equals(data),sha256:crypto.createHash('sha256').update(data).digest('hex')}));
 fs.mkdirSync(output,{recursive:true});
 fs.writeFileSync(path.join(output,'historical-evidence-restoration.json'),JSON.stringify({exitCode:code,files:hashes},null,2)+'\n');
 if(hashes.some(h=>!h.restored)) code=1;
 process.exitCode=code;
}
child.on('error',error=>{console.error(error);finish(1);});
child.on('exit',code=>finish(code??1));
