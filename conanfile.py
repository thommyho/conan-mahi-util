
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
from shutil import which
import fnmatch


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    # from whichcraft import which
    return which(name) is not None


class MahiUtilsConan(ConanFile):
    name = "mahi_util"
    description = "Utility classes and common functionality use by the mahi-lib ecosystem"
    homepage = "https://github.com/mahilab/mahi-util"
    license = "MIT"
    topics = ("conan", "mahi", "utility")
    url = "https://github.com/conan-io/conan-center-index"
    generators = "cmake"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    exports_sources = "CMakeLists.txt"
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 11)
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration(
                "oatpp can not be built as shared library on Windows")
        if self.settings.compiler == "gcc" and tools.Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration("oatpp requires GCC >=5")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("mahi-util-master", self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        if is_tool('Ninja'):
            self._cmake = CMake(self, generator='Ninja')
        else:
            self._cmake = CMake(self)
        self._cmake.definitions["MAHI_UTIL_EXAMPLES"] = False
        self._cmake.configure(build_folder=self._build_subfolder,
                              source_folder=self._source_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            if self.settings.build_type == "Debug" or self.settings.build_type == "RelWithDebInfo":
                self.output.info("Searching for pdbs")
                patterns = ['util', 'fmt']
                for root, dirs, files in os.walk(self._build_subfolder):
                    for pattern in patterns:
                        for filename in fnmatch.filter(files, pattern+'*.pdb'):
                            self.copy(pattern=filename, dst="lib",
                                      src=root, keep_path=False)
                            self.output.info("Copied pdb: %s" % filename)
        self.copy('*', src=os.path.join(self._source_subfolder,
                                        '3rdparty', 'fmt', 'include'), dst="include")

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "mahi_util"
        self.cpp_info.names["cmake_find_package_multi"] = "mahi_util"
        self.cpp_info.components["_mahi_util"].names["cmake_find_package"] = "mahi_util"
        self.cpp_info.components["_mahi_util"].names["cmake_find_package_multi"] = "mahi_util"
        if self.settings.build_type == "Debug":
            self.cpp_info.components["_mahi_util"].libs = [
                "mahi-util-d", "fmtd"]
        else:
            self.cpp_info.components["_mahi_util"].libs = ["mahi-util", "fmt"]
