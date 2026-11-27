// Site-wide UI helpers (drawer is handled by navbar.html's own script)
document.addEventListener("DOMContentLoaded", function () {
  /* ---------- Password visibility toggle ---------- */
  document.querySelectorAll("[data-pw-toggle]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const field = btn.previousElementSibling;
      if (field) {
        field.type = field.type === "password" ? "text" : "password";
      }
    });
  });

  /* ---------- Password strength meter (register) ---------- */
  const pwField = document.querySelector("[data-pw-strength]");
  if (pwField) {
    const bars = [1, 2, 3, 4]
      .map((n) => document.getElementById(`pw-bar-${n}`))
      .filter(Boolean);
    const label = document.getElementById("pw-label");
    const colors = {
      weak: "#f87171",
      okay: "#facc15",
      good: "#4ade80",
      strong: "var(--color-accent, #4ade80)",
    };

    pwField.addEventListener("input", () => {
      const value = pwField.value;
      bars.forEach((b) => {
        if (b) b.style.backgroundColor = "";
      });
      if (!value) {
        if (label) label.textContent = "\u00A0";
        return;
      }
      let score = 0;
      if (value.length >= 8) score++;
      if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
      if (/\d/.test(value)) score++;
      if (/[^A-Za-z0-9]/.test(value)) score++;

      const levels = [
        { key: "weak", text: "Weak" },
        { key: "okay", text: "Okay" },
        { key: "good", text: "Good" },
        { key: "strong", text: "Strong" },
      ];
      const level = levels[Math.max(0, score - 1)];
      for (let i = 0; i < score; i++) {
        if (bars[i]) bars[i].style.backgroundColor = colors[level.key];
      }
      if (label) label.textContent = level.text;
    });
  }

  /* ---------- Flash message auto-dismiss ---------- */
  document.querySelectorAll("[data-flash]").forEach((el) => {
    const dismissBtn = el.querySelector("[data-flash-dismiss]");
    if (dismissBtn) {
      dismissBtn.addEventListener("click", () => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 300);
      });
    }
    if (el.dataset.autodismiss === "true") {
      setTimeout(() => {
        el.style.opacity = "0";
        setTimeout(() => el.remove(), 300);
      }, 4000);
    }
  });

  /* ---------- Scroll reveal animations ---------- */
  // Every page gets the same effect without tagging each element by hand:
  // blocks inside <main> sections/articles fade up as they scroll into view,
  // and card grids reveal card by card. Add class "reveal" to force one element,
  // or data-no-reveal on a wrapper to opt out.
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!prefersReducedMotion && "IntersectionObserver" in window) {
    const found = new Map(); // element -> stagger delay (ms)

    const isWrapper = (el) =>
      el.tagName === "DIV" && el.classList.contains("mx-auto") && /\bmax-w-/.test(el.className);

    const collect = (parent, delay = 0) => {
      Array.from(parent.children).forEach((child, i) => {
        if (child.closest("[data-no-reveal]") || child.matches("script, style, template, [hidden], [aria-hidden='true']")) return;
        const cs = getComputedStyle(child);
        if (cs.display === "none" || cs.display === "contents") return;
        if (cs.position === "absolute" || cs.position === "fixed" || cs.position === "sticky") return;

        if (child.classList.contains("reveal")) { found.set(child, Math.min(i, 5) * 70); return; }
        if (isWrapper(child)) { collect(child, delay); return; }

        // A plain grid (no border/background) is just layout: reveal its items one by one.
        const isBareGrid = cs.display === "grid" && child.children.length > 1 &&
          cs.borderTopWidth === "0px" && cs.backgroundColor === "rgba(0, 0, 0, 0)";
        if (isBareGrid) { collect(child, delay); return; }

        found.set(child, delay || Math.min(i, 5) * 70);
      });
    };

    document.querySelectorAll(".reveal").forEach((el) => { if (!found.has(el)) found.set(el, 0); });
    document.querySelectorAll("main section, main article").forEach((section) => {
      if (isWrapper(section) || section.children.length) collect(section);
    });

    // Never animate both a block and something inside it.
    const all = Array.from(found.keys());
    const targets = all.filter((el) => !all.some((other) => other !== el && other.contains(el)));

    targets.forEach((el) => {
      el.classList.add("opacity-0", "translate-y-3", "transition-all", "duration-700");
      el.style.transitionDelay = found.get(el) + "ms";
    });

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          el.classList.remove("opacity-0", "translate-y-3");
          // Afterwards drop the slow fade + delay so hover effects stay snappy.
          const delay = parseInt(el.style.transitionDelay, 10) || 0;
          const cleanup = (e) => {
            if (e && e.target !== el) return; // ignore transitions bubbling up from children
            el.classList.remove("duration-700");
            el.style.transitionDelay = "";
            el.removeEventListener("transitionend", cleanup);
          };
          el.addEventListener("transitionend", cleanup);
          // Safety net: some browsers skip transitionend (e.g. tab in background).
          setTimeout(() => cleanup(), delay + 900);
          io.unobserve(el);
        });
      },
      // threshold 0 + a small bottom margin: tall blocks (long posts) still trigger.
      { threshold: 0, rootMargin: "0px 0px -8% 0px" }
    );
    targets.forEach((el) => io.observe(el));
  }

  /* ---------- Profile: avatar preview + bio counter ---------- */
  const MAX_AVATAR_BYTES = 2 * 1024 * 1024;
  const avatarInput = document.querySelector("[data-avatar-input]");
  if (avatarInput) {
    const preview = document.querySelector("[data-avatar-preview]");
    const current = document.querySelector("[data-avatar-current]");
    const hint = document.querySelector("[data-avatar-hint]");
    let objectUrl = null;

    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      if (!/^image\/(png|jpeg|webp)$/.test(file.type)) {
        avatarInput.value = "";
        if (hint) hint.textContent = "Use a JPG, PNG or WebP image.";
        return;
      }
      if (file.size > MAX_AVATAR_BYTES) {
        avatarInput.value = "";
        if (hint) hint.textContent = "That image is over 2 MB.";
        return;
      }
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);
      if (preview) { preview.src = objectUrl; preview.classList.remove("hidden"); }
      if (current) current.classList.add("hidden");
      if (hint) hint.textContent = file.name;
    });
  }

  document.querySelectorAll("[data-counter]").forEach((field) => {
    const out = document.getElementById(field.dataset.counter);
    if (!out) return;
    const update = () => { out.textContent = field.value.length; };
    field.addEventListener("input", update);
    update();
  });
});
