(function(document) {
    'use strict';

    var app = document.querySelector('#app');

    app.baseUrl = '/';
    if (window.location.port === '') {  // if production
    };


    window.addEventListener('WebComponentsReady', function() {

        var pages = document.getElementById("mainPages");
        var menu = document.getElementById('bigmenu');
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
            app.editor.refresh();

        });
        menu.addEventListener('iron-activate', function() {
            app.$.paperDrawerPanel.closeDrawer();
        });

        var jobsEntry = document.getElementById("jobs");
        // var sharedEntry = document.getElementById("shared");
        var coaddEntry = document.getElementById("coadd");
        // var epochEntry = document.getElementById("epoch");
        // var apiEntry = document.getElementById("api");
        var footprintEntry = document.getElementById("footprint");


        var queryEntry = document.getElementById("query");
        var allTablesEntry = document.getElementById("allTables");
        var exampleEntry = document.getElementById("example");
        // var helpEntry = document.getElementById("help");

        // var demoEntry = document.getElementById("demo");

        // var gal = document.getElementById("mainGallery");

        jobsEntry.addEventListener('click', function() {
            // gal.selected = "1";
            menu.selected="1";
            app.selection="1";
            pages.selected="1";
            // help.selected="1";
            app.$.paperDrawerPanel.closeDrawer();
        });

        coaddEntry.addEventListener('click', function() {
            // gal.selected = "2";
            menu.selected="2";
            app.selection="2";
            pages.selected="2";
            // help.selected="2";
            app.$.paperDrawerPanel.closeDrawer();
        });

        footprintEntry.addEventListener('click', function() {
            // gal.selected = "3";
            menu.selected="3";
            app.selection="3";
            pages.selected="3";
            // help.selected="3";
            app.$.paperDrawerPanel.closeDrawer();
        });



        queryEntry.addEventListener('click', function() {
            // gal.selected = "4";
            menu.selected="4";
            app.selection="4";
            pages.selected="4";
            // help.selected="11";
            app.$.paperDrawerPanel.closeDrawer();
        });

        allTablesEntry.addEventListener('click', function() {
            // gal.selected = "5";
            menu.selected="5";
            app.selection="5";
            pages.selected="5";
            // help.selected="5";
            app.$.paperDrawerPanel.closeDrawer();
        });

        exampleEntry.addEventListener('click', function() {
            // gal.selected = "6";
            menu.selected="6";
            app.selection="6";
            pages.selected="6";
            // help.selected="6";
            app.$.paperDrawerPanel.closeDrawer();
        });


        // // var list = document.getElementById("jobList");
        // // var list2 = document.getElementById("jobListShared");
        // var smallList = document.getElementById("smallJobList");
        // var smallListL = document.getElementById("smallJobListL");
        // var smallList2 = document.getElementById("smallJobListShared");
        // var smallListL2 = document.getElementById("smallJobListLShared");
        // var checkList = document.getElementById("checkAll");
        // var checkList2 = document.getElementById("checkAllShared");
        //
        // list.addEventListener('iron-select', function(){
        //     var listAll = [];
        //     listAll = list.selectedValues;
        //     if (listAll.length > 0){
        //         document.getElementById("DeleteHeader").style.display = "block";
        //         document.getElementById("ListHeader").style.display = "none";
        //         checkList.checked = true;
        //     };
        // });
        //
        // //smallList.addEventListener('iron-select', function(){
        //   //  console.log(smallList.selectedItem.item);
        //    // document.getElementById("desResults").jobid=smallList.selectedItem.innerText.trim();
        //    // desResults.username = document.getElementById("desJobs").username;
        //    // document.getElementById("getTiles").generateRequest();
        //     //});
        // //smallListL.addEventListener('iron-select', function(){
        //   //  document.getElementById("desLog").jobid=smallList.selectedItem.innerText.trim();
        //    // document.getElementById("getLog").generateRequest();
        //     //});
        //
        // list.addEventListener('iron-deselect', function(){
        //     var listAll = [];
        //     listAll = list.selectedValues;
        //     if (listAll.length == 0){
        //         document.getElementById("DeleteHeader").style.display = "none";
        //         document.getElementById("ListHeader").style.display = "block";
        //         checkList.checked = false;
        //         };
        // });
        //
        //
        // list.addEventListener('iron-items-changed', function(){
        //     document.getElementById("DeleteHeader").style.display = "none";
        //     document.getElementById("ListHeader").style.display = "block";
        //     checkList.checked = false;
        // });
        //
        // list2.addEventListener('iron-select', function(){
        //     var listAll = [];
        //     listAll = list2.selectedValues;
        //     if (listAll.length > 0){
        //         checkList2.checked = true;
        //     };
        // });
        //
        // list2.addEventListener('iron-deselect', function(){
        //     var listAll = [];
        //     listAll = list2.selectedValues;
        //     if (listAll.length == 0){
        //         // document.getElementById("InfoHeader").style.display = "none";
        //         document.getElementById("ListHeaderShared").style.display = "block";
        //         checkList2.checked = false;
        //     };
        // });
        //
        // list2.addEventListener('iron-items-changed', function(){
        //     // document.getElementById("InfoHeader").style.display = "none";
        //     document.getElementById("ListHeaderShared").style.display = "block";
        //     checkList2.checked = false;
        // });

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
    var myQuery = document.getElementById("queryBox");
    app.editor = CodeMirror.fromTextArea(myQuery, {
        lineNumbers: true,
        mode: 'text/x-plsql',
        autofocus: true,
    });
    app.editor.setValue('-- Insert Query --\n');
    app.editor.focus();
    app.editor.execCommand('goLineDown');
    var myJobQuery = document.getElementById("jobQueryBox");
    app.jobquerybox = CodeMirror.fromTextArea(myJobQuery, {
        lineNumbers: false,
        mode: 'text/x-plsql',
        readOnly: true,
        autofocus: true,
    });
    app.jobquerybox.setValue('\n\n\n\n\n\n\n\n\n\n');
    app.jobquerybox.focus();

})(document);
