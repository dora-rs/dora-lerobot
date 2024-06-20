# Installation script

from setuptools import setup

package_name = 'alexk_arm'

setup(name='Alexk Arm',
      version='1.0',
      description='Python API for the Alexk Arm',
      author='Enzo Le Van',
      author_email='dev@enzo-le-van.fr',
      packages=[package_name],
      install_requires=['numpy', 'dynamixel_sdk'],
      )
