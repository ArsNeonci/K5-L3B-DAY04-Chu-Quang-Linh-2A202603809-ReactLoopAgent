const $ = id => document.getElementById(id);
let config, finalResult, busy = false, timer;
const notes = {snapshot:'Dữ liệu status cố định; agent vẫn gọi LLM thật.',live:'Gọi API status thật. Dữ liệu thay đổi, có thể timeout hoặc rate limit.',replay:'Phát lại trace thật của case H1 từ eval_after.json; không chạy câu hỏi mới và không gọi API.'};
function modeChanged(){
  $('mode-note').textContent = notes[$('source').value];
  const replay = $('source').value === 'replay';
  ['suite','steps','question','sample'].forEach(id => $(id).disabled = replay || busy);
}
$('source').addEventListener('change', modeChanged);
$('sample').onclick = () => {$('question').value = $('suite').value === 'bonus' ? 'Kiểm tra status GitHub, Vercel và npm. Nêu thời điểm dữ liệu và dẫn nguồn.' : 'GitHub Actions có sự cố gì gần đây? Hãy kiểm tra incident và dẫn nguồn.';};
function eventTitle(e){
  const step = e.step ? `Bước ${e.step} · ` : '';
  const titles = {started:'Bắt đầu điều tra',model_start:'Đang chờ model phản hồi…',model:`Model phản hồi · ${e.tool_calls || 0} tool call`,tool_start:`Đang gọi ${e.name}…`,tool:`Nhận kết quả ${e.name}`,model_retry:'Thử lại kết nối model',validation_missing_source:'Yêu cầu model bổ sung nguồn',completed:'Đã tổng hợp câu trả lời',max_steps:'Đã hết giới hạn lượt gọi model',error:'Gặp lỗi khi thực thi'};
  return step + (titles[e.event] || e.event);
}
function addEvent(e){
  $('timeline').querySelector('.empty')?.remove();
  const item = document.createElement('li'), title = document.createElement('div');
  title.className = 'event-title'; title.textContent = eventTitle(e); item.append(title);
  if(e.event === 'started'){
    const subtitle = document.createElement('div'); subtitle.className='event-sub';
    subtitle.textContent = `${e.provider} / ${e.model} · ${e.mode}\n${e.question}`; item.append(subtitle);
  }
  if(e.event === 'tool'){
    const sub = document.createElement('div'); sub.className='event-sub';
    sub.textContent = e.result?.ok === false ? `Lỗi tool: ${e.result.error} · Trả observation cho model xử lý.` : 'Đã nhận bằng chứng · Đưa kết quả về context của model.';
    item.append(sub); $('tools').textContent = Number($('tools').textContent)+1;
  }
  if(e.event === 'model' || e.event === 'model_retry' || (e.event==='error' && e.error?.startsWith('PROVIDER_ERROR'))) $('models').textContent = e.step;
  const details = document.createElement('details'), summary = document.createElement('summary'), pre = document.createElement('pre');
  summary.textContent = 'Xem dữ liệu bước này'; pre.textContent = JSON.stringify(e,null,2); details.append(summary,pre); item.append(details);
  $('timeline').append(item); $('timeline').scrollTop = $('timeline').scrollHeight;
  $('status').textContent = e.event === 'tool_start' ? 'Đang gọi tool' : e.event === 'model_start' ? 'Đang gọi model' : 'Đang điều tra';
}
function showAnswer(text){
  $('answer').replaceChildren();
  // Treat all model and tool content as text; only link explicit HTTP(S) URLs.
  for(const part of text.split(/(https?:\/\/[^\s<>"\u0027]+)/g)){
    if(/^https?:\/\//.test(part)){
      const url = part.replace(/[)\].,;:!?]+$/, '');
      const link = document.createElement('a'); link.textContent=url; link.href=url; link.target='_blank'; link.rel='noopener noreferrer'; $('answer').append(link);
      if(url.length < part.length) $('answer').append(document.createTextNode(part.slice(url.length)));
    } else $('answer').append(document.createTextNode(part));
  }
}
function finish(result){
  finalResult=result;
  $('status').textContent = {completed:'Hoàn tất',error:'Có lỗi',max_steps:'Hết giới hạn'}[result.status] || result.status;
  showAnswer(result.answer || 'Chưa có câu trả lời hoàn chỉnh. Xem tiến trình và lỗi bên dưới.');
  $('error').textContent=result.error || '';
  $('raw').textContent=JSON.stringify(result,null,2); $('raw-wrap').hidden=false; $('download').disabled=false;
}
$('form').onsubmit = async event => {
  event.preventDefault(); if(busy || !config) return;
  busy=true; finalResult=null; $('run').disabled=true; $('source').disabled=true; modeChanged();
  $('download').disabled=true; $('raw-wrap').hidden=true; $('error').textContent=''; $('timeline').replaceChildren();
  $('answer').textContent='Agent đang điều tra…'; $('models').textContent='0'; $('tools').textContent='0'; $('status').textContent='Đang kết nối';
  const start=Date.now(); $('elapsed').textContent='0s'; timer=setInterval(()=>{$('elapsed').textContent=((Date.now()-start)/1000).toFixed(1)+'s';},100);
  try{
    const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':config.token},body:JSON.stringify({question:$('question').value,source:$('source').value,bonus:$('suite').value==='bonus',max_steps:Number($('steps').value)})});
    if(!response.ok) throw new Error((await response.json()).error || `HTTP ${response.status}`);
    const reader=response.body.getReader(), decoder=new TextDecoder(); let pending='';
    while(true){
      const {value,done}=await reader.read(); pending+=decoder.decode(value,{stream:!done});
      const lines=pending.split('\n'); pending=lines.pop();
      for(const line of lines){if(!line.trim())continue; const e=JSON.parse(line); if(e.event==='result')finish(e.result);else addEvent(e);}
      if(done)break;
    }
    if(!finalResult) throw new Error('Kết nối đã đóng trước khi nhận được kết quả.');
  }catch(error){$('error').textContent=error.message; $('status').textContent='Có lỗi'; $('answer').textContent='Chưa nhận được kết quả hoàn chỉnh.';}
  finally{clearInterval(timer);busy=false;$('run').disabled=false;$('source').disabled=false;modeChanged();}
};
$('download').onclick=()=>{if(!finalResult)return;const url=URL.createObjectURL(new Blob([JSON.stringify(finalResult,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='agent-demo-result.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
async function init(){
  $('run').disabled=true;modeChanged();
  try{const response=await fetch('/api/config');if(!response.ok)throw new Error('Không đọc được cấu hình.');config=await response.json();$('config').textContent=`${config.provider} / ${config.model || 'chưa đặt MODEL'} · ${config.key_ready ? 'Đã có API key' : 'Chưa có API key'}`;if(!config.model || !config.key_ready)$('source').value='replay';$('run').disabled=false;modeChanged();}
  catch(error){$('error').textContent=error.message;}
}
init();
