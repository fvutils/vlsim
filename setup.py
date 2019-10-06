
import os
from setuptools import setup

setup(
  name = "vlsim",
  packages=['vlsim'],
  package_dir = {'' : 'src'},
  author = "Matthew Ballance",
  author_email = "matt.ballance@gmail.com",
  description = ("vlsim is a wrapper around Verilator that adds in a simple C++ front-end for clock generation and trace control"),
  license = "Apache 2.0",
  keywords = ["SystemVerilog", "Verilog", "RTL", "Verilator"],
  url = "https://github.com/mballance/vlsim",
  entry_points={
    'console_scripts': [
      'vlsim = vlsim.__main__:main'
    ]
  },
  setup_requires=[
    'setuptools_scm',
  ],
)

