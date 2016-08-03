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
        var list = document.getElementById("jobList");
        list.addEventListener('iron-select', function(){
            var listAll = [];
            listAll = list.selectedValues;
            if (listAll.length > 0){
                document.getElementById("deleteSelected").style.display = "block";
                };
            });
        list.addEventListener('iron-deselect', function(){
            var listAll = [];
            listAll = list.selectedValues;
            if (listAll.length == 0){
                document.getElementById("deleteSelected").style.display = "none";
                };
            });


  });

  app.scrollPageToTop = function() {
    app.$.headerPanelMain.scrollToTop(false);
  };

  app.closeDrawer = function() {
    app.$.paperDrawerPanel.closeDrawer();
  };

})(document);
