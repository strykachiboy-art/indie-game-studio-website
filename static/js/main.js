// Mobile navigation toggle — slide-in drawer
document.addEventListener("DOMContentLoaded", function () {
  const navToggle = document.getElementById("nav-toggle");
  const navDrawer = document.getElementById("nav-drawer");
  const navBackdrop = document.getElementById("nav-backdrop");

  if (!navToggle || !navDrawer || !navBackdrop) return;

  const bars = navToggle.querySelectorAll(".bar");

  function openMenu() {
    navToggle.setAttribute("aria-expanded", "true");
    navDrawer.setAttribute("aria-hidden", "false");
    navDrawer.classList.remove("translate-x-full");
    navBackdrop.classList.remove("hidden");
    requestAnimationFrame(() => navBackdrop.classList.remove("opacity-0"));
    document.body.classList.add("overflow-hidden");

    bars[0].style.transform = "translateY(7px) rotate(45deg)";
    bars[1].style.opacity = "0";
    bars[1].style.transform = "scaleX(0)";
    bars[2].style.transform = "translateY(-7px) rotate(-45deg)";
  }

  function closeMenu() {
    navToggle.setAttribute("aria-expanded", "false");
    navDrawer.setAttribute("aria-hidden", "true");
    navDrawer.classList.add("translate-x-full");
    navBackdrop.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");

    bars[0].style.transform = "";
    bars[1].style.opacity = "1";
    bars[1].style.transform = "scaleX(1)";
    bars[2].style.transform = "";
  }

  navToggle.addEventListener("click", () => {
    const isOpen = navToggle.getAttribute("aria-expanded") === "true";
    isOpen ? closeMenu() : openMenu();
  });

  navBackdrop.addEventListener("click", closeMenu);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  // Close drawer when a link inside it is clicked
  navDrawer.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });
});