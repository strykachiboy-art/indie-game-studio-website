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
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealTargets = document.querySelectorAll(".reveal");
  if (revealTargets.length && !prefersReducedMotion && "IntersectionObserver" in window) {
    revealTargets.forEach((el) =>
      el.classList.add("opacity-0", "translate-y-3", "transition-all", "duration-700")
    );
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.remove("opacity-0", "translate-y-3");
            // Drop the slow fade-in duration afterwards so hover effects stay snappy.
            entry.target.addEventListener(
              "transitionend",
              () => entry.target.classList.remove("duration-700"),
              { once: true }
            );
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    revealTargets.forEach((el) => io.observe(el));
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
