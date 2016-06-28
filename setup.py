import platform
import sys

from setuptools import setup

install_requires = [
    'neovim>=0.1.3',
    'click>=3.0',
    'pygobject'
]
ext_modules = None

# Cythonizing screen.py to improve scrolling/clearing speed. Maybe the
# performance can be improved even further by writing a screen.pxd with
# static type information
try:
    from Cython.Build import cythonize
    ext_modules = cythonize('neovim_gui/screen.py')
except ImportError:
    pass

entry_points = {'console_scripts':  ['pynvim=neovim_gui.cli:main'] }

setup(name='neovim_gui',
      version='0.1.3',
      description='Gtk gui for neovim',
      url='http://github.com/neovim/python-gui',
      download_url='https://github.com/neovim/python-gui/archive/0.1.3.tar.gz',
      author='Thiago de Arruda',
      author_email='tpadilha84@gmail.com',
      license='Apache',
      packages=['neovim_gui'],
      install_requires=install_requires,
      ext_modules=ext_modules,
      entry_points=entry_points,
      zip_safe=False)
