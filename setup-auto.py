import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import find_resource_files

### Apps Definition ###
tethysapp_dir_list = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', child)
                      for child in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp'))]
app_package = os.path.basename(list(filter(os.path.isdir, tethysapp_dir_list))[0])
release_package = 'tethysapp-' + app_package
app_class = '{0}.app:Hydroviewer'.format(app_package)
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

# -- Get Resource File -- #
resource_files = find_resource_files('tethysapp/' + app_package + '/templates')
resource_files += find_resource_files('tethysapp/' + app_package + '/public')


setup(
    name=release_package,
    version='0.0.1',
    description='',
    long_description='',
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data={'': resource_files},
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=[]
)
