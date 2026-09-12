/* PHEAKTRA COFFEE Cafe POS & Management System - JavaScript Engine */
const CURRENCY = document.body.dataset.currency || '$';
const STORAGE_KEY = 'cafe-pos-cart';

const cartItemsEl = document.getElementById('cart-items');
const cartDataEl = document.getElementById('cart-data');
const cartSubtotalEl = document.getElementById('cart-subtotal');
const cartDiscountEl = document.getElementById('cart-discount');
const cartTaxEl = document.getElementById('cart-tax');
const cartTotalEl = document.getElementById('cart-total');
const discountInput = document.getElementById('order-discount');
const paidAmountInput = document.getElementById('paid-amount');
const changeDueEl = document.getElementById('change-due');
const posForm = document.getElementById('pos-form');
const clearCartBtn = document.getElementById('clear-cart');

const modalEl = document.getElementById('custom-modal');
const modalTitleEl = document.getElementById('modal-title');
const modalPriceEl = document.getElementById('modal-price');
const modalOptionsEl = document.getElementById('modal-options');
const modalNoteEl = document.getElementById('modal-note');
const modalQtyEl = document.getElementById('modal-qty');

let cart = [];
let modalProduct = null;
let modalQty = 1;

/* ------------------------------------------------------------------ Audio Synthesizer */
let _audioCtx = null;
function playUiChime(freq1 = 659.25, freq2 = 880.0, duration = 0.25) {
  try {
    if (!_audioCtx) {
      _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (_audioCtx.state === 'suspended') {
      _audioCtx.resume();
    }
    const now = _audioCtx.currentTime;
    const osc = _audioCtx.createOscillator();
    const gain = _audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq1, now);
    osc.frequency.setValueAtTime(freq2, now + 0.08);

    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    osc.connect(gain);
    gain.connect(_audioCtx.destination);

    osc.start(now);
    osc.stop(now + duration + 0.05);
  } catch (e) {
    // Audio context not allowed or unsupported
  }
}

/* ------------------------------------------------------------------ utils */
function money(value) {
  return CURRENCY + parseFloat(value || 0).toFixed(2);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text == null ? '' : String(text);
  return div.innerHTML;
}

function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function loadCart() {
  try {
    const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]');
    cart = Array.isArray(stored) ? stored : [];
  } catch (err) {
    cart = [];
  }
}

function saveCart() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
}

/* ------------------------------------------------------------------ Toast */
let _toastContainer = null;

function getToastContainer() {
  if (!_toastContainer) {
    _toastContainer = document.createElement('div');
    _toastContainer.className = 'toast-container';
    document.body.appendChild(_toastContainer);
  }
  return _toastContainer;
}

function showToast(message, type = 'warn', duration = 3500) {
  const iconMap = {
    success: 'fa-check-circle',
    error: 'fa-circle-exclamation',
    warn: 'fa-triangle-exclamation',
  };
  const container = getToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i class="fas ${iconMap[type] || 'fa-info-circle'}" aria-hidden="true"></i><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => toast.classList.add('show'));
  });

  setTimeout(() => dismissToast(toast), duration);
}

function dismissToast(toast) {
  toast.classList.remove('show');
  toast.addEventListener('transitionend', () => toast.remove(), { once: true });
}

/* ------------------------------------------------------------------- Cart & POS Calculations */
function renderCart() {
  if (!cartItemsEl) return;
  cartItemsEl.innerHTML = '';
  let subtotal = 0;
  let itemDiscounts = 0;

  if (cart.length === 0) {
    cartItemsEl.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:24px; color:var(--muted)">Cart is empty</td></tr>`;
  } else {
    cart.forEach((item, index) => {
      const itemTotal = item.unit_price * item.quantity - item.discount;
      subtotal += item.unit_price * item.quantity;
      itemDiscounts += item.discount;

      const row = document.createElement('tr');
      row.innerHTML = `
        <td>
          <strong style="font-size:0.95rem;">${escapeHtml(item.name)}</strong>
          ${item.options ? `<br><small class="muted item-options">${escapeHtml(item.options)}</small>` : ''}
        </td>
        <td>
          <div style="display:inline-flex; align-items:center; gap:4px;">
            <button type="button" class="button secondary small" data-action="dec" data-index="${index}" aria-label="Decrease quantity"><i class="fas fa-minus" style="font-size:0.75rem;"></i></button>
            <span class="qty-label" style="min-width:22px; text-align:center; font-weight:700;">${item.quantity}</span>
            <button type="button" class="button secondary small" data-action="inc" data-index="${index}" aria-label="Increase quantity"><i class="fas fa-plus" style="font-size:0.75rem;"></i></button>
          </div>
        </td>
        <td><strong style="color:var(--primary);">${money(itemTotal)}</strong></td>
        <td><button type="button" class="button danger small" data-action="remove" data-index="${index}" aria-label="Remove item"><i class="fas fa-xmark" aria-hidden="true"></i></button></td>
      `;
      cartItemsEl.appendChild(row);
    });
  }

  const orderDiscount = parseFloat(discountInput ? discountInput.value : 0) || 0;
  const totalDiscount = itemDiscounts + orderDiscount;
  const discountedSubtotal = Math.max(subtotal - totalDiscount, 0);

  // Check for tax rate if present
  let taxAmount = 0;
  const taxRate = parseFloat(document.body.dataset.taxRate || 0) || 0;
  if (taxRate > 0) {
    taxAmount = parseFloat((discountedSubtotal * (taxRate / 100.0)).toFixed(2));
    if (cartTaxEl) cartTaxEl.textContent = money(taxAmount);
  }

  const grandTotal = Math.max(discountedSubtotal + taxAmount, 0);

  if (cartSubtotalEl) cartSubtotalEl.textContent = money(subtotal);
  if (cartDiscountEl) cartDiscountEl.textContent = money(totalDiscount);
  if (cartTotalEl) cartTotalEl.textContent = money(grandTotal);
  
  updateChange(grandTotal);
  updateMobileCartBar(grandTotal, cart.reduce((sum, item) => sum + item.quantity, 0));
  if (cartDataEl) cartDataEl.value = JSON.stringify(cart);
  saveCart();
}

function updateMobileCartBar(total, count) {
  const bar = document.getElementById('pos-mobile-cart-bar');
  const barQty = document.getElementById('mobile-bar-qty');
  const barTotal = document.getElementById('mobile-bar-total');
  const mobileCartBadge = document.getElementById('mobile-cart-badge');

  const totalCount = count != null ? count : cart.reduce((sum, item) => sum + item.quantity, 0);
  const totalAmt = total != null ? total : (cartTotalEl ? parseFloat(cartTotalEl.textContent.replace(CURRENCY, '').replace(/,/g, '')) || 0 : 0);

  if (mobileCartBadge) {
    mobileCartBadge.textContent = totalCount;
  }

  if (!bar) return;

  if (totalCount > 0 && window.innerWidth <= 1024) {
    const leftPane = document.getElementById('pos-left-pane');
    if (leftPane && !leftPane.classList.contains('pos-hidden-mobile')) {
      bar.style.display = 'flex';
    } else {
      bar.style.display = 'none';
    }
    if (barQty) barQty.textContent = `${totalCount} item${totalCount > 1 ? 's' : ''}`;
    if (barTotal) barTotal.textContent = money(totalAmt);
  } else {
    bar.style.display = 'none';
  }
}

function setupPosMobileTabs() {
  const tabCatalog = document.getElementById('pos-tab-catalog');
  const tabCart = document.getElementById('pos-tab-cart');
  const leftPane = document.getElementById('pos-left-pane');
  const rightPane = document.getElementById('pos-right-pane');
  const backBtn = document.getElementById('pos-back-catalog-btn');
  const barPayBtn = document.getElementById('pos-mobile-bar-pay-btn');

  if (!tabCatalog || !tabCart || !leftPane || !rightPane) return;

  function showCatalog() {
    tabCatalog.classList.add('active');
    tabCart.classList.remove('active');
    leftPane.classList.remove('pos-hidden-mobile');
    rightPane.classList.add('pos-hidden-mobile');
    updateMobileCartBar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function showCart() {
    tabCart.classList.add('active');
    tabCatalog.classList.remove('active');
    rightPane.classList.remove('pos-hidden-mobile');
    leftPane.classList.add('pos-hidden-mobile');
    const bar = document.getElementById('pos-mobile-cart-bar');
    if (bar) bar.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  tabCatalog.addEventListener('click', showCatalog);
  tabCart.addEventListener('click', showCart);
  if (backBtn) backBtn.addEventListener('click', showCatalog);
  if (barPayBtn) barPayBtn.addEventListener('click', showCart);

  // Initial state on mobile / tablet
  if (window.innerWidth <= 1024) {
    rightPane.classList.add('pos-hidden-mobile');
  }

  window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) {
      leftPane.classList.remove('pos-hidden-mobile');
      rightPane.classList.remove('pos-hidden-mobile');
      const bar = document.getElementById('pos-mobile-cart-bar');
      if (bar) bar.style.display = 'none';
    } else {
      if (tabCatalog.classList.contains('active')) {
        rightPane.classList.add('pos-hidden-mobile');
        leftPane.classList.remove('pos-hidden-mobile');
      } else {
        leftPane.classList.add('pos-hidden-mobile');
        rightPane.classList.remove('pos-hidden-mobile');
      }
      updateMobileCartBar();
    }
  });
}

function updateChange(totalOverride) {
  if (!changeDueEl) return;
  const totalText = cartTotalEl ? cartTotalEl.textContent.replace(CURRENCY, '').replace(/,/g, '') : '0';
  const total = totalOverride != null ? totalOverride : parseFloat(totalText) || 0;
  const paid = parseFloat(paidAmountInput ? paidAmountInput.value : 0) || 0;
  const change = Math.max(paid - total, 0);
  changeDueEl.textContent = money(change);
  changeDueEl.style.color = paid >= total && total > 0 ? 'var(--success)' : 'var(--muted)';
}

window.changeQty = function (index, delta) {
  const item = cart[index];
  if (!item) return;
  const max = item.max_stock || 999;
  const next = Math.min(Math.max(1, item.quantity + delta), max);
  if (next === item.quantity && delta > 0) {
    showToast(`Only ${max} units available in stock.`, 'warn');
    return;
  }
  item.quantity = next;
  playUiChime(523.25, 659.25, 0.1);
  renderCart();
};

window.removeItem = function (index) {
  cart.splice(index, 1);
  renderCart();
};

if (cartItemsEl) {
  cartItemsEl.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const index = parseInt(button.dataset.index, 10);
    const action = button.dataset.action;
    if (action === 'inc') window.changeQty(index, 1);
    else if (action === 'dec') window.changeQty(index, -1);
    else if (action === 'remove') window.removeItem(index);
  });
}

if (clearCartBtn) {
  clearCartBtn.addEventListener('click', () => {
    if (!cart.length) return;
    if (window.confirm('Clear all items from the current order?')) {
      cart = [];
      if (discountInput) discountInput.value = 0;
      if (paidAmountInput) paidAmountInput.value = 0;
      renderCart();
    }
  });
}

/* ---------------------------------------------------- Customization Modal */
function openModal(product) {
  if (!modalEl) return;
  modalProduct = product;
  modalQty = 1;
  if (modalQtyEl) modalQtyEl.textContent = '1';
  if (modalTitleEl) modalTitleEl.textContent = product.name;
  if (modalPriceEl) modalPriceEl.textContent = `${money(parseFloat(product.price))} &bull; ${product.stock} in stock`;

  if (modalOptionsEl) {
    modalOptionsEl.innerHTML = '';
    const tags = (product.tags || '')
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);
    tags.forEach((tag) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'option-chip';
      chip.textContent = tag;
      chip.addEventListener('click', () => chip.classList.toggle('selected'));
      modalOptionsEl.appendChild(chip);
    });
  }
  if (modalNoteEl) modalNoteEl.value = '';

  modalEl.hidden = false;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => modalEl.classList.add('is-open'));
  });
}

function closeModal() {
  if (!modalEl) return;
  modalEl.classList.remove('is-open');
  modalEl.addEventListener(
    'transitionend',
    () => {
      if (!modalEl.classList.contains('is-open')) {
        modalEl.hidden = true;
      }
    },
    { once: true }
  );
  modalProduct = null;
}

function addModalItemToCart() {
  if (!modalProduct) return;
  const stock = parseInt(modalProduct.stock, 10) || 1;
  if (modalQty > stock) {
    showToast(`Only ${stock} in stock for this product.`, 'error');
    return;
  }
  const selected = Array.from(
    modalOptionsEl ? modalOptionsEl.querySelectorAll('.option-chip.selected') : []
  ).map((chip) => chip.textContent);
  const note = modalNoteEl ? modalNoteEl.value.trim() : '';
  const options = [selected.join(', '), note].filter(Boolean).join('; ');

  const existing = cart.find(
    (item) => item.product_id === modalProduct.id && item.options === options
  );
  if (existing) {
    if (existing.quantity + modalQty > stock) {
      showToast(`Only ${stock} units available in stock.`, 'error');
      return;
    }
    existing.quantity += modalQty;
  } else {
    cart.push({
      product_id: modalProduct.id,
      name: modalProduct.name,
      quantity: modalQty,
      unit_price: parseFloat(modalProduct.price),
      discount: 0,
      options,
      max_stock: stock,
    });
  }
  closeModal();
  renderCart();
  triggerCartBadgeBounce();
  playUiChime(587.33, 880.0, 0.2);
  showToast(`${modalProduct.name} added to cart.`, 'success', 2000);
}

document.querySelectorAll('.add-product').forEach((button) => {
  button.addEventListener('click', () => {
    try {
      openModal(JSON.parse(button.dataset.product));
    } catch (err) {
      console.error('Invalid product payload', err);
    }
  });
});

if (modalEl) {
  const cancelBtn = document.getElementById('modal-cancel');
  const addBtn = document.getElementById('modal-add');
  const minusBtn = document.getElementById('modal-qty-minus');
  const plusBtn = document.getElementById('modal-qty-plus');

  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
  if (addBtn) addBtn.addEventListener('click', addModalItemToCart);
  if (minusBtn) {
    minusBtn.addEventListener('click', () => {
      modalQty = Math.max(1, modalQty - 1);
      if (modalQtyEl) modalQtyEl.textContent = String(modalQty);
    });
  }
  if (plusBtn) {
    plusBtn.addEventListener('click', () => {
      const stock = parseInt(modalProduct ? modalProduct.stock : 999, 10) || 999;
      if (modalQty >= stock) {
        showToast(`Only ${stock} units available in stock.`, 'warn');
        return;
      }
      modalQty += 1;
      if (modalQtyEl) modalQtyEl.textContent = String(modalQty);
    });
  }

  modalEl.addEventListener('click', (event) => {
    if (event.target === modalEl) closeModal();
  });
}

/* ---------------------------------------------------- Category & Live Search */
function setupCategoryFilter() {
  document.querySelectorAll('.category-button').forEach((button) => {
    button.addEventListener('click', () => {
      const category = button.dataset.category;
      document
        .querySelectorAll('.category-button')
        .forEach((other) => other.classList.remove('active'));
      button.classList.add('active');
      filterProducts();
    });
  });

  const posSearchInput = document.getElementById('pos-search');
  if (posSearchInput) {
    posSearchInput.addEventListener('input', debounce(filterProducts, 120));
  }
}

function filterProducts() {
  const activeCategoryBtn = document.querySelector('.category-button.active');
  const category = activeCategoryBtn ? activeCategoryBtn.dataset.category : 'all';
  const posSearchInput = document.getElementById('pos-search');
  const searchTerm = posSearchInput ? posSearchInput.value.toLowerCase().trim() : '';

  document.querySelectorAll('.product-card').forEach((card) => {
    const cardCategory = card.dataset.category;
    const cardName = card.querySelector('strong') ? card.querySelector('strong').textContent.toLowerCase() : '';
    const cardTags = card.dataset.tags ? card.dataset.tags.toLowerCase() : '';
    
    const categoryMatch = category === 'all' || cardCategory === category;
    const searchMatch = !searchTerm || cardName.includes(searchTerm) || cardTags.includes(searchTerm);

    card.style.display = categoryMatch && searchMatch ? '' : 'none';
  });
}

/* ---------------------------------------------------- Quick Cash Presets & Discounts */
function setupPosQuickActions() {
  // Quick cash buttons
  document.querySelectorAll('.cash-preset-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const amountAttr = btn.dataset.amount;
      if (amountAttr === 'exact') {
        const totalText = cartTotalEl ? cartTotalEl.textContent.replace(CURRENCY, '').replace(/,/g, '') : '0';
        if (paidAmountInput) paidAmountInput.value = parseFloat(totalText) || 0;
      } else {
        const amt = parseFloat(amountAttr) || 0;
        if (paidAmountInput) paidAmountInput.value = amt;
      }
      playUiChime(523.25, 783.99, 0.15);
      updateChange();
    });
  });

  // Quick discount buttons
  document.querySelectorAll('.discount-preset-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const pct = parseFloat(btn.dataset.pct) || 0;
      const subtotalText = cartSubtotalEl ? cartSubtotalEl.textContent.replace(CURRENCY, '').replace(/,/g, '') : '0';
      const subtotal = parseFloat(subtotalText) || 0;
      
      document.querySelectorAll('.discount-preset-btn').forEach((b) => b.classList.remove('active'));
      if (pct > 0) {
        btn.classList.add('active');
        const disc = parseFloat((subtotal * (pct / 100)).toFixed(2));
        if (discountInput) discountInput.value = disc;
      } else {
        if (discountInput) discountInput.value = 0;
      }
      renderCart();
    });
  });

  // Order type buttons
  document.querySelectorAll('.order-type-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.order-type-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const orderType = btn.dataset.type;
      const orderTypeVal = document.getElementById('order-type-val');
      if (orderTypeVal) orderTypeVal.value = orderType;

      const tableGroup = document.getElementById('pos-table-group');
      if (tableGroup) {
        tableGroup.style.display = orderType === 'Dine-In' ? '' : 'none';
      }
    });
  });

  // Table select change
  const tableSelect = document.getElementById('pos-table-select');
  if (tableSelect) {
    tableSelect.addEventListener('change', () => {
      const tableIdVal = document.getElementById('table-id-val');
      if (tableIdVal) tableIdVal.value = tableSelect.value;
    });
  }

  // Customer selection & loyalty points lookup
  const custSelect = document.getElementById('pos-customer-select');
  const loyaltyBar = document.getElementById('pos-loyalty-bar');
  const custTier = document.getElementById('pos-cust-tier');
  const custPoints = document.getElementById('pos-cust-points');
  const custIdVal = document.getElementById('customer-id-val');
  const redeemBtn = document.getElementById('pos-redeem-pts-btn');
  const pointsRedeemedVal = document.getElementById('points-redeemed-val');

  if (custSelect) {
    custSelect.addEventListener('change', async () => {
      const custId = custSelect.value;
      if (custIdVal) custIdVal.value = custId;
      if (!custId) {
        if (loyaltyBar) loyaltyBar.style.display = 'none';
        if (pointsRedeemedVal) pointsRedeemedVal.value = '0';
        return;
      }

      try {
        const res = await fetch(`/api/customers/${custId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.found && loyaltyBar) {
            loyaltyBar.style.display = 'flex';
            if (custTier) custTier.textContent = `${data.tier} Member`;
            if (custPoints) custPoints.textContent = `${data.points} pts ($${(data.points / 20).toFixed(2)})`;
            
            if (redeemBtn) {
              redeemBtn.disabled = data.points < 20;
              redeemBtn.onclick = () => {
                const maxRedeem = Math.min(data.points, 200); // redeem up to 200 pts ($10)
                const ptsDiscount = parseFloat((maxRedeem / 20.0).toFixed(2));
                if (discountInput) discountInput.value = ptsDiscount;
                if (pointsRedeemedVal) pointsRedeemedVal.value = String(maxRedeem);
                showToast(`Applied ${maxRedeem} loyalty points discount (-$${ptsDiscount.toFixed(2)})`, 'success');
                renderCart();
              };
            }
          }
        }
      } catch (e) {
        console.warn('Customer lookup error', e);
      }
    });
  }

  // Quick Customer Modal
  const qcModal = document.getElementById('quick-customer-modal');
  const openQcBtn = document.getElementById('open-quick-customer');
  const closeQcBtn = document.getElementById('quick-cust-close');
  const cancelQcBtn = document.getElementById('qc-cancel');
  const qcForm = document.getElementById('quick-customer-form');

  if (openQcBtn && qcModal) {
    openQcBtn.addEventListener('click', () => {
      qcModal.hidden = false;
      requestAnimationFrame(() => qcModal.classList.add('is-open'));
    });
  }
  function closeQcModal() {
    if (!qcModal) return;
    qcModal.classList.remove('is-open');
    qcModal.addEventListener('transitionend', () => { if (!qcModal.classList.contains('is-open')) qcModal.hidden = true; }, { once: true });
  }
  if (closeQcBtn) closeQcBtn.addEventListener('click', closeQcModal);
  if (cancelQcBtn) cancelQcBtn.addEventListener('click', closeQcModal);

  if (qcForm) {
    qcForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('qc-name').value.trim();
      const phone = document.getElementById('qc-phone').value.trim();
      const email = document.getElementById('qc-email').value.trim();
      if (!name) return;

      try {
        const res = await fetch('/api/customers/quick-create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, phone, email })
        });
        if (res.ok) {
          const data = await res.json();
          if (data.success && custSelect) {
            const opt = document.createElement('option');
            opt.value = data.customer.id;
            opt.textContent = `${data.customer.name} (${data.customer.phone || 'No phone'})`;
            opt.selected = true;
            custSelect.appendChild(opt);
            custSelect.dispatchEvent(new Event('change'));
            closeQcModal();
            qcForm.reset();
            showToast(`Customer ${data.customer.name} created and selected.`, 'success');
          }
        }
      } catch (err) {
        showToast('Failed to save customer', 'error');
      }
    });
  }
}

/* ---------------------------------------------------- Keyboard Shortcuts */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // F2: Focus POS search
    if (e.key === 'F2') {
      e.preventDefault();
      const posSearch = document.getElementById('pos-search');
      if (posSearch) posSearch.focus();
    }
    // F4: Clear cart
    if (e.key === 'F4') {
      e.preventDefault();
      if (clearCartBtn) clearCartBtn.click();
    }
    // Escape: Close modals
    if (e.key === 'Escape') {
      if (modalEl && !modalEl.hidden) closeModal();
      const qcModal = document.getElementById('quick-customer-modal');
      if (qcModal && !qcModal.hidden) qcModal.hidden = true;
    }
  });
}

/* ---------------------------------------------------- Live Order Tracking Auto-polling */
function setupLiveOrderTracking() {
  const trackCard = document.querySelector('.public-landing .status-line');
  if (!trackCard) return;

  const orderNumEl = document.querySelector('.public-landing h3');
  const orderNum = orderNumEl ? orderNumEl.textContent.trim() : '';
  if (!orderNum) return;

  const steps = ['Pending', 'Preparing', 'Ready', 'Completed'];
  let currentStatus = '';

  async function pollStatus() {
    try {
      const res = await fetch(`/api/orders/${encodeURIComponent(orderNum)}/status`);
      if (!res.ok) return;
      const data = await res.json();
      if (!data.found) return;

      const newStatus = data.order_status || data.status;
      if (newStatus !== currentStatus) {
        currentStatus = newStatus;
        updateTrackingUI(newStatus);
        if (newStatus === 'Ready' || newStatus === 'Completed') {
          playUiChime(587.33, 1174.66, 0.4);
          showToast(`Your order is ${newStatus}!`, 'success', 5000);
        }
      }
    } catch (e) {
      console.warn('Tracking poll error', e);
    }
  }

  function updateTrackingUI(status) {
    const badge = document.querySelector('.public-landing .badge');
    if (badge) {
      badge.textContent = status;
      badge.className = `badge ${status === 'Completed' || status === 'Ready' ? 'badge-ok' : 'badge-paid'}`;
    }

    const stepEls = document.querySelectorAll('.status-step');
    const targetIdx = steps.indexOf(status);
    stepEls.forEach((el, idx) => {
      if (idx <= targetIdx && targetIdx !== -1) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });
  }

  // Poll every 4 seconds on tracking screen
  setInterval(pollStatus, 4000);
}

/* ---------------------------------------------------- Mobile Navigation */
function setupMobileNav() {
  const publicToggle = document.getElementById('public-menu-toggle');
  const publicLinks = document.getElementById('public-links');
  if (publicToggle && publicLinks) {
    publicToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      publicLinks.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
      if (!publicToggle.contains(e.target) && !publicLinks.contains(e.target)) {
        publicLinks.classList.remove('open');
      }
    });
  }

  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarCloseBtn = document.getElementById('sidebar-close-btn');

  if (sidebar) {
    // Create backdrop overlay for mobile sidebar if not present
    let sidebarBackdrop = document.querySelector('.sidebar-backdrop');
    if (!sidebarBackdrop) {
      sidebarBackdrop = document.createElement('div');
      sidebarBackdrop.className = 'sidebar-backdrop';
      sidebar.parentNode.insertBefore(sidebarBackdrop, sidebar.nextSibling);
    }

    function openSidebar() {
      sidebar.classList.add('open');
      sidebarBackdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
      sidebar.classList.remove('open');
      sidebarBackdrop.classList.remove('active');
      document.body.style.overflow = '';
    }

    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (sidebar.classList.contains('open')) {
          closeSidebar();
        } else {
          openSidebar();
        }
      });
    }

    if (sidebarCloseBtn) {
      sidebarCloseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeSidebar();
      });
    }

    sidebarBackdrop.addEventListener('click', closeSidebar);

    document.addEventListener('click', (e) => {
      if (
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        (!sidebarToggle || !sidebarToggle.contains(e.target)) &&
        !sidebarBackdrop.contains(e.target)
      ) {
        closeSidebar();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) {
        closeSidebar();
      }
    });
  }
}

/* ------------------------------------------------------------------ Forms */
if (posForm) {
  let _posSubmitting = false;
  posForm.addEventListener('submit', (event) => {
    if (!cart.length) {
      event.preventDefault();
      showToast('Please add at least one product to the cart before checking out.', 'error');
    } else if (_posSubmitting) {
      event.preventDefault();
    } else {
      if (cartDataEl) cartDataEl.value = JSON.stringify(cart);
      _posSubmitting = true;
      const btn = document.getElementById('pos-submit-btn') || posForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing Payment...';
      }
    }
  });
}

if (discountInput) discountInput.addEventListener('input', renderCart);
if (paidAmountInput) paidAmountInput.addEventListener('input', () => updateChange());

// Auto dismiss server-side flashed toasts after 5 seconds
setTimeout(() => {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-6px)';
    setTimeout(() => alert.remove(), 400);
  });
}, 5000);

/* ----------------------------------------------------------- Ripple Effect */
function initRippleEffect() {
  document.addEventListener('click', (e) => {
    const target = e.target.closest('.button, .category-button, .menu-item, .hero-floating-card');
    if (!target) return;

    const rect = target.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 1.6;
    const wave = document.createElement('span');
    wave.className = 'ripple-wave';
    wave.style.width = wave.style.height = `${size}px`;
    wave.style.left = `${e.clientX - rect.left - size / 2}px`;
    wave.style.top = `${e.clientY - rect.top - size / 2}px`;

    target.appendChild(wave);
    wave.addEventListener('animationend', () => wave.remove(), { once: true });
  });
}

/* ------------------------------------------------- Page Transition Loader */
function initPageLoader() {
  const loader = document.getElementById('page-loader');
  if (!loader) return;
  loader.style.width = '65%';
  window.addEventListener('load', () => {
    loader.style.width = '100%';
    setTimeout(() => {
      loader.style.opacity = '0';
      setTimeout(() => {
        loader.style.width = '0%';
      }, 350);
    }, 180);
  });
  if (document.readyState === 'complete') {
    loader.style.width = '100%';
    setTimeout(() => {
      loader.style.opacity = '0';
    }, 180);
  }
}

/* --------------------------------------------------- Counter Animation */
function initCounterAnimation() {
  const counters = document.querySelectorAll('.stat-counter');
  counters.forEach((el) => {
    const rawTarget = el.dataset.target || el.textContent.replace(/[^0-9.-]+/g, '');
    const target = parseFloat(rawTarget);
    if (isNaN(target)) return;

    const prefix = el.dataset.prefix || (el.textContent.includes(CURRENCY) ? CURRENCY : '');
    const suffix = el.dataset.suffix || '';
    const decimals = parseInt(el.dataset.decimals != null ? el.dataset.decimals : (target % 1 !== 0 ? 2 : 0), 10);
    const duration = 1100;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = target * ease;
      const formatted = current.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
      el.textContent = `${prefix}${formatted}${suffix}`;
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        const finalFormatted = target.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
        el.textContent = `${prefix}${finalFormatted}${suffix}`;
      }
    }
    requestAnimationFrame(update);
  });
}

/* ---------------------------------------------------- Cart Badge Bounce */
function triggerCartBadgeBounce() {
  const badges = document.querySelectorAll('.cart-badge, .mobile-cart-count');
  badges.forEach((b) => {
    b.classList.remove('bounce', 'cart-badge-bounce');
    void b.offsetWidth;
    b.classList.add('cart-badge-bounce');
  });
}

/* ----------------------------------------------------------- Scroll Reveal Observer */
function initScrollReveal() {
  const reveals = document.querySelectorAll('.scroll-reveal');
  if (!reveals.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );

  reveals.forEach((el) => observer.observe(el));
}

/* ----------------------------------------------------------- Smooth Number Ticker */
function initSmoothTicker() {
  const tickers = document.querySelectorAll('[data-ticker]');
  tickers.forEach((el) => {
    const target = parseFloat(el.dataset.ticker);
    if (isNaN(target)) return;
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    const duration = 1000;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(2, -10 * progress);
      const current = target * ease;
      el.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`;
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
    }
    requestAnimationFrame(tick);
  });
}

/* ---------------------------------------------------- Login Page Helpers */
function setupLoginHelpers() {
  const chips = document.querySelectorAll('.login-quick-chip');
  const userInp = document.getElementById('login-username');
  const pwInp = document.getElementById('login-password');
  const toggleBtn = document.getElementById('toggle-pw-btn');

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const u = chip.dataset.user;
      const p = chip.dataset.pw;
      if (userInp) userInp.value = u;
      if (pwInp) pwInp.value = p;
      playUiChime(659.25, 880.0, 0.15);
      showToast(`Filled credentials for ${u}`, 'success', 2000);
    });
  });

  if (toggleBtn && pwInp) {
    toggleBtn.addEventListener('click', () => {
      if (pwInp.type === 'password') {
        pwInp.type = 'text';
        toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide';
      } else {
        pwInp.type = 'password';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i> Show';
      }
    });
  }
}

/* ------------------------------------------------------------------- Boot */
loadCart();
setupCategoryFilter();
setupPosQuickActions();
setupPosMobileTabs();
setupKeyboardShortcuts();
setupLiveOrderTracking();
setupMobileNav();
setupLoginHelpers();
initRippleEffect();
initPageLoader();
initCounterAnimation();
initScrollReveal();
initSmoothTicker();

cart = cart.filter((item) => !item.max_stock || item.quantity <= item.max_stock);
renderCart();


