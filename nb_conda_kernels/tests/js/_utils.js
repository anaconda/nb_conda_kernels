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
  }

  root.canSeeAndClick = function(message, visible, click){
    return this
      .waitUntilVisible(visible)
      .then(function(){
        this.test.assertExists(click || visible, "I can see and click " + message);
        this.screenshot(message);
        this.click(click || visible);
      });
  }

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
  }

}).call(this);
