
/* ================= MOBILE MENU ================= */

const menuToggle = document.getElementById("menuToggle");
const navbarLinks = document.querySelector(".navbar-links");
const navbarAuth = document.querySelector(".navbar-auth");


if (menuToggle) {

    menuToggle.addEventListener("click", function () {

        navbarLinks.classList.toggle("active");
        navbarAuth.classList.toggle("active");

    });

}
