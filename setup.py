from setuptools import setup, find_packages


setup(
    name='crane',
    version='1.1.1',
    url='https://github.com/kiwicom/crane',
    author='Bence Nagy',
    author_email='bence@kiwi.com',
    download_url='https://github.com/kiwicom/crane',
    description='A GitLab CI ready image to upgrade services in Rancher.',
    packages=find_packages(),
    install_requires=[
        'attrs',
        'click',
        'gitpython',
        'requests',
    ],
    entry_points={'console_scripts': 'crane=crane.cli:main'},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Software Distribution',
    ]
)
