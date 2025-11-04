// Back to Top Button with smooth fade
(function() {
  const backToTopButton = document.getElementById("back-to-top");
  
  if (!backToTopButton) return;

  // Show/hide button based on scroll position with opacity transition
  window.addEventListener('scroll', function() {
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
      backToTopButton.style.display = "block";
      // Small delay for display:block to take effect before opacity
      setTimeout(function() {
        backToTopButton.style.opacity = "1";
      }, 10);
    } else {
      backToTopButton.style.opacity = "0";
      setTimeout(function() {
        if (document.documentElement.scrollTop <= 100) {
          backToTopButton.style.display = "none";
        }
      }, 300);
    }
  });

  // Smooth scroll to top
  backToTopButton.addEventListener('click', function(e) {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
})();

// External links - open in new tab with security
document.addEventListener('DOMContentLoaded', function() {
  const links = document.querySelectorAll('a[href^="http"]');
  links.forEach(function(link) {
    // Check if link is external
    if (!link.href.includes(window.location.hostname)) {
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    }
  });
});

// Active navigation state
(function() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('header nav a');
  
  navLinks.forEach(function(link) {
    const linkPath = link.getAttribute('href');
    
    // Exact match for home
    if (linkPath === '/' && currentPath === '/') {
      link.style.color = 'var(--accent)';
    }
    // Match for blog section
    else if (linkPath && linkPath.includes('/blog') && currentPath.includes('/blog')) {
      link.style.color = 'var(--accent)';
    }
  });
})();