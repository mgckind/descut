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


        // function _selectPage(index) {
        //    window.alert(5 + 6);
        // }
        var jobsEntry = document.getElementById("jobs");
        var coaddEntry = document.getElementById("coadd");
        var epochEntry = document.getElementById("epoch");
        var apiEntry = document.getElementById("api");
        var footprintEntry = document.getElementById("footprint");

        var gal = document.getElementById("mainGallery");

        jobsEntry.addEventListener('click', function() {
            gal.selected = "1";
        });

        coaddEntry.addEventListener('click', function() {
            gal.selected = "2";
        });

        epochEntry.addEventListener('click', function() {
            gal.selected = "3";
        });

        apiEntry.addEventListener('click', function() {
            gal.selected = "4";
        });

        footprintEntry.addEventListener('click', function() {
            gal.selected = "5";
        });
        // viewlog: function(e) {
        //     e.stopPropagation();
        //     var pages = document.getElementById("mainPages");
        //     var help = document.getElementById("helpPages");
        //     var menu = document.querySelector('paper-menu');
        //     var desLog = document.getElementById("desLog");
        //     var desResults = document.getElementById("desResults");
        //     document.getElementById("smallJobList").selected=e.model.index;
        //     document.getElementById("smallJobListL").selected=e.model.index;
        //     desLog.jobidFull = e.model.item.job;
        //     desLog.jobid= this.returnName(e.model.item.job);
        //     desResults.jobid = this.returnName(e.model.item.job);
        //     desResults.jobidFull = e.model.item.job;
        //     desResults.username = this.username;
        //     desResults.jtypes = e.model.item.jtypes;
        //     app.selection="7";
        //     pages.selected="7";
        //     menu.selected="7";
        //     help.selected="7";
        // },
        // var iron_coadds = document.querySelector('iron-pages');
        // var coadds = document.getElementById('coadds-page')
        // iron_coadds.addEventListener('click', function(e) {
        //     coadds.selectNext();
        //     coadds.selected="0";
        // });

        // var worker = document.querySelector('iron-pages');
        // var choice = document.querySelector('iron-selector');
        // var intro = document.getElementById('mainGallery')
        // choice.addEventListener('click', function(e) {
        //     intro.selected = choice.selected;
        // });



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

        var xsizeS = document.getElementById("xsizeSliderS");
            xsizeS.addEventListener('value-change', function() {
            document.getElementById("xsizeLabelS").textContent = xsizeS.value;
        });
        var ysizeS = document.getElementById("ysizeSliderS");
            ysizeS.addEventListener('value-change', function() {
            document.getElementById("ysizeLabelS").textContent = ysizeS.value;
        });

    });

    app.scrollPageToTop = function() {
        app.$.headerPanelMain.scrollToTop(false);
    };

    app.closeDrawer = function() {
        app.$.paperDrawerPanel.closeDrawer();
    };

})(document);
