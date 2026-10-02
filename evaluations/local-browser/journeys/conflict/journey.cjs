const assert=require('node:assert/strict');
async function state(request,baseURL){const r=await request.get(baseURL+'/api/state');assert.equal(r.status(),200);return r.json();}
async function shown(page,stock,count){await page.waitForFunction(([stock,count])=>document.querySelector('#stock').textContent===String(stock)&&document.querySelectorAll('#reservations li').length===count,[stock,count]);}
async function enter(page,reference,quantity){await page.getByLabel('Customer reference').fill(reference);await page.getByLabel('Quantity',{exact:true}).fill(String(quantity));}
module.exports=async({page,context,request,baseURL,screenshot,newContext})=>{
const other=await newContext();const second=await other.newPage();await page.goto(baseURL);await second.goto(baseURL);await shown(page,2,0);await shown(second,2,0);await enter(page,'First',2);await enter(second,'Second',2);await page.getByRole('button',{name:'Reserve',exact:true}).click();await shown(page,0,1);await second.getByRole('button',{name:'Reserve',exact:true}).click();await second.waitForFunction(()=>document.querySelector('[role=alert]').textContent.trim().length>0);await shown(second,0,1);assert.deepEqual(await state(request,baseURL),{stock:0,reservations:[{id:1,reference:'First',quantity:2}]});assert.equal(await second.getByLabel('Customer reference').inputValue(),'Second');await screenshot(second);
};
