# Running Tests

Tests need both your `celly` installation and this top-level directory in
their search path, which means you might need to do something like:

    export PYTHONPATH="/path/to/celly:${PWD}"
    py.test

