from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    long_description = f.read()

dependencies = [
    'google-api-python-client >= 2.89.0',
    'google-cloud-billing >= 1.12.0',
    'google-cloud-resource-manager >= 1.10.4',
    'google-cloud-service-usage >= 1.8.0',
    'grpc-google-iam-v1 >= 0.12.7',
    'PyYAML >= 6.0.1',
    'terrasnek >= 0.1.13',
]

setup(
        name='psetup',
        version='0.2.0',
        author='Raphaël',
        author_email='r@gmail.com',
        description='Setup tool for Google Cloud organization structure',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/RaphaeldeGail',
        packages=find_packages('src'),
        package_dir={'': 'src'},
        data_files=[('config/psetup', ['default.yaml'])],
        install_requires=dependencies,
        python_requires='>=3.9',
        entry_points={
            'console_scripts': [
                'psetup=psetup.cli:main',
                'wsetup=psetup.workspace_cli:main'
            ],
        }
)