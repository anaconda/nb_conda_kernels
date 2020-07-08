;(function(){
  "use strict";

  var system = require('system');

  var root = casper,
    _img = 0,
    _shotDir = "unnamed";

  function nextId(){
    return ("000" + (_img++)).slice(-4);
  }

  function slug(text){
    return text.replace(/[^a-z0-9]/g, "_");
  }

  root.screenshot = function(message){
    this.captureSelector([
        "screenshots/",
         _shotDir,
         "/",
         nextId(),
         "_",
         slug(message),
         ".png",
      ].join(""),
      "body"
    );
  };


  root.screenshot.init = function(ns){
    _shotDir = ns;
    _img = 0;
  };

  root.canSee = function(message, visible){
    return this
      .waitUntilVisible(visible)
      .then(function(){
        this.test.assertExists(visible, "I can see " + message);
        this.screenshot(message);
      });
  };

  root.canSeeAndClick = function(message, visible, click){
    return this
      .waitUntilVisible(visible)
      .then(function(){
        this.test.assertExists(click || visible, "I can see and click " + message);
        this.screenshot(message);
        this.click(click || visible);
      });
  };

  root.dragRelease = function(message, selector, opts){
    var it, x, y, x1, y1;
    return this.then(function(){
      it = this.getElementBounds(selector);
      x = it.left + it.width / 2;
      y = it.top + it.height / 2;
      x1 = x + (opts.right || -opts.left || 0);
      y1 = y + (opts.down || -opts.up || 0);
    })
    .then(function(){
      this.mouse.down(x, y);
    })
    .then(function(){
      this.screenshot("click " + message);
      this.mouse.move(x1, y1);
    })
    .then(function(){
      this.screenshot("drag " + message);
      this.mouse.up(x1, y1);
    })
    .then(function(){
      this.screenshot("release " + message);
    });
  };

  root.baseline_notebook = function(){
    // the actual test
    this.set_cell_text(0, [
      'from IPython.display import Markdown',
      'Markdown("# Hello World!")'
    ].join("\n"));
    this.execute_cell_then(0);

    this.append_cell();
  };

  root.runCell = function(idx, lines){
    // the actual test
    this.set_cell_text(idx, lines.join("\n"));
    this.execute_cell_then(idx);
  };

  casper.notebook_test_kernel = function(kernel_prefix, kernel_suffix, test) {
    // Wrap a notebook test to reduce boilerplate.
    this.open_new_notebook_kernel(kernel_prefix, kernel_suffix);

    // Echo whether or not we are running this test using SlimerJS
    if (this.evaluate(function(){
        return typeof InstallTrigger !== 'undefined';   // Firefox 1.0+
    })) {
        console.log('This test is running in SlimerJS.');
        this.slimerjs = true;
    }

    // Make sure to remove the onbeforeunload callback.  This callback is
    // responsible for the "Are you sure you want to quit?" type messages.
    // PhantomJS ignores these prompts, SlimerJS does not which causes hangs.
    this.then(function(){
        this.evaluate(function(){
            window.onbeforeunload = function(){};
        });
    });

    this.then(test);

    // Kill the kernel and delete the notebook.
    this.shutdown_current_kernel();
    // This is still broken but shouldn't be a problem for now.
    // this.delete_current_notebook();

    // This is required to clean up the page we just finished with. If we don't call this
    // casperjs will leak file descriptors of all the open WebSockets in that page. We
    // have to set this.page=null so that next time casper.start runs, it will create a
    // new page from scratch.
    this.then(function () {
        this.page.close();
        this.page = null;
    });

    // Run the browser automation.
    this.run(function() {
        this.test.done();
    });
  };

  root.open_new_notebook_kernel = function (kernel_prefix, kernel_suffix) {
    // Create and open a new notebook.
    var baseUrl = this.get_notebook_server();
    this.start(baseUrl);

    this.waitFor(this.page_loaded);
    this.waitForSelector("#new-buttons > .dropdown-toggle");
    this.thenClick("#new-buttons > .dropdown-toggle");

    var kernel_li_id = '[id^="kernel-' + kernel_prefix + '"]';
    if(kernel_suffix){
      kernel_li_id += '[id$="-' + kernel_suffix + '"]';
    }
    var kernel_selector = '#new-menu li' + kernel_li_id + ' a';

    this.waitForSelector(kernel_selector);
    this.thenClick(kernel_selector);

    this.screenshot("picking kernel");

    this.waitForPopup('');

    this.withPopup('', function () {this.waitForSelector('.CodeMirror-code');});
    this.then(function () {
        this.open(this.popups[0].url);
    });
    this.waitFor(this.page_loaded);

    // Hook the log and error methods of the console, forcing them to
    // serialize their arguments before printing.  This allows the
    // Objects to cross into the phantom/slimer regime for display.
    this.thenEvaluate(function(){
        var serialize_arguments = function(f, context) {
            return function() {
                var pretty_arguments = [];
                for (var i = 0; i < arguments.length; i++) {
                    var value = arguments[i];
                    if (value instanceof Object) {
                        var name = value.name || 'Object';
                        // Print a JSON string representation of the object.
                        // If we don't do this, [Object object] gets printed
                        // by casper, which is useless.  The long regular
                        // expression reduces the verbosity of the JSON.
                        pretty_arguments.push(name + ' {' + JSON.stringify(value, null, '  ')
                            .replace(/(\s+)?({)?(\s+)?(}(\s+)?,?)?(\s+)?(\s+)?\n/g, '\n')
                            .replace(/\n(\s+)?\n/g, '\n'));
                    } else {
                        pretty_arguments.push(value);
                    }
                }
                f.apply(context, pretty_arguments);
            };
        };
        console.log = serialize_arguments(console.log, console);
        console.error = serialize_arguments(console.error, console);
    });

    // Make sure the kernel has started
    this.waitFor(this.kernel_running);

    // track the IPython busy/idle state
    this.thenEvaluate(function () {
        require(['base/js/namespace', 'base/js/events'], function (IPython, events) {

            events.on('kernel_idle.Kernel',function () {
                IPython._status = 'idle';
            });
            events.on('kernel_busy.Kernel',function () {
                IPython._status = 'busy';
            });
        });
    });

    // Because of the asynchronous nature of SlimerJS (Gecko), we need to make
    // sure the notebook has actually been loaded into the IPython namespace
    // before running any tests.
    this.waitFor(function() {
        return this.evaluate(function () {
            return IPython.notebook;
        });
    });
};

}).call(this);
