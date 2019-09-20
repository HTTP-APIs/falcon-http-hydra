# !/usr/bin/env python
"""Setup script for Hydrus."""

from setuptools import setup, find_packages

setup(name='hydrus',
      include_package_data=True,
      version='0.0.1',
      description='A space-based application for W3C HYDRA Draft',
      author='W3C HYDRA development group',
      author_email='collective@hydraecosystem.org',
      url='https://github.com/HTTP-APIs/hydrus',
      py_modules=['cli'],
      python_requires='>=3',
      install_requires=[
          'MarkupSafe==1.0',
          'SQLAlchemy==1.1.10',
          'Werkzeug==0.15.3',
          'aniso8601==1.2.1',
          'appdirs==1.4.3',
          'argparse==1.2.1',
          'click==6.7',
          'itsdangerous==0.24',
          'lifter==0.4.1',
          'packaging==16.8',
          'persisting-theory==0.2.1',
          'psycopg2',
          'pyparsing==2.2.0',
          'python-dateutil==2.6.0',
          'pytz==2017.2',
          'six==1.10.0',
          'thespian==3.5.2',
          'blinker==1.4',
          'typing==3.6.4',
          'mypy',
          'Click',
          'gevent==1.2.2',
           'falcon'
      ],
      packages=find_packages(exclude=['contrib', 'docs', 'tests*', 'hydrus.egg-info']),
      package_dir={'hydrus':
                    'hydrus'},
      entry_points='''
            [console_scripts]
            hydrus=cli:startserver
        '''
      )
