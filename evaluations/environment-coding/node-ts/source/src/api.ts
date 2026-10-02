import {total} from './domain';
export function dispatch(payload:any): unknown {
 if (payload.action==='total') return total(payload.values);
 throw new Error('unknown action');
}
