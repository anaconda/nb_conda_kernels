/* global casper */

var kernel_prefix = 'ir',
  kernel_suffix = '',
  kernel_label = 'R';

casper.notebook_test_kernel(kernel_prefix, kernel_suffix, function(){
  casper.screenshot.init("default-r-kernel");
  casper.viewport(1440, 900)
    .then(default_r_kernel_test);
});

function default_r_kernel_test(){
  this.screenshot("kernel_indicator_name");
  this.test.assertSelectorHasText('.kernel_indicator_name', kernel_label);
}
