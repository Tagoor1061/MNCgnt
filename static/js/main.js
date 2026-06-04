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

// Hide loading overlay when page is fully loaded with a 0.5 second delay
window.addEventListener('load', () => {
  const loadingOverlay = document.getElementById('loading-overlay');
  if (loadingOverlay) {
    setTimeout(() => {
      loadingOverlay.style.display = 'none';
    }, 500); // 500 milliseconds = 0.5 seconds
  }
});

// Push Notification Functions
function requestNotificationPermission() {
  if ('Notification' in window) {
    Notification.requestPermission().then(function(permission) {
      if (permission === 'granted') {
        console.log('Notification permission granted.');
        subscribeToNotifications();
      } else {
        console.log('Notification permission denied.');
      }
    });
  }
}

function unsubscribeFromNotifications() {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    navigator.serviceWorker.ready.then(function(registration) {
      registration.pushManager.getSubscription().then(function(subscription) {
        if (subscription) {
          subscription.unsubscribe().then(function(successful) {
            console.log('Successfully unsubscribed:', successful);
            fetch('/push/unsubscribe', {
              method: 'POST',
              body: JSON.stringify({ endpoint: subscription.endpoint }),
              headers: {
                'Content-Type': 'application/json'
              }
            });
          }).catch(function(error) {
            console.log('Failed to unsubscribe:', error);
          });
        }
      });
    });
  }
}

// Add notification button to page if supported
document.addEventListener('DOMContentLoaded', function() {
  if ('Notification' in window && 'serviceWorker' in navigator) {
    // Create notification permission button
    const notificationBtn = document.createElement('button');
    notificationBtn.id = 'notification-btn';
    notificationBtn.innerHTML = '🔔 Enable Weather Alerts';
    notificationBtn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #007bff;
      color: white;
      border: none;
      padding: 10px 15px;
      border-radius: 5px;
      cursor: pointer;
      z-index: 1000;
      display: none;
    `;

    if (Notification.permission === 'default') {
      notificationBtn.style.display = 'block';
      notificationBtn.addEventListener('click', requestNotificationPermission);
    } else if (Notification.permission === 'granted') {
      notificationBtn.innerHTML = '🔕 Disable Weather Alerts';
      notificationBtn.style.display = 'block';
      notificationBtn.addEventListener('click', unsubscribeFromNotifications);
    }

    document.body.appendChild(notificationBtn);
  }
});
