// ai-analyze.js
async function analyzeBirth(birth, time) {
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ birth, time })
  });
  return await res.json();
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('aiForm');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const birth = form.birth_date.value;
    const time = form.birth_time.value || '00:00';
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerText = 'Analyzing...';

    try {
      const result = await analyzeBirth(birth, time);
      renderResultInPlace(result);
    } catch (err) {
      alert('Analysis failed: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.innerText = 'ANALYZE DESTINY';
    }
  });
});

function renderResultInPlace(res) {
  // Open a new results window or replace page - we'll open /result (server-side) for now
  // But to be purely SPA: we can build DOM in-place. For now show quick overlay then navigate to /result
  // For quick UX: show parsed values in console and navigate to /result page with query
  console.log('Analysis result:', res);
  // Simple client-side render example: open result page with API data in localStorage
  localStorage.setItem('last_analysis', JSON.stringify(res));
  // Redirect to server-rendered result page (fallback)
  window.location.href = '/result';
}

// Additional helpers for client-only rendering (optional)
function drawTimeline(canvasId, arr) {
  const canvas = document.getElementById(canvasId);
  if(!canvas || !arr) return;
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth * devicePixelRatio;
  canvas.height = 160 * devicePixelRatio;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.beginPath();
  ctx.strokeStyle = '#00e0ff';
  ctx.lineWidth = 2.2;
  const w = canvas.offsetWidth;
  const h = 160;
  arr.forEach((v,i)=>{
    const x = (i/(arr.length-1))*w;
    const y = h - (v/100)*h;
    if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();
}
