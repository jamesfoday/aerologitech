// Video modal controls (hardened: delegation + explicit button type)
(function(){
  const openBtn = document.getElementById('openVideoModal');
  const modalEl = document.getElementById('videoModal');
  const heroVideo = document.getElementById('heroVideo');
  const modalVideo = document.getElementById('modalVideo');

  function openModal(e){
    if (e) e.preventDefault();
    if (!modalEl) return;
    modalEl.classList.add('show');
    try { heroVideo && heroVideo.pause(); } catch(_) {}
    try { if (modalVideo && modalVideo.paused) modalVideo.play(); } catch(_) {}
  }

  function closeModal(e){
    if (e) e.preventDefault();
    if (!modalEl) return;
    modalEl.classList.remove('show');
    try { modalVideo && !modalVideo.paused && modalVideo.pause(); } catch(_) {}
    try { heroVideo && heroVideo.play(); } catch(_) {}
  }

  // Direct bindings
  openBtn && openBtn.addEventListener('click', openModal);

  // Delegate clicks for any element that has the close hook
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-video-modal-close]')) {
      closeModal(e);
    }
  });

  // Click outside dialog closes
  modalEl && modalEl.addEventListener('click', (e) => {
    if (e.target === modalEl) closeModal(e);
  });

  // ESC closes
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl && modalEl.classList.contains('show')) {
      closeModal(e);
    }
  });
})();
