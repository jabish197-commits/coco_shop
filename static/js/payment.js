(() => {
  const page = document.getElementById('payment-page');
  if (!page) return;
  const feedback = document.getElementById('payment-feedback');
  const note = document.getElementById('tracking-note');
  const form = document.getElementById('upi-form');
  let terminal = page.dataset.initial !== 'pending';
  let checking = false;
  let attempts = 0;
  async function check() {
    if (checking) return;
    checking = true;
    try {
      const response = await fetch(page.dataset.statusUrl, {cache: 'no-store', headers: {'Accept': 'application/json'}});
      if (!response.ok || response.redirected) throw new Error();
      const data = await response.json();
      document.getElementById('payment-label').textContent = data.label;
      terminal = data.status !== 'pending';
      note.textContent = data.status === 'paid' ? 'Payment verified. Thank you for your order!' : 'Status checked just now.';
      if (data.status === 'paid') document.getElementById('confirmation-label').textContent = 'Confirmed';
      if (terminal) document.getElementById('payment-actions')?.setAttribute('hidden', '');
    } catch (_) { note.textContent = 'Unable to check right now. Try again or sign in to view your order.'; }
    finally { checking = false; }
  }
  async function post(url, body) {
    const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json', 'X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value}, body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to start payment. Please try again later.');
    return data;
  }
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const button = document.getElementById('upi-pay');
    button.disabled = true;
    feedback.textContent = 'Opening secure checkout…';
    try {
      if (!window.Razorpay) throw new Error('Checkout could not load. Please refresh and check your connection.');
      const options = await post(page.dataset.startUrl, {});
      const checkout = new window.Razorpay({...options, theme:{color:'#593a29'},
        handler: async result => {
          feedback.textContent = 'Verifying your payment…';
          try {
            const verified = await post(page.dataset.verifyUrl, result);
            feedback.textContent = verified.status === 'paid' ? 'Payment confirmed.' : 'Waiting for payment confirmation. Please do not pay again.';
          } catch(error) { feedback.textContent = error.message; }
          await check();
          button.disabled = false;
        },
        modal:{ondismiss:() => {feedback.textContent = 'Checkout closed. Checking payment status…'; button.disabled = false; check();}}
      });
      checkout.on('payment.failed', () => {feedback.textContent = 'Payment was not completed. Check the status before trying again.'; button.disabled = false; check();});
      checkout.open();
    } catch(error) {feedback.textContent = error.message; button.disabled = false;}
  });
  document.getElementById('check-payment').addEventListener('click', check);
  async function poll() {
    if (terminal || attempts >= 120) return;
    if (!document.hidden) {attempts++; await check();}
    setTimeout(poll, 5000);
  }
  document.addEventListener('visibilitychange', () => {if (!document.hidden) check();});
  poll();
})();
