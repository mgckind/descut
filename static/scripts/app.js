(function(document) {
  'use strict';

  var app = document.querySelector('#app');

  app.baseUrl = '/';
  if (window.location.port === '') {  // if production
  };


  window.addEventListener('WebComponentsReady', function() {
    var pages = document.getElementById("mainPages");
    var menu = document.querySelector('paper-menu');
    var help = document.getElementById("helpPages");
    app.selection="0";
    pages.selected="0";
    menu.selected="0";
    help.selected="0";
        menu.addEventListener('iron-select', function() {
            app.selection=menu.selected;
            pages.selected=menu.selected;
            help.selected=menu.selected;
           app.$.paperDrawerPanel.closeDrawer();
        });
        menu.addEventListener('iron-activate', function() {
           app.$.paperDrawerPanel.closeDrawer();
        });
        var list = document.getElementById("jobList");
        var smallList = document.getElementById("smallJobList");
        var smallListL = document.getElementById("smallJobListL");
        var checkList = document.getElementById("checkAll");
        list.addEventListener('iron-select', function(){
            var listAll = [];
            listAll = list.selectedValues;
            if (listAll.length > 0){
                document.getElementById("DeleteHeader").style.display = "block";
                document.getElementById("ListHeader").style.display = "none";
                checkList.checked = true;
                };
            });
        //smallList.addEventListener('iron-select', function(){
          //  console.log(smallList.selectedItem.item);
           // document.getElementById("desResults").jobid=smallList.selectedItem.innerText.trim();
           // desResults.username = document.getElementById("desJobs").username;
           // document.getElementById("getTiles").generateRequest();
            //});
        //smallListL.addEventListener('iron-select', function(){
          //  document.getElementById("desLog").jobid=smallList.selectedItem.innerText.trim();
           // document.getElementById("getLog").generateRequest();
            //});

        list.addEventListener('iron-deselect', function(){
            var listAll = [];
            listAll = list.selectedValues;
            if (listAll.length == 0){
                document.getElementById("DeleteHeader").style.display = "none";
                document.getElementById("ListHeader").style.display = "block";
                checkList.checked = false;
                };
            });
        list.addEventListener('iron-items-changed', function(){
            document.getElementById("DeleteHeader").style.display = "none";
            document.getElementById("ListHeader").style.display = "block";
            checkList.checked = false;
            });

        var xsize = document.getElementById("xsizeSlider");
        xsize.addEventListener('value-change', function() {
        document.getElementById("xsizeLabel").textContent = xsize.value;
        });
        var ysize = document.getElementById("ysizeSlider");
        ysize.addEventListener('value-change', function() {
        document.getElementById("ysizeLabel").textContent = ysize.value;
        });


  });

  app.scrollPageToTop = function() {
    app.$.headerPanelMain.scrollToTop(false);
  };

  app.closeDrawer = function() {
    app.$.paperDrawerPanel.closeDrawer();
  };

})(document);
