// static/js/booking.js
(function () {
  const overlay = document.getElementById('bm-overlay');
  if (!overlay) return;

  const openHero  = document.getElementById('open-booking-hero');
  const openSide  = document.getElementById('open-booking-side');
  const closeBtn  = overlay.querySelector('.bm-close');
  const contBtn   = document.getElementById('bm-continue-step1');
  const step1 = document.getElementById('bm-step1');
  const step2 = document.getElementById('bm-step2');

  const fDate  = document.getElementById('bm-datetime');
  const fName  = document.getElementById('bm-name');
  const fEmail = document.getElementById('bm-email');
  const fPhone = document.getElementById('bm-phone');

  const rDate  = document.getElementById('bm-review-date');
  const rName  = document.getElementById('bm-review-name');
  const rEmail = document.getElementById('bm-review-email');
  const rPhone = document.getElementById('bm-review-phone');

  const openPickerBtn = document.getElementById('bm-open-picker');
  const clearBtn      = document.getElementById('bm-clear-datetime');

  const DATA = {
    type: overlay.dataset.objectType,    // 'service' or 'car'
    id:   overlay.dataset.objectId,
    action: overlay.dataset.action,      // '/orders/create/'
    ordersList: overlay.dataset.ordersListUrl
  };

  function getCookie(name) {
    const v = document.cookie.split(';').map(v => v.trim());
    for (const part of v) {
      if (part.startsWith(name + '=')) return decodeURIComponent(part.slice(name.length + 1));
    }
    return '';
  }
  const CSRF = getCookie('csrftoken');

  function open(){ overlay.hidden = false; document.body.style.overflow='hidden'; reset(); }
  function close(){ overlay.hidden = true; document.body.style.overflow=''; }
  function reset(){ step1.hidden=false; step2.hidden=true; contBtn.disabled=false; }

  function validStep1(){
    return fDate.value && fName.value.trim() && fEmail.value.trim() && fPhone.value.trim();
  }

  function toReview(){
    if(!validStep1()){
      [fDate,fName,fEmail,fPhone].forEach(el=>{
        if(!el.value) { el.classList.add('is-invalid'); setTimeout(()=>el.classList.remove('is-invalid'), 900); }
      });
      return;
    }
    const dt = new Date(fDate.value);
    rDate.textContent  = isNaN(dt) ? fDate.value : dt.toLocaleString();
    rName.textContent  = fName.value;
    rEmail.textContent = fEmail.value;
    rPhone.textContent = fPhone.value;
    step1.hidden = true; step2.hidden = false; contBtn.disabled = true;
  }

  async function createOrder(paymentLabel){
    if (!DATA.type || !DATA.id || !DATA.action) {
      alert("Missing booking context. Please refresh the page.");
      return;
    }
    const payload = {
      object_type: DATA.type,
      object_id: Number(DATA.id),
      when: fDate.value,
      name: fName.value.trim(),
      email: fEmail.value.trim(),
      phone: fPhone.value.trim(),
      payment: paymentLabel || ""
    };

    let resp;
    try {
      resp = await fetch(DATA.action, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF
        },
        body: JSON.stringify(payload),
        credentials: 'same-origin'
      });
    } catch (e) {
      alert("Network error. Please check your connection.");
      return;
    }

    if (!resp.ok) {
      // Try to show a server-provided error (useful when you saw the 400)
      try {
        const err = await resp.json();
        if (err && err.error) {
          alert(err.error);
          return;
        }
      } catch(_) {}
      alert("Sorry, we could not complete your booking. Please try again.");
      return;
    }

    const data = await resp.json();
    close();
    if (data.redirect) {
      window.location.href = data.redirect;
    } else {
      alert("Booked!");
    }
  }

  // UI hooks
  openHero?.addEventListener('click', e=>{ e.preventDefault(); open(); });
  openSide?.addEventListener('click', e=>{ e.preventDefault(); open(); });
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', e=>{ if(e.target === overlay) close(); });
  document.addEventListener('keydown', e=>{ if(!overlay.hidden && e.key==='Escape') close(); });

  contBtn.addEventListener('click', toReview);
  document.getElementById('bm-edit-date')?.addEventListener('click', ()=>{
    step2.hidden=true; step1.hidden=false; contBtn.disabled=false;
  });

  openPickerBtn?.addEventListener('click', ()=>{
    try { if (typeof fDate.showPicker === 'function') fDate.showPicker(); else { fDate.focus(); fDate.click?.(); } }
    catch { fDate.focus(); }
  });

  clearBtn?.addEventListener('click', ()=>{
    fDate.value = '';
    fDate.dispatchEvent(new Event('input', {bubbles:true}));
    fDate.dispatchEvent(new Event('change', {bubbles:true}));
  });

  document.getElementById('bm-pay-cash')?.addEventListener('click', ()=> createOrder('cash'));
  document.getElementById('bm-pay-paypal')?.addEventListener('click', ()=> createOrder('paypal'));
})();
