const assert=require('node:assert/strict');
async function state(request,baseURL){const r=await request.get(baseURL+'/api/state');assert.equal(r.status(),200);return r.json();}
async function shown(page,stock,count){await page.waitForFunction(([stock,count])=>document.querySelector('#stock').textContent===String(stock)&&document.querySelectorAll('#reservations li').length===count,[stock,count]);}
async function enter(page,reference,quantity){await page.getByLabel('Customer reference').fill(reference);await page.getByLabel('Quantity',{exact:true}).fill(String(quantity));}
module.exports=async({page,context,request,baseURL,screenshot,newContext})=>{
await page.goto(baseURL);await shown(page,5,0);await enter(page,'Order A',2);await page.getByRole('button',{name:'Reserve',exact:true}).click();await shown(page,3,1);assert.deepEqual(await state(request,baseURL),{stock:3,reservations:[{id:1,reference:'Order A',quantity:2}]});await page.reload();await shown(page,3,1);assert.equal(await page.locator('#reservations li span').innerText(),'Order A — 2');await screenshot();
};
