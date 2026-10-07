function togglePassword(id){const input=document.getElementById(id); if(!input)return; input.type=input.type==='password'?'text':'password';}
document.querySelectorAll('.flash').forEach((el)=>setTimeout(()=>{if(el)el.remove()},5000));
