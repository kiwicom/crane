from setuptools import setup


setup(
    name='advance',
    version='0.1.0',
    url='https://gitlab.skypicker.com/simone/advance',
    author='Simone Esposito',
    author_email='simone@kiwi.com',
    download_url='https://gitlab.skypicker.com/simone/advance',
    description='GitLab CI + Rancher deployment',
    packages=['advance'],
    install_requires=[
        'requests<3',
    ],
    entry_points={'console_scripts': 'advance=advance:main'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ]
)
