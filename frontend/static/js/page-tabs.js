(() => {
  const panels = [...document.querySelectorAll("[data-page-panel]")];
  if (!panels.length) return;

  const tablist = document.querySelector("[data-page-tablist]");
  const panelByName = new Map(
    panels.map((panel) => [panel.dataset.pagePanel, panel]),
  );
  const tabLinks = [...document.querySelectorAll(".main-nav [data-page-tab]")];
  const curtain = document.querySelector(".page-curtain");
  const transitionDuration = 360;
  let activePage = "inicio";
  let transitionDirection = 1;
  let isTransitioning = false;

  function setPage(pageName) {
    const activePanel = panelByName.get(pageName);
    if (!activePanel) return false;

    activePage = pageName;
    panels.forEach((panel) => {
      const isActive = panel === activePanel;
      panel.hidden = !isActive;
      panel.classList.toggle("is-active", isActive);
    });
    tabLinks.forEach((link) => {
      const isActive = link.dataset.pageTab === pageName;
      link.setAttribute("aria-selected", String(isActive));
      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
    return true;
  }

  function getPageFromLocation() {
    const requestedPage = window.location.hash.slice(1);
    return panelByName.has(requestedPage) ? requestedPage : "inicio";
  }

  function updateHistory(pageName) {
    const nextUrl = `${window.location.pathname}${window.location.search}#${pageName}`;
    window.history.pushState({ pageName }, "", nextUrl);
  }

  async function switchPage(pageName, { updateUrl = true, animate = true } = {}) {
    if (!panelByName.has(pageName) || pageName === activePage || isTransitioning) {
      return;
    }

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (!animate || reduceMotion || !curtain || typeof curtain.animate !== "function") {
      setPage(pageName);
      if (updateUrl) updateHistory(pageName);
      window.scrollTo(0, 0);
      return;
    }

    isTransitioning = true;
    const enteringFrom = transitionDirection === 1 ? "100%" : "-100%";
    const leavingTo = transitionDirection === 1 ? "-100%" : "100%";
    curtain.classList.add("is-active");

    await curtain.animate(
      [{ transform: `translateY(${enteringFrom})` }, { transform: "translateY(0)" }],
      { duration: transitionDuration, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
    ).finished;

    curtain.style.transform = "translateY(0)";
    setPage(pageName);
    if (updateUrl) updateHistory(pageName);
    window.scrollTo(0, 0);

    await curtain.animate(
      [{ transform: "translateY(0)" }, { transform: `translateY(${leavingTo})` }],
      { duration: transitionDuration, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
    ).finished;

    curtain.classList.remove("is-active");
    curtain.style.transform = `translateY(${leavingTo})`;
    transitionDirection *= -1;
    isTransitioning = false;
  }

  document.body.classList.add("has-page-tabs");
  if (tablist) tablist.setAttribute("role", "tablist");
  tabLinks.forEach((link) => {
    link.setAttribute("role", "tab");
    link.setAttribute("aria-controls", `pagina-${link.dataset.pageTab}`);
  });
  panels.forEach((panel) => {
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", `tab-${panel.dataset.pagePanel}`);
    panel.setAttribute("tabindex", "-1");
  });
  setPage(getPageFromLocation());

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;

    const tabLink = event.target.closest("[data-page-tab]");
    if (!tabLink || !panelByName.has(tabLink.dataset.pageTab)) return;

    event.preventDefault();
    void switchPage(tabLink.dataset.pageTab);
  });

  document.addEventListener("keydown", (event) => {
    const currentIndex = tabLinks.indexOf(document.activeElement);
    if (currentIndex === -1) return;

    let nextIndex;
    if (event.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % tabLinks.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + tabLinks.length) % tabLinks.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = tabLinks.length - 1;
    } else {
      return;
    }

    event.preventDefault();
    const nextTab = tabLinks[nextIndex];
    nextTab.focus();
    void switchPage(nextTab.dataset.pageTab);
  });

  window.addEventListener("popstate", () => {
    void switchPage(getPageFromLocation(), { updateUrl: false });
  });
})();
