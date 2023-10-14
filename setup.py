from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
        name='psetup',
        version='0.1.0',
        author='Raphaël',
        author_email='r@gmail.com',
        description='Setup tool for Google Cloud organization structure',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/RaphaeldeGail',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        install_requires=[],
        python_requires='>=3.9',
        entry_points={
            'console_scripts': [
                'psetup=psetup.cli:main'
            ],
        }
)