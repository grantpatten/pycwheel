Compile all py files in a wheel to pyc files
============================================

The package version information is changed to append .compiled to the end.

If you want the pyc only version of the wheel, specify the .compiled version in your
requirements file.

Usage
-----

.. code-block:: bash

    $ pycwheel your_wheel-1.0.0-py2-none-any.whl
    # Output: your_wheel-1.0.0.compiled-py2-none-any.whl
