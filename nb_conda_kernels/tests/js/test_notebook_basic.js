/* global casper */
casper.dashboard_test(function(){
  casper.screenshot.init("basic");
  casper.viewport(1440, 900)
    .then(basic_test);
});

function basic_test(){
  var default_py = '#new-menu li[id^=kernel-python]',
    default_r = '#new-menu li[id=kernel-ir]',
    root_py = '#new-menu li[id=kernel-conda-root-py]',
    env_py = '#new-menu li[id^=kernel-conda-env-][id$=-py]',
    env_r = '#new-menu li[id^=kernel-conda-env-][id$=-r]';

  return this.canSeeAndClick(
      "the kernel selector", "#new-buttons > .dropdown-toggle"
    )
    .canSee("the default python kernel", default_py)
    .canSee("a conda env python kernel", env_py)
    .canSee("a conda root python kernel", root_py)
    .canSee("the default r kernel", default_r)
    .canSee("an r kernel", env_r)
    .canSeeAndClick("fin", "body");
}
