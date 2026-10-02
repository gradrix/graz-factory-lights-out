export function total(values: unknown): number {
 if (!Array.isArray(values) || values.some(v => !Number.isSafeInteger(v))) throw new Error('integers required');
 const result=values.reduce((a:number,b:number)=>a+b,0);
 if (!Number.isSafeInteger(result)) throw new Error('overflow');
 return result;
}
