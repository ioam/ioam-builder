from setuptools import setup

setup(
    name='ioam_theme',
    version='0.0.1', # SIGH
    zip_safe=False,
    packages=['ioam_theme'],
    package_data={'ioam_theme': [
        'theme.conf',
        '*.html',
        'includes/*.html',
        'static/css/*.css',
        'static/js/*.js',
        'static/images/*.*'
    ]},
    include_package_data=True,
    # See http://www.sphinx-doc.org/en/stable/theming.html#distribute-your-theme-as-a-python-package
    entry_points = {
        'sphinx.html_themes': [
            'name_of_theme = ioam_theme',
        ]
    },
)


