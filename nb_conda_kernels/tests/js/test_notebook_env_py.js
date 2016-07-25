/* global casper */

var kernel_prefix = 'conda-env',
  kernel_suffix = 'py',
  kernel_label = 'Python';

casper.notebook_test_kernel(kernel_prefix, kernel_suffix, function(){
  casper.screenshot.init("env-python-kernel");
  casper.viewport(1440, 900)
    .then(default_python_kernel_test);
});

function default_python_kernel_test(){
  this.screenshot("kernel_indicator_name");
  this.test.assertSelectorHasText('.kernel_indicator_name', kernel_label);
}
