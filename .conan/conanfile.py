from conans import ConanFile, tools
from conans.errors import CalledProcessErrorWithStderr


class ConanPackage(ConanFile):
    name = 'compile-time-printer'
    license = 'BSL-1.0'
    url = 'https://github.com/Viatorus/compile-time-printer'
    description = 'The C++ files for the compile-time printer.'
    exports_sources = '../include/**'
    no_copy_source = True

    def set_version(self):
        git = tools.Git(folder=self.recipe_folder)
        try:
            self.version = git.run('describe --tags --abbrev=0')
        except CalledProcessErrorWithStderr:
            self.version = '0.0.0'

    def package(self):
        self.copy('*.hpp', dst='include')

    def package_id(self):
        self.info.header_only()

    def package_info(self):
        self.cpp_info.cxxflags = ['-fpermissive']
