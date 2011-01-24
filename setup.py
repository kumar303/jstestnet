
from setuptools import setup, find_packages

setup(name='jstestnet',
      version='0.1',
      description="""JS TestNet is a Django_ web service that coordinates the
                     execution of JavaScript tests across web browsers.""",
      long_description="",
      author='Kumar McMillan',
      author_email='kumar.mcmillan@gmail.com',
      license="Apache License",
      packages=find_packages(exclude=['ez_setup']),
      install_requires=[], # see requirements.txt
      tests_require=[], # see tox.ini
      # url='',
      )
