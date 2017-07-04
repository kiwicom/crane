from setuptools import setup, find_packages


setup(
    name='crane',
    version='0.2.0',
    url='https://gitlab.skypicker.com/bence/crane',
    author='Bence Nagy',
    author_email='bece@kiwi.com',
    download_url='https://gitlab.skypicker.com/bence/crane',
    description='GitLab CI + Rancher deployment',
    packages=find_packages(),
    install_requires=[
        'click',
        'requests',
    ],
    entry_points={'console_scripts': 'crane=crane.cli:main'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ]
)
