from distutils.core import setup
import py2exe

setup(windows=['TagMe.py'],
      options={
                "py2exe":{
                        "unbuffered": True,
                        "optimize": 2,
                         }
              }
        )
