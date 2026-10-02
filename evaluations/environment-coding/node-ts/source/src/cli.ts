import {readFileSync} from 'node:fs';
import {dispatch} from './api';
try {console.log(JSON.stringify(dispatch(JSON.parse(readFileSync(0,'utf8')))));}
catch(error) {console.error(error instanceof Error ? error.message : String(error));process.exitCode=2;}
