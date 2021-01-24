from setuptools import find_packages, setup

setup(
    name='main',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
		'flask-bcrypt',
		'flask-api',
		'psycopg2-binary',
    ],
	extras_require={"test": ["pytest", "mock", "coverage", "testcontainers[postgres]", "sqlalchemy"]},
)
