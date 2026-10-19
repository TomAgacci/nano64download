function renderGridFromJSON(json) {
  const canvas = document.getElementById("grid");
  const ctx = canvas.getContext("2d");
  const cols = 40, rows = 25;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;

  const screen = json.screen;
  const colors = json.colors;
  const sprites = json.sprites || {};
  const vic = json.vic || {border:6,background:0,scrollX:0,scrollY:0};

  ctx.fillStyle = palette[vic.background % palette.length];
  ctx.fillRect(0,0,canvas.width,canvas.height);

  // border
  ctx.strokeStyle = palette[vic.border % palette.length];
  ctx.strokeRect(0,0,canvas.width,canvas.height);

  for (let i=0;i<screen.length;i++) {
    const x = i % cols;
    const y = Math.floor(i / cols);
    const ch = screen[i];
    const col = colors[i];
    const px = x*cellW - vic.scrollX;
    const py = y*cellH - vic.scrollY;

    ctx.fillStyle = palette[col % palette.length];

    if (ch === 160 || ch === 219) {
      ctx.fillRect(px, py, cellW, cellH);
    } else if (ch === 81) {
      ctx.fillRect(px, py, cellW/2, cellH/2);
      ctx.fillRect(px+cellW/2, py+cellH/2, cellW/2, cellH/2);
    } else {
      ctx.fillRect(px, py, cellW, cellH);
    }
  }

  for (let idx in sprites) {
    const s = sprites[idx];
    ctx.fillStyle = palette[s.color % palette.length];
    ctx.fillRect(s.x, s.y, cellW, cellH);
  }
}
