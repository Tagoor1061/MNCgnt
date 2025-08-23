// Mobile Menu Toggle (for future use)
document.addEventListener('DOMContentLoaded', function() {
  // Initialize any JavaScript plugins or custom functionality
  
  // Example: Mobile menu toggle
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const mainNav = document.querySelector('nav ul');
  
  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', function() {
      mainNav.classList.toggle('active');
    });
  }

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });

  // Form validation example (can be extended)
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      // Add form validation logic here
    });
  });
});

// Dynamic year in footer
const yearSpan = document.querySelector('footer p');
if (yearSpan) {
  const currentYear = new Date().getFullYear();
  yearSpan.innerHTML = yearSpan.innerHTML.replace('2025', currentYear);
}

// Dark mode toggle (example feature)
const darkModeToggle = document.getElementById('dark-mode-toggle');
if (darkModeToggle) {
  darkModeToggle.addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
  });

  // Check for saved user preference
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
  }
}
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll(".auth-container form");

  forms.forEach(form => {
    form.addEventListener("submit", (e) => {
      const inputs = form.querySelectorAll("input[required]");
      let valid = true;

      inputs.forEach(input => {
        if (!input.value.trim()) {
          input.style.border = "1px solid red";
          valid = false;
        } else {
          input.style.border = "1px solid #ccc";
        }
      });

      if (!valid) {
        e.preventDefault();
        alert("Please fill all required fields!");
      }
    });
  });
});
