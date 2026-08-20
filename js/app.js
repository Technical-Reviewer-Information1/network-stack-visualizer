(function () {
  'use strict';
  const T = window.Tools, $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  function el(n, a, t) { const e = document.createElementNS(NS, n); for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; }

  /* ---------- STEP1 階層 ---------- */
  const LAYERS = [
    { n: '第4層', t: 'アプリケーション層', proto: 'HTTP・SMTP・POP・DNS', role: 'app' },
    { n: '第3層', t: 'トランスポート層', proto: 'TCP・UDP', role: 'trans' },
    { n: '第2層', t: 'インターネット層', proto: 'IP', role: 'inet' },
    { n: '第1層', t: 'ネットワークインタフェース層', proto: 'イーサネット・無線LAN', role: 'phys' }
  ];
  const ROLES = [
    { id: 'app', t: 'ネットワークを利用するアプリケーション間でやり取りする。' },
    { id: 'trans', t: '通信の信頼性を確保し、データの送受信を制御する。' },
    { id: 'inet', t: '送信先のIPアドレスをもとに、最適な通信経路を決定しデータを転送する。' },
    { id: 'phys', t: '物理的な通信手段を用いてデータを送受信する。' }
  ];
  let sel = null, placed = {};

  function drawLayers() {
    $('roles').innerHTML = '';
    ROLES.forEach(r => {
      const b = document.createElement('button');
      b.className = 'r' + (Object.values(placed).indexOf(r.id) >= 0 ? ' used' : '');
      b.setAttribute('aria-pressed', sel === r.id);
      b.textContent = r.t;
      b.addEventListener('click', () => { sel = (sel === r.id ? null : r.id); drawLayers(); });
      $('roles').appendChild(b);
    });
    $('layers').innerHTML = '';
    LAYERS.forEach((L, i) => {
      const d = document.createElement('div');
      d.className = 'layer';
      const got = placed[i];
      const zoneCls = got ? (got === L.role ? 'dropzone filled ok' : 'dropzone filled ng') : 'dropzone';
      d.innerHTML = '<div><div class="n">' + L.n + '</div><div class="t">' + L.t + '</div>' +
        '<div class="proto">' + L.proto + '</div></div>' +
        '<div class="' + zoneCls + '">' + (got ? ROLES.find(r => r.id === got).t : '（ここに役割を入れる）') + '</div>';
      d.addEventListener('click', () => {
        if (!sel) {
          if (placed[i]) { delete placed[i]; drawLayers(); }
          else { const f = $('layFb'); f.hidden = false; f.className = 'note warn'; f.textContent = 'まず上の役割カードを1つえらんでください。'; }
          return;
        }
        placed[i] = sel;
        const ok = sel === L.role;
        const f = $('layFb'); f.hidden = false;
        f.className = 'note ' + (ok ? 'ok' : 'ng');
        f.innerHTML = ok ? '正解。' + L.t + 'は「' + ROLES.find(r => r.id === L.role).t + '」を担当します。'
          : 'この役割は <strong>' + LAYERS.find(x => x.role === sel).t + '</strong> のものです。' +
            L.t + 'は「' + ROLES.find(r => r.id === L.role).t + '」を担当します。';
        sel = null;
        drawLayers();
      });
      $('layers').appendChild(d);
    });
    const score = Object.keys(placed).filter(i => placed[i] === LAYERS[i].role).length;
    $('layScore').textContent = score + ' / 4';
  }

  /* ---------- STEP2 カプセル化 ---------- */
  const STAGES = [
    { t: '送信：アプリケーション層', segs: [['データ', '#123a6b']],
      d: 'アプリケーションが用意したデータそのもの。まだ何も付いていません。' },
    { t: '送信：トランスポート層', segs: [['TCPヘッダ', '#8a5a00'], ['データ', '#123a6b']],
      d: 'TCP（またはUDP）のヘッダが付きます。ここにポート番号や順序の情報が入り、これで<strong>パケット</strong>になります。' },
    { t: '送信：インターネット層', segs: [['IPヘッダ', '#1f7a3d'], ['TCPヘッダ', '#8a5a00'], ['データ', '#123a6b']],
      d: 'IPヘッダが付きます。<strong>送信元と宛先のIPアドレス</strong>が入り、経路を決められるようになります。' },
    { t: '送信：ネットワークインタフェース層', segs: [['MACヘッダ', '#8a2f1f'], ['IPヘッダ', '#1f7a3d'], ['TCPヘッダ', '#8a5a00'], ['データ', '#123a6b'], ['FCS', '#5a3d8a']],
      d: 'いちばん外側の封筒が付き、実際の回線に流れます。ここまでが<strong>カプセル化</strong>です。' },
    { t: '受信：ネットワークインタフェース層', segs: [['IPヘッダ', '#1f7a3d'], ['TCPヘッダ', '#8a5a00'], ['データ', '#123a6b']],
      d: '受け取った側では、外側から1枚ずつはがしていきます。まず外側の封筒をはがしました。' },
    { t: '受信：インターネット層', segs: [['TCPヘッダ', '#8a5a00'], ['データ', '#123a6b']],
      d: 'IPヘッダをはがし、「自分あてだ」と確認します。' },
    { t: '受信：トランスポート層', segs: [['データ', '#123a6b']],
      d: 'TCPヘッダをはがし、順序を並べ直します。欠けていれば再送を求めます。' },
    { t: '受信：アプリケーション層', segs: [['データ', '#123a6b']],
      d: '元のデータがアプリケーションに届きました。<strong>送る側と同じ形にもどっています。</strong>' }
  ];
  const HDR = { 'TCPヘッダ': 20, 'IPヘッダ': 20, 'MACヘッダ': 14, 'FCS': 4 };
  function msgBytes() {
    const t = ($('msgIn') ? $('msgIn').value : 'こんにちは');
    return { text: t, n: new TextEncoder().encode(t).length };
  }
  function drawSize() {
    if (!$('szData')) return;
    const m = msgBytes();
    const head = HDR['TCPヘッダ'] + HDR['IPヘッダ'] + HDR['MACヘッダ'] + HDR['FCS'];
    $('szData').textContent = m.n + ' バイト';
    $('szHead').textContent = head + ' バイト';
    $('szAll').textContent = (m.n + head) + ' バイト';
    const n = $('szNote');
    const ratio = m.n ? Math.round(head / (m.n + head) * 100) : 100;
    n.className = 'note ' + (ratio >= 60 ? 'warn' : 'info');
    n.innerHTML = 'UTF-8では日本語1文字が3バイト、半角英数字が1バイトです。' +
      'この通信では、実際に流れるデータのうち <strong>' + ratio + '％がヘッダ</strong>です。' +
      (ratio >= 60
        ? '<br><strong>短いデータほど、ヘッダの割合が大きくなり効率が落ちます。</strong>まとめて送るほうが効率的なのはこのためです。'
        : '<br>データが長くなるほど、ヘッダの割合は小さくなります。');
  }
  let stage = 0, capTimer = null;
  function drawCap() {
    const s = STAGES[stage];
    const mb = msgBytes();
    const W = 660, H = 150;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: '100%', role: 'img', 'aria-label': 'カプセル化のようす' });
    const total = s.segs.reduce((a, x) => a + (x[0] === 'データ' ? 3 : 1), 0);
    let x = 30;
    const unitW = (W - 60) / total;
    s.segs.forEach(([label, col]) => {
      const w = unitW * (label === 'データ' ? 3 : 1);
      svg.appendChild(el('rect', { x, y: 52, width: w - 3, height: 46, fill: col, class: 'seg' }));
      const isData = label === 'データ';
      const main = isData ? (mb.text.length > 10 ? mb.text.slice(0, 10) + '…' : (mb.text || 'データ')) : label;
      svg.appendChild(el('text', { x: x + w / 2 - 1.5, y: isData ? 72 : 78, class: 'segl' }, main));
      svg.appendChild(el('text', { x: x + w / 2 - 1.5, y: isData ? 88 : 0, class: 'segl', 'font-size': 10, opacity: isData ? .85 : 0 },
        isData ? (mb.n + ' バイト') : ''));
      if (!isData) svg.appendChild(el('text', { x: x + w / 2 - 1.5, y: 92, class: 'segl', 'font-size': 9.5, opacity: .8 }, (HDR[label] || 0) + 'B'));
      x += w;
    });
    svg.appendChild(el('text', { x: 30, y: 34, class: 'stage', 'font-weight': 700 }, s.t));
    svg.appendChild(el('text', { x: 30, y: 122, class: 'stage' },
      stage < 4 ? '↓ 下の層へ（ヘッダが増える）' : (stage < 7 ? '↑ 上の層へ（ヘッダをはがす）' : '完了')));
    const box = $('capBox'); box.innerHTML = ''; box.appendChild(svg);
    $('capStage').textContent = (stage + 1) + ' / ' + STAGES.length;
    const n = $('capNote');
    n.className = 'note ' + (stage === STAGES.length - 1 ? 'ok' : 'info');
    n.innerHTML = s.d;
    // 対応する層を光らせる
    const map = [0, 1, 2, 3, 3, 2, 1, 0];
    [...$('layers').children].forEach((d, i) => d.classList.toggle('hot', i === map[stage]));
  }

  /* ---------- STEP3 TCP/UDP ---------- */
  function runProto(kind) {
    const loss = +$('loss').value / 100;
    const rows = [];
    let time = 0, delivered = 0;
    for (let i = 1; i <= 10; i++) {
      let tries = 0, ok = false;
      do {
        tries++; time++;
        ok = Math.random() >= loss;
        if (kind === 'udp') break;
      } while (!ok && tries < 6);
      if (ok) delivered++;
      rows.push({ i, tries, ok });
    }
    $('tuTable').innerHTML = '<thead><tr><th>パケット</th><th>送った回数</th><th>結果</th></tr></thead><tbody>' +
      rows.map(r => '<tr><td>' + r.i + '</td><td class="mono">' + r.tries + '</td><td style="color:' +
        (r.ok ? 'var(--ok)' : 'var(--ng)') + ';font-weight:700">' + (r.ok ? '届いた' : '失われた') + '</td></tr>').join('') + '</tbody>';
    const n = $('tuNote');
    n.className = kind === 'tcp' ? 'note ok' : 'note warn';
    n.innerHTML = '<strong>' + (kind === 'tcp' ? 'TCP' : 'UDP') + '</strong>で10個のパケットを送りました。' +
      '届いたのは <strong>' + delivered + ' 個</strong>、送信の総回数は <strong>' + time + ' 回</strong>。<br>' +
      (kind === 'tcp'
        ? '失われたパケットを<strong>再送</strong>するので、ほぼすべて届きます。そのかわり送信回数が増え、時間がかかります。'
        : '<strong>再送しない</strong>ので、失われたぶんは欠けたままです。そのかわり送信回数は10回で済み、遅れが小さくなります。' +
          '動画や通話では、少し欠けても遅れないほうが大切なのでUDPが使われます。');
  }

  /* ---------- STEP4 クイズ ---------- */
  const QUIZ = [
    { t: 'トランスポート層の役割はどれか。',
      choices: ['通信の信頼性を確保し、データの送受信を制御する', 'ネットワークを利用するアプリケーション間でやり取りする',
                '送信先のIPアドレスをもとに最適な経路を決定し転送する', '物理的な通信手段を用いてデータを送受信する'],
      a: '通信の信頼性を確保し、データの送受信を制御する',
      why: 'TCPやUDPが属する層です。届いたかどうかの確認や順序の管理を行います。' },
    { t: 'インターネット層の役割はどれか。',
      choices: ['送信先のIPアドレスをもとに最適な経路を決定し転送する', '通信の信頼性を確保する',
                'アプリケーション間でやり取りする', '物理的な通信手段でデータを送受信する'],
      a: '送信先のIPアドレスをもとに最適な経路を決定し転送する',
      why: 'IPが属する層です。宛先まで届けるための経路を決めます。' },
    { t: 'TCPとUDPに共通することはどれか。',
      choices: ['データをパケットという小さな単位に分割して管理する', 'どちらも必ず再送を行う',
                'どちらも遅延を最小にする', 'どちらもIPアドレスを付与する'],
      a: 'データをパケットという小さな単位に分割して管理する',
      why: 'どちらもトランスポート層のプロトコルで、データをパケット単位で扱います。再送するのはTCPだけ、IPアドレスを付けるのはIPです。' },
    { t: 'IPの説明として正しいものはどれか。',
      choices: ['パケットを正しい送り先に届けるためにIPアドレスを付与する', 'データの完全性や順序性を保証する',
                '再送を行わず遅延を最小限に抑える', 'アプリケーション間のやり取りを担当する'],
      a: 'パケットを正しい送り先に届けるためにIPアドレスを付与する',
      why: '完全性・順序性はTCP、再送しないのはUDPの説明です。' },
    { t: 'UDPの説明として正しいものはどれか。',
      choices: ['再送を行わず、遅延を最小限に抑えられる', 'データの完全性や順序性を保証する',
                '必ず再送して確実に届ける', 'IPアドレスを付与する'],
      a: '再送を行わず、遅延を最小限に抑えられる',
      why: '「信頼性が高い」「順序を保証する」はTCPの説明です。<strong>TCPとUDPの説明を入れかえた選択肢</strong>がよく出ます。' },
    { t: '通信プロトコルが階層に分かれていることの利点はどれか。',
      choices: ['ある階層を変更しても他の階層に影響を与えず、新しい技術を導入しやすい',
                'すべての階層が同じプロトコルを使うので互換性が高まる',
                '上位層を変更すると下位層も必ず変更できる', '階層構造にすると通信速度が上がる'],
      a: 'ある階層を変更しても他の階層に影響を与えず、新しい技術を導入しやすい',
      why: '役割を分けておくことで、たとえば無線LANという新しい下位層が登場しても、上位のHTTPなどはそのまま使えます。' },
    { t: '送信側でデータにヘッダが付いていく順番として正しいものはどれか。',
      choices: ['アプリケーション → トランスポート → インターネット → ネットワークインタフェース',
                'ネットワークインタフェース → インターネット → トランスポート → アプリケーション',
                'インターネット → トランスポート → アプリケーション → ネットワークインタフェース',
                'トランスポート → アプリケーション → ネットワークインタフェース → インターネット'],
      a: 'アプリケーション → トランスポート → インターネット → ネットワークインタフェース',
      why: '送るときは上から下へ包んでいき、受け取るときは下から上へはがしていきます。' }
  ];
  let qList = [], qi = 0, qScore = 0;
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  function startQuiz() { qList = shuffle(QUIZ); qi = 0; qScore = 0; renderQ(); }
  function renderQ() {
    if (qi >= qList.length) {
      $('qText').textContent = qScore + ' / ' + qList.length + ' 問正解';
      $('qChoices').innerHTML = ''; $('qFb').hidden = true; $('qNext').disabled = true;
      $('qProgress').textContent = qList.length + ' / ' + qList.length; return;
    }
    const it = qList[qi];
    $('qProgress').textContent = (qi + 1) + ' / ' + qList.length;
    $('qScore').textContent = qScore;
    $('qText').textContent = it.t;
    const box = $('qChoices'); box.className = 'choice4'; box.innerHTML = '';
    shuffle(it.choices).forEach(c => {
      const b = document.createElement('button');
      b.className = 'btn'; b.textContent = c; b.dataset.c = c;
      b.addEventListener('click', () => answerQ(c));
      box.appendChild(b);
    });
    $('qFb').hidden = true; $('qNext').disabled = true;
    $('qNext').textContent = (qi === qList.length - 1) ? '結果を見る' : '次の問題';
  }
  function answerQ(c) {
    const it = qList[qi], ok = c === it.a, box = $('qChoices');
    box.classList.add('locked');
    [...box.children].forEach(b => {
      if (b.dataset.c === it.a) b.classList.add('correct');
      else if (b.dataset.c === c) b.classList.add('wrong');
    });
    if (ok) qScore++;
    const fb = $('qFb');
    fb.className = 'note ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = (ok ? '正解。' : '正解は「<strong>' + it.a + '</strong>」。') + it.why;
    fb.hidden = false;
    $('qScore').textContent = qScore; $('qNext').disabled = false;
  }

  function init() {
    $('layReset').addEventListener('click', () => { placed = {}; sel = null; $('layFb').hidden = true; drawLayers(); });
    $('layShow').addEventListener('click', () => {
      LAYERS.forEach((L, i) => placed[i] = L.role);
      const f = $('layFb'); f.hidden = false; f.className = 'note info';
      f.innerHTML = '答えを表示しました。<strong>信頼性＝トランスポート層、経路＝インターネット層</strong>という対応を覚えておきましょう。';
      drawLayers();
    });
    $('capNext').addEventListener('click', () => { stage = (stage + 1) % STAGES.length; drawCap(); });
    if ($('msgIn')) $('msgIn').addEventListener('input', function () { drawSize(); drawCap(); });
    document.querySelectorAll('[data-msg]').forEach(function (b) {
      b.addEventListener('click', function () { $('msgIn').value = b.dataset.msg; drawSize(); drawCap(); });
    });
    drawSize();
    $('capReset').addEventListener('click', () => { stage = 0; drawCap(); });
    $('capAuto').addEventListener('click', () => {
      if (capTimer) { clearInterval(capTimer); capTimer = null; $('capAuto').textContent = '自動で動かす'; return; }
      $('capAuto').textContent = '止める';
      capTimer = setInterval(() => { stage = (stage + 1) % STAGES.length; drawCap(); }, 1500);
    });
    $('loss').addEventListener('input', () => $('lossV').textContent = $('loss').value);
    $('runTcp').addEventListener('click', () => runProto('tcp'));
    $('runUdp').addEventListener('click', () => runProto('udp'));
    $('qNext').addEventListener('click', () => { qi++; renderQ(); });
    $('qReset').addEventListener('click', startQuiz);
    window.Terms.glossary($('glossBox'), ['プロトコル', 'TCP/IP', 'TCP', 'UDP', 'IP', 'パケット', 'IPアドレス', 'HTTP']);
    drawLayers(); drawCap(); startQuiz();
    window.Terms.attach();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
