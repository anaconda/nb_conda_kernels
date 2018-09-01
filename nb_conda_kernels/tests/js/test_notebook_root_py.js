/* global casper */

var kernel_prefix = 'conda-root-py',
  kernel_suffix = '',
  kernel_label = 'Python [conda env:root]';

casper.notebook_test_kernel(kernel_prefix, kernel_suffix, function(){
  casper.screenshot.init("root-python-kernel");
  casper.viewport(1440, 900)
    .then(root_python_kernel_test);
});

function root_python_kernel_test(){
  this.screenshot("kernel_indicator_name");
  this.test.assertSelectorHasText('.kernel_indicator_name', kernel_label);
}
