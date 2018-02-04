from setuptools import setup

setup(name='zapi',
      description='zapi',
      version='0.0.148',
      packages=['zapi'],
      install_requires=[
          'flask',
          'pymysql',
          'PyJWT',
          'cryptography',
          'jsonschema',
          'requests'
      ],
      zip_safe=True)
