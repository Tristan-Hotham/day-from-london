/* A day from London: where a traveller leaving Charing Cross at dawn could reach in 12 hours, in 1750, the 1830s, 1850,
 * 1910 and today. Modelled hours on a 2 km grid drawn as transparent images over a plain MapLibre base map (OpenFreeMap
 * Positron). Tap anywhere for the hours in every era (read from a small lookup image); towns, documented journeys and the
 * networks of each era as toggleable layers. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const BCOL = ['#6E1C17', '#A8382A', '#D2643A', '#E8955A', '#F2C07E', '#F8E2AE', '#C9D6DC', '#E6E2DA'];
  const BANDS = [0, 2, 4, 6, 8, 10, 12, 24, 1e9];
  const ECOL = ['#8A6A3B', '#D08A1E', '#2F7FB8', '#3B8B5A', '#B4442E'];
  let map = null, D = null, era = 0, timer = null, LK = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  const hm = h => { if (h == null) return 'beyond the model'; if (h < 1) return Math.round(h * 60) + ' min'; const H = Math.floor(h), M = Math.round((h - H) * 60); return M === 60 ? (H + 1) + ' h' : H + ' h' + (M ? ' ' + String(M).padStart(2, '0') + ' min' : ''); };
  const dayStr = h => h == null ? '' : h <= 12 ? 'within the day' : h <= 24 ? 'a second day' : 'about ' + Math.ceil(h / 12) + ' travelling days';
  function bandColor(h) { if (h == null) return '#E6E2DA'; for (let k = 0; k < BCOL.length; k++) if (h < BANDS[k + 1]) return BCOL[k]; return BCOL[BCOL.length - 1]; }

  function lookup(lng, lat) {
    if (!LK) return null;
    const [x0, y0, x1, y1] = D.bounds, w = D.lookup.w, h = D.lookup.h;
    const c = Math.floor((lng - x0) / (x1 - x0) * w), r = Math.floor((y1 - lat) / (y1 - y0) * h);
    if (c < 0 || c >= w || r < 0 || r >= h) return null;
    return D.eras.map((e, k) => { const tr = Math.floor(k / 3), tc = k % 3; const v = LK[((tr * h + r) * (w * 3) + tc * w + c) * 4]; return v === 255 ? undefined : v === 252 ? null : v / 2; });
  }
  function popupHtml(title, sub, hrs, extra) {
    let h = `<b class="t">${esc(title)}</b>${sub ? `<div class="nt">${esc(sub)}</div>` : ''}<table class="hrs">`;
    D.labels.forEach((l, k) => { const v = hrs[k]; if (v === undefined) return; h += `<tr><td>${esc(l)}</td><td class="${k === era ? 'b' : ''}"><span style="display:inline-block;width:9px;height:9px;background:${bandColor(v)};border:1px solid #9C8656;margin-right:5px"></span>${hm(v)}${v != null ? ' <span class="nt" style="display:inline">(' + dayStr(v) + ')</span>' : ''}</td></tr>`; });
    h += '</table>' + (extra || '');
    h += `<p class="nt">Modelled hours from Charing Cross, leaving at dawn, on a 2 km grid. Model error in each era: about ${D.band.map((b, k) => D.labels[k] + ' ' + Math.round(b) + '%').join(', ')} (median, against documented journeys).</p>`;
    return h;
  }
  function showPopup(ll, title, sub, hrs, extra) {
    new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(popupHtml(title, sub, hrs, extra)).addTo(map);
  }
  function corners() { const [x0, y0, x1, y1] = D.bounds; return [[x0, y1], [x1, y1], [x1, y0], [x0, y0]]; }
  function setEra(k) {
    era = k;
    map.getSource('hours').updateImage({ url: `img/hours_${D.eras[k]}.png`, coordinates: corners() });
    const hasRoads = k <= 1;
    if (hasRoads) map.getSource('roads').updateImage({ url: `img/roads_${D.eras[k]}.png`, coordinates: corners() });
    const rv = document.getElementById('lyR').checked;
    map.setLayoutProperty('roads', 'visibility', rv && hasRoads ? 'visible' : 'none');
    map.setLayoutProperty('rail51', 'visibility', rv && (k === 2 || k === 3) ? 'visible' : 'none');
    map.setLayoutProperty('inferred', 'visibility', rv && k === 3 ? 'visible' : 'none');
    ['iso', 'isoband'].forEach(id => map.getSource(id).setData({ type: 'Feature', properties: {}, geometry: id === 'iso' ? D.iso[D.eras[k]].base : { type: 'MultiLineString', coordinates: D.iso[D.eras[k]].fast.coordinates.concat(D.iso[D.eras[k]].slow.coordinates) } }));
    map.setPaintProperty('towns', 'circle-color', ['match', ['get', 'b' + k], 0, BCOL[0], 1, BCOL[1], 2, BCOL[2], 3, BCOL[3], 4, BCOL[4], 5, BCOL[5], 6, '#9FB4BE', '#BDB6A8']);
    map.setFilter('docs', ['==', ['get', 'e'], k]);
    document.querySelectorAll('.eras button').forEach((b, i) => b.setAttribute('aria-pressed', i === k));
    const a = D.area[k];
    document.getElementById('keyArea').textContent = `${D.labels[k]}: ${a.km2.toLocaleString('en-GB')} km² within 12 hours (${Math.round(a.share)}% of Great Britain)${D.eras[k] === '1750' ? '; a rough sketch' : (D.eras[k] === '1850' || D.eras[k] === '1910') ? '; a lower bound' : ''}`;
    document.getElementById('keyNet').textContent = ['Roads: turnpikes of 1750 (dark), other main roads (light)', 'Roads: turnpikes of 1830 (dark), other main roads (light)', 'Railways open in 1851', 'Railways of 1910: the 1851 lines, today’s lines and inferred closed lines (dashed)', 'Today: motorways and A roads, and the railways (base map)'][k];
  }
  function setup() {
    map.addSource('hours', { type: 'image', url: 'img/hours_1750.png', coordinates: corners() });
    map.addSource('roads', { type: 'image', url: 'img/roads_1750.png', coordinates: corners() });
    const firstSym = map.getStyle().layers.find(l => l.type === 'symbol');
    const before = firstSym ? firstSym.id : undefined;
    map.addLayer({ id: 'hours', type: 'raster', source: 'hours', paint: { 'raster-opacity': 0.82, 'raster-fade-duration': 0, 'raster-resampling': 'nearest' } }, before);
    map.addLayer({ id: 'roads', type: 'raster', source: 'roads', paint: { 'raster-opacity': 0.75, 'raster-fade-duration': 0 } }, before);
    map.addSource('rail51', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'MultiLineString', coordinates: D.rail1851 } }, attribution: '1851 rail lines: Satchell et al. 2023, CC BY 4.0' });
    map.addLayer({ id: 'rail51', type: 'line', source: 'rail51', layout: { visibility: 'none' }, paint: { 'line-color': '#2B2119', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 10, 2] } }, before);
    map.addSource('inferred', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'MultiLineString', coordinates: D.inferred } } });
    map.addLayer({ id: 'inferred', type: 'line', source: 'inferred', layout: { visibility: 'none' }, paint: { 'line-color': '#3B6B4A', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 10, 2], 'line-dasharray': [2, 1.5] } }, before);
    map.addSource('isoband', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'isoband', type: 'line', source: 'isoband', paint: { 'line-color': '#2B2119', 'line-width': 1.2, 'line-dasharray': [2, 2], 'line-opacity': 0.8 } });
    map.addSource('iso', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'iso', type: 'line', source: 'iso', paint: { 'line-color': '#2B2119', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 2.2, 10, 3.5] } });
    const tf = D.towns.map((t, i) => { const p = { i, n: t.n }; t.h.forEach((h, k) => { let b = 7; if (h != null) for (let j = 0; j < 8; j++) if (h < BANDS[j + 1]) { b = j; break; } p['b' + k] = b; }); return { type: 'Feature', properties: p, geometry: { type: 'Point', coordinates: [t.lo, t.la] } }; });
    map.addSource('towns', { type: 'geojson', data: { type: 'FeatureCollection', features: tf } });
    map.addLayer({ id: 'towns', type: 'circle', source: 'towns', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, small ? 3.6 : 4.5, 8, 7, 12, 9], 'circle-color': BCOL[0], 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.6 } });
    map.addLayer({ id: 'tlbl', type: 'symbol', source: 'towns', minzoom: 5.2, layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.6 } });
    const df = D.docs.map((d, i) => ({ type: 'Feature', properties: { i, e: D.eras.indexOf(d.e) }, geometry: { type: 'Point', coordinates: [0, 0] } }));
    D.docs.forEach((d, i) => { const t = D.towns.find(x => x.n === d.n); df[i].geometry.coordinates = t ? [t.lo, t.la] : [0, 0]; });
    map.addSource('docs', { type: 'geojson', data: { type: 'FeatureCollection', features: df.filter(f => f.geometry.coordinates[0] !== 0) } });
    map.addLayer({ id: 'docs', type: 'circle', source: 'docs', layout: { visibility: 'none' }, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 8, 10, 13], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#2B2119', 'circle-stroke-width': 2 } });
    map.on('click', e => {
      const f = map.queryRenderedFeatures(e.point, { layers: ['towns', 'docs'].filter(l => map.getLayoutProperty(l, 'visibility') !== 'none') });
      if (f.length) { const t = D.towns.find(x => x.n === f[0].properties.n) || D.towns.find(x => x.n === D.docs[f[0].properties.i].n); openTown(t); return; }
      const h = lookup(e.lngLat.lng, e.lngLat.lat);
      if (!h || h.every(v => v === undefined)) return;
      showPopup(e.lngLat, `${e.lngLat.lat.toFixed(3)}, ${e.lngLat.lng.toFixed(3)}`, 'This 2 km square', h);
    });
    ['towns', 'docs'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyH').addEventListener('change', e => vis(['hours'], e.target.checked));
    document.getElementById('lyI').addEventListener('change', e => vis(['iso'], e.target.checked));
    document.getElementById('lyU').addEventListener('change', e => vis(['isoband'], e.target.checked));
    document.getElementById('lyR').addEventListener('change', () => setEra(era));
    document.getElementById('lyT').addEventListener('change', e => vis(['towns', 'tlbl'], e.target.checked));
    document.getElementById('lyD').addEventListener('change', e => vis(['docs'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'tlbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('.eras button').forEach((b, i) => b.addEventListener('click', () => { stop(); setEra(i); }));
    const play = document.getElementById('play');
    function stop() { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; } }
    play.addEventListener('click', () => { if (timer) { stop(); return; } play.textContent = 'Pause'; let k = era >= 4 ? -1 : era; timer = setInterval(() => { k += 1; if (k > 4) { stop(); return; } setEra(k); }, 1600); });
    const e0 = D.eras.indexOf(qs.get('era') || ''); setEra(e0 >= 0 ? e0 : 0);
  }
  function openTown(t) {
    if (!t) return;
    const docs = D.docs.filter(d => d.n === t.n);
    let extra = '';
    if (docs.length) {
      extra = '<div class="pl"><b>Documented journeys from London</b><table>' + docs.map(d => `<tr><td>${d.y}</td><td>${d.u === 'days' ? d.v + ' days' : hm(d.d)} by ${esc(d.m)}; model ${hm(d.l != null ? d.l : d.h)}<br><span class="nt" style="display:inline">${esc(d.s)}</span></td></tr>`).join('') + '</table></div>';
    }
    showPopup([t.lo, t.la], t.n, `${t.km} km from Charing Cross as the crow flies`, t.h, extra);
  }
  function go(t) {
    fold(true);
    map.flyTo({ center: [t.lo, t.la], zoom: small ? 7 : 7.5, duration: 1100, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.28 : 0.2))] });
    map.once('moveend', () => openTown(t));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.towns.map(t => ({ t: t.n, nn: norm(t.n), o: t }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 2 && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${it.o.km} km</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it.o); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const [n, ek] = a.dataset.go.split('|'); const t = D.towns.find(x => x.n === n); if (!t) return;
      if (ek) setEra(D.eras.indexOf(ek)); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go(t); }));
  }
  function loadLookup() {
    const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, 0, 0); LK = x.getImageData(0, 0, im.width, im.height).data; }; im.src = 'data/lookup.png';
  }
  const keyBands = document.getElementById('keyBands'); keyBands.innerHTML = BCOL.map(c => `<span style="background:${c}"></span>`).join('');
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d; loadLookup();
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-6.4, 50.0], [1.8, 56.2]], fitBoundsOptions: { padding: small ? { top: 10, bottom: 70, left: 10, right: 10 } : { top: 40, bottom: 80, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true, customAttribution: 'Model: Hotham 2026; turnpikes and coaches: Rosevear, Bogart, Shaw-Taylor, Satchell (openICPSR)' }, maxZoom: 13, minZoom: 4 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('town')) { const t = D.towns.find(x => norm(x.n) === norm(qs.get('town'))); if (t) go(t); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.tl,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
