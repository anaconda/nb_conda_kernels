/* global casper */
casper.notebook_test(function(){
  casper.screenshot.init("basic");
  casper.viewport(1440, 900)
    .then(basic_test);
});

function basic_test(){
  this.baseline_notebook();

  return this.then(function(){
    this.canSeeAndClick("the body", "body");
  });
}
