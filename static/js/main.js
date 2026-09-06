/* =========================================================
   FRESHROOTS - MAIN JAVASCRIPT
   ========================================================= */


/* =========================================================
   PAGE LOAD
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("FreshRoots website loaded successfully.");

    initializeScrollAnimations();

});


/* =========================================================
   NAVBAR SCROLL EFFECT
   ========================================================= */

window.addEventListener("scroll", function () {

    const header = document.querySelector(".site-header");

    if (!header) {
        return;
    }

    if (window.scrollY > 50) {

        header.classList.add("scrolled");

    } else {

        header.classList.remove("scrolled");

    }

});


/* =========================================================
   SCROLL REVEAL ANIMATIONS
   ========================================================= */

function initializeScrollAnimations() {

    const animatedElements = document.querySelectorAll(
        `
        .story-section,
        .feature,
        .welcome-section,
        .cta-section,
        .about-story,
        .mission-card,
        .value-card,
        .journey-step,
        .about-cta
        `
    );


    if (!animatedElements.length) {
        return;
    }


    const observer = new IntersectionObserver(

        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    entry.target.classList.add("visible");

                    observer.unobserve(entry.target);

                }

            });

        },

        {
            threshold: 0.15
        }

    );


    animatedElements.forEach(function (element) {

        observer.observe(element);

    });

}


/* =========================================================
   CURRENT YEAR
   ========================================================= */

const yearElement =
    document.getElementById("current-year");


if (yearElement) {

    yearElement.textContent =
        new Date().getFullYear();

}