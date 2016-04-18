/* globals require casper Jupyter */
var system = require('system');

var root = casper,
  _img = 0,
  node_modules = system.env.NBPRESENT_TEST_MODULES || "../../../node_modules",
  vendor = root.vendor = root.vendor ? root.vendor : (root.vendor = {}),
  _ = vendor._ = require(node_modules + "/lodash"),
  _shotDir = "_unnamed";

function nextId(){
  return ("000" + (_img++)).slice(-4);
}

function slug(text){
  return text.replace(/[^a-z0-9]/g, "_");
}


root.screenshot = function(message){
  return this.captureSelector([
      "screenshots/",
       _shotDir,
       "/",
       nextId(),
       "_",
       slug(message),
       ".png"
    ].join(""),
    "body"
  );
};


root.screenshot.init = function(ns){
  _shotDir = ns;
  _img = 0;
  return root;
};


root.canSeeAndClick = function(message, visible, click){
  var things = message;

  if(arguments.length !== 1){
    things = [[message, visible, click]];
  }

  var that = this;

  things.map(function(thing){
    var message = thing[0],
      visible = thing[1],
      click = thing[2];

    that = that
      .waitUntilVisible(visible)
      .then(function(){
        this.test.assertExists(click || visible, "I can see and click " + message);
        this.screenshot(message);
        this.click(click || visible);
      });
  });

  return that;
}

root.hasMeta = function(path, tests){
  var meta;

  this.thenEvaluate(function () {
    require(['base/js/events'], function(events) {
      Jupyter._save_success = Jupyter._save_failed = false;
      events.on('notebook_saved.Notebook', function () {
        Jupyter._save_success = true;
      });
      events.on('notebook_save_failed.Notebook',
        function (event, error) {
          Jupyter._save_failed = "save failed with " + error;
      });
      Jupyter.notebook.save_notebook();
    });
});

this.waitFor(function () {
  return this.evaluate(function(){
    return Jupyter._save_failed || Jupyter._save_success;
  });
});

return this
  .then(function(){
    meta = this.evaluate(function(){
      return Jupyter.notebook.metadata;
    });
  })
  .then(function(){
    _.map(tests, function(test, message){
      var results = test(_.get(meta, path));
      this.test.assertEquals(results[0], results[1],
        "I remember " + message + " in " + path);
    }, this);
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

  this.append_cell();
  this.set_cell_text(1, [
    'from IPython.display import Markdown',
    'Markdown("# Hello World!")'
  ].join("\n"));
  this.execute_cell_then(1);

  this.append_cell();
  this.set_cell_text(2, [
    'from ipywidgets import FloatSlider',
    'x = FloatSlider()',
    'x'
  ].join("\n"));
  this.execute_cell_then(2);
}

root.saveNbpresent = function (){
  return this.thenEvaluate(function(){
    window.nbpresent.mode.metadata(true);
  });
}
