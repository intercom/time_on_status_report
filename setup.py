from setuptools import setup

setup(
    name='generate_time_on_status_report',
    version='0.1.0',
    py_modules=['report_time_on_status'],
    install_requires=[
        'Click',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'generate_time_on_status_report = time_on_status:generate_report',
        ],
    },
)
