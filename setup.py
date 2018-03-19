from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='uniswap',
    description='Uniswap Market Maker',
    long_description=readme,
    author='Hayden Adams',
    author_email='',
    license=license,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'ethereum',
        'web3',
        'py-solc',
        'pytest'
    ],
)
