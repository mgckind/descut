(function(document) {
  'use strict';

  var app = document.querySelector('#app');

  app.baseUrl = '/';
  if (window.location.port === '') {  // if production
  };


  window.addEventListener('WebComponentsReady', function() {
    var pages = document.querySelector('iron-pages');
    var menu = document.querySelector('paper-menu');
    app.selection="0";
    pages.selected="0";
    menu.selected="0";
        menu.addEventListener('iron-select', function() {
            app.selection=menu.selected;
            pages.selected=menu.selected;
           app.$.paperDrawerPanel.closeDrawer();
        });
        menu.addEventListener('iron-activate', function() {
           app.$.paperDrawerPanel.closeDrawer();
        });
  });

  app.scrollPageToTop = function() {
    app.$.headerPanelMain.scrollToTop(true);
  };

  app.closeDrawer = function() {
    app.$.paperDrawerPanel.closeDrawer();
  };

})(document);
