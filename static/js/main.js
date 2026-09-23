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
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    revealTargets.forEach((el) => io.observe(el));
  }
});
