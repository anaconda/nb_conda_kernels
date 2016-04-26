"%PREFIX%\npm.cmd" install . --no-spin --no-progress && "%PREFIX%\npm.cmd" run test --no-progress --no-spin && if errorlevel 1 exit 1
