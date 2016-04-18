/* global casper */
casper.dashboard_test(function(){
  casper.screenshot.init("basic");
  casper.viewport(1440, 900)
    .then(basic_test);
});

function basic_test(){
  var pysel = '#new-menu li[id*=Python]',
    rsel = '#new-menu li[id*=R ]';

  return this.canSeeAndClick(
      "the kernel selector", "#new-buttons > .dropdown-toggle"
    )
    .canSee("a python kernel", pysel)
    .canSee("an r kernel", rsel)
    .canSeeAndClick("fin", "body");
}
