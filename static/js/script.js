// ===== Sticky nav background on scroll =====
const nav = document.getElementById('nav');
const updateNav = () => {
    if (window.scrollY > 40) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
};
window.addEventListener('scroll', updateNav, { passive: true });
updateNav();

// ===== Mobile hamburger menu =====
const navToggle   = document.getElementById('navToggle');
const navLinks    = document.getElementById('navLinks');
const navBackdrop = document.getElementById('navBackdrop');
if (navToggle && navLinks) {
    const setOpen = (open) => {
        document.body.classList.toggle('menu-open', open);
        navToggle.setAttribute('aria-expanded', String(open));
    };
    navToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        setOpen(!document.body.classList.contains('menu-open'));
    });
    navLinks.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => setOpen(false));
    });
    if (navBackdrop) {
        navBackdrop.addEventListener('click', () => setOpen(false));
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') setOpen(false);
    });
    window.addEventListener('resize', () => {
        if (window.innerWidth > 760) setOpen(false);
    });
}

// ===== Reveal-on-scroll =====
const revealEls = document.querySelectorAll('.section, .card, .gallery-item, .stat');
const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            io.unobserve(entry.target);
        }
    });
}, { threshold: 0.12 });
revealEls.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity .7s ease, transform .7s ease';
    io.observe(el);
});

// ===== Animated stat counters =====
const statEls = document.querySelectorAll('[data-stat]');
const statIO = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const num = entry.target.querySelector('.stat-num');
        const target = parseFloat(num.dataset.target);
        const decimals = parseInt(num.dataset.decimals || '0');
        const suffix = num.dataset.suffix || '';
        const duration = 1600;
        const start = performance.now();
        const ease = (t) => 1 - Math.pow(1 - t, 3);
        const tick = (now) => {
            const t = Math.min(1, (now - start) / duration);
            const v = target * ease(t);
            num.textContent = v.toFixed(decimals).toLocaleString
                ? Number(v.toFixed(decimals)).toLocaleString('en-IN') + suffix
                : v.toFixed(decimals) + suffix;
            if (t < 1) requestAnimationFrame(tick);
            else num.textContent = Number(target.toFixed(decimals)).toLocaleString('en-IN') + suffix;
        };
        requestAnimationFrame(tick);
        statIO.unobserve(entry.target);
    });
}, { threshold: 0.4 });
statEls.forEach(el => statIO.observe(el));

// ===== 3D mouse-tilt on amenity cards =====
const tilts = document.querySelectorAll('.card.tilt');
tilts.forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        const x = e.clientX - r.left;
        const y = e.clientY - r.top;
        const rx = ((y / r.height) - 0.5) * -8;
        const ry = ((x / r.width)  - 0.5) * 10;
        card.style.transform = `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-6px)`;
        card.style.setProperty('--mx', `${x}px`);
        card.style.setProperty('--my', `${y}px`);
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
    });
});

// ===== Live price calculator =====
const peopleInput = document.querySelector('input[name="people"]');
const peoplePill  = document.getElementById('peoplePill');
const priceTotal  = document.getElementById('priceTotal');

function updatePrice() {
    if (!peopleInput || !priceTotal) return;
    const n = Math.max(1, Math.min(100, parseInt(peopleInput.value) || 0));
    const total = n * 200;
    peoplePill.textContent = n;
    priceTotal.textContent = '₹' + total.toLocaleString('en-IN');
    priceTotal.parentElement.classList.remove('bump');
    void priceTotal.parentElement.offsetWidth;
    priceTotal.parentElement.classList.add('bump');
}
if (peopleInput) {
    peopleInput.addEventListener('input', updatePrice);
    updatePrice();
}

// ===== Back-to-top button =====
const backTop = document.getElementById('backTop');
const updateBackTop = () => {
    if (window.scrollY > 600) backTop.classList.add('visible');
    else backTop.classList.remove('visible');
};
window.addEventListener('scroll', updateBackTop, { passive: true });
backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ===== Confetti (used on successful submit) =====
const confettiCanvas = document.getElementById('confettiCanvas');
const cctx = confettiCanvas.getContext('2d');
let confettiPieces = [];
let confettiActive = false;

function resizeCanvas() {
    confettiCanvas.width  = window.innerWidth;
    confettiCanvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

function fireConfetti() {
    const colors = ['#06b6d4', '#22d3ee', '#67e8f9', '#fbbf24', '#ffffff', '#a5f3fc'];
    confettiPieces = [];
    for (let i = 0; i < 160; i++) {
        confettiPieces.push({
            x: window.innerWidth / 2 + (Math.random() - 0.5) * 200,
            y: window.innerHeight * 0.4,
            vx: (Math.random() - 0.5) * 12,
            vy: -Math.random() * 14 - 4,
            g: 0.35 + Math.random() * 0.15,
            r: 4 + Math.random() * 6,
            color: colors[Math.floor(Math.random() * colors.length)],
            rot: Math.random() * Math.PI,
            vr: (Math.random() - 0.5) * 0.3,
            life: 0
        });
    }
    if (!confettiActive) { confettiActive = true; requestAnimationFrame(animateConfetti); }
}

function animateConfetti() {
    cctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
    confettiPieces.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.g;
        p.rot += p.vr;
        p.life++;
        cctx.save();
        cctx.translate(p.x, p.y);
        cctx.rotate(p.rot);
        cctx.fillStyle = p.color;
        cctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 0.5);
        cctx.restore();
    });
    confettiPieces = confettiPieces.filter(p => p.y < confettiCanvas.height + 20 && p.life < 220);
    if (confettiPieces.length > 0) requestAnimationFrame(animateConfetti);
    else { cctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height); confettiActive = false; }
}

// ===== Reservation form submit =====
const form = document.getElementById('reserveForm');
const msg  = document.getElementById('formMsg');

async function verifyPayment(response, msg) {
    try {
        const verify = await fetch('/reserve/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_order_id:   response.razorpay_order_id,
                razorpay_signature:  response.razorpay_signature,
            }),
        });
        const v = await verify.json();
        if (verify.ok && v.ok) {
            msg.textContent = v.message || 'Payment successful! Reservation confirmed.';
            msg.classList.remove('error');
            msg.classList.add('success');
            fireConfetti();
            form.reset();
            updatePrice();
        } else {
            msg.textContent = v.error || 'Payment received but verification failed. Please contact us.';
            msg.classList.add('error');
        }
    } catch (err) {
        msg.textContent = 'Payment verification network error. Please contact us with your payment ID.';
        msg.classList.add('error');
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    msg.textContent = '';
    msg.className = 'form-msg';

    const data = Object.fromEntries(new FormData(form).entries());

    if (!data.email.includes('@')) {
        msg.textContent = 'Please enter a valid email address.';
        msg.classList.add('error');
        return;
    }
    if (typeof Razorpay === 'undefined') {
        msg.textContent = 'Payment service unavailable. Check your internet and try again.';
        msg.classList.add('error');
        return;
    }

    form.classList.add('loading');
    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;

    try {
        const res = await fetch('/reserve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const out = await res.json();
        if (!res.ok || !out.ok) {
            msg.textContent = out.error || 'Could not start payment. Please try again.';
            msg.classList.add('error');
            return;
        }

        const options = {
            key:         out.key_id,
            amount:      out.amount,
            currency:    out.currency,
            name:        out.name,
            description: out.description,
            order_id:    out.order_id,
            prefill:     out.prefill,
            theme:       { color: '#06b6d4' },
            handler:     (response) => verifyPayment(response, msg),
            modal: {
                ondismiss: () => {
                    msg.textContent = 'Payment cancelled. Submit again when you are ready.';
                    msg.classList.add('error');
                },
            },
        };

        const rzp = new Razorpay(options);
        rzp.on('payment.failed', (resp) => {
            const desc = (resp && resp.error && resp.error.description) || 'unknown error';
            msg.textContent = 'Payment failed: ' + desc;
            msg.classList.add('error');
        });
        rzp.open();
    } catch (err) {
        msg.textContent = 'Network error. Please check your connection and try again.';
        msg.classList.add('error');
    } finally {
        form.classList.remove('loading');
        btn.disabled = false;
    }
});
