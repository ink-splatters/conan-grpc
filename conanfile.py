# import os
# import os.path
from pathlib import Path

from conans import ConanFile, CMake, tools


# https://github.com/conan-io/conan/issues/7007
def replace_regex_in_file(file_path: Path, pattern, repl, flags=None, strict=True, output=None, encoding=None):
    import re
    from conans.util.fallbacks import default_output
    from conans.client.tools.files import save, load, _manage_text_not_found

    output = default_output(output, 'replace_regex_in_file')

    encoding_in = encoding or "auto"
    encoding_out = encoding or "utf-8"
    content = load(file_path, encoding=encoding_in)

    content, nb = re.subn(pattern, repl, content, flags=flags)
    if nb == 0:
        _manage_text_not_found(pattern, file_path, strict, 'replace_regex_in_file', output=output)

    content = content.encode(encoding_out)
    save(file_path, content, only_if_modified=False, encoding=encoding_out)


class grpcConan(ConanFile):

    @staticmethod
    def _get_latest(url):
        import urllib.request
        import json

        response = urllib.request.urlopen(url)
        data = response.read()
        releases = json.loads(data.decode('utf-8'))
        for release in releases:
            if not release["draft"] and not release["prerelease"]:
                return release["tag_name"]
        raise Exception('Unknown tags')

    @staticmethod
    def _get_latest_with_cache(url):
        try:
            with open("git.branch", "r") as version_file:
                version = version_file.readline().strip()
        except Exception:
            version = grpcConan._get_latest(url)
        with open("git.branch", "w") as version_file:
            version_file.write(version)
        return version



    name = "grpc"
    description = "gRPC framework with protobuf"
    topics = ("conan", "grpc", "rpc", "protobuf")
    url = "https://github.com/zcube/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    license = "Apache-2.0"
    author = "zcube <zcube@zcube.kr>"
    exports_sources = ["CMakeLists.txt", "grpc.cmake", "git.branch"]
    generators = "cmake", "cmake_find_package_multi"
    short_paths = True  # https://docs.conan.io/en/latest/reference/conanfile/attributes.html#short-paths

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "build_codegen": [True, False],
        "build_csharp_ext": [True, False]
    }

    default_options = {
        "fPIC": True,
        "build_codegen": True,
        "build_csharp_ext": False
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "zlib/1.2.1.1g11", = Path()
    source_subfolder.
        "openssl/1.1.1g",
        "c-ares/1.16.1",
        "abseil/20200923.2",
        "gflags/2.2.2",
        "re2/20201001",
    )

    def set_version(self):
        url = 'https://api.github.com/repos/grpc/grpc/releases'
        self.version = grpcConan._get_latest_with_cache(url)[1:]

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def source(self):
        git = tools.Git(folder=self._source_subfolder)
        git.clone("https://github.com/grpc/grpc.git", "v" + self.version)
        git.checkout_submodules(submodule='recursive')

        source_subfolder = Path(self._source_subfolder)
        TODO
        source_subfolder.
        cmake_path = Path('{}/CMakeLists.txt'.format(self._source_subfolder))

        # don't hardcode c++ standard
        tools.replace_in_file(cmake_path, "set(CMAKE_CXX_STANDARD 11)", "")
        # use Conan abseil package
        replace_regex_in_file(cmake_path, 'absl::[a-z_]+', 'CONAN_PKG::abseil' )

        # use Conan openssl package
        ssl_cmake_path = os.path.join(self._source_subfolder, "cmake", "ssl.cmake")
        tools.replace_in_file(ssl_cmake_path, "${OPENSSL_LIBRARIES}", "CONAN_PKG::openssl")

        cares_cmake_path = os.path.join(self._source_subfolder, "cmake", "cares.cmake")
        gflags_cmake_path = os.path.join(self._source_subfolder, "cmake", "gflags.cmake")
        re2_cmake_path = os.path.join(self._source_subfolder, "cmake", "re2.cmake")

        tools.replace_in_file(cmake_path, "target_include_directories(check_epollexclusive",
                              '''set_source_files_properties(test/build/check_epollexclusive.c PROPERTIES LANGUAGE CXX)
                  target_include_directories(check_epollexclusive''')



        tools.replace_in_file(ssl_cmake_path, "OpenSSL::SSL OpenSSL::Crypto", "CONAN_PKG::openssl")
        tools.replace_in_file(cares_cmake_path, "c-ares::cares", "CONAN_PKG::c-ares")
        if os.path.isfile(gflags_cmake_path):
            tools.replace_in_file(gflags_cmake_path, "gflags::gflags", "CONAN_PKG::gflags", strict=False)
        tools.replace_in_file(re2_cmake_path, "re2::re2", "CONAN_PKG::re2")

        protobuf_cmake_path = os.path.join(self._source_subfolder, "third_party", "protobuf", "cmake")
        protobuf_config_cmake_path = os.path.join(protobuf_cmake_path, "protobuf-config.cmake.in")

        tools.replace_in_file("{}/CMakeLists.txt".format(protobuf_cmake_path),
                              "set(LIB_PREFIX lib)", "set(LIB_PREFIX)")

        tools.replace_in_file("{}/CMakeLists.txt".format(protobuf_cmake_path),
                              "set(CMAKE_CXX_STANDARD 11)", "")

        tools.replace_in_file("{}/install.cmake".format(protobuf_cmake_path),
                              '''set(CMAKE_INSTALL_CMAKEDIR "cmake" CACHE STRING "${_cmakedir_desc}")''',
                              '''set(CMAKE_INSTALL_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/protobuf" CACHE STRING "${_cmakedir_desc}")''')

        tools.replace_in_file("{}/install.cmake".format(protobuf_cmake_path),
                              "CMAKE_INSTALL_CMAKEDIR", "PROTOBUF_CMAKE_INSTALL_CMAKEDIR")

        grpcconfig_cmake_path = os.path.join(self._source_subfolder, "cmake", "gRPCConfig.cmake.in")
        tools.save(grpcconfig_cmake_path, '''
function(grpc_generate)
include(CMakeParseArguments)

set(_options APPEND_PATH)
set(_singleargs LANGUAGE OUT_VAR EXPORT_MACRO PROTOC_OUT_DIR)
if(COMMAND target_sources)
  list(APPEND _singleargs TARGET)
endif()
set(_multiargs PROTOS IMPORT_DIRS GENERATE_EXTENSIONS)

cmake_parse_arguments(grpc_generate "${_options}" "${_singleargs}" "${_multiargs}" "${ARGN}")

if(NOT grpc_generate_TARGET)
message(SEND_ERROR "Error: grpc_generate called without any targets or source files")
return()
endif()

find_program(_GRPC_CPP_PLUGIN NAMES grpc_cpp_plugin)
mark_as_advanced(_GRPC_CPP_PLUGIN)

protobuf_generate(TARGET ${grpc_generate_TARGET} LANGUAGE cpp)
set(_GRPC_PLUGIN "protoc-gen-grpc=${_GRPC_CPP_PLUGIN}")
protobuf_generate(TARGET ${grpc_generate_TARGET} PLUGIN ${_GRPC_PLUGIN} LANGUAGE grpc GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc)

endfunction(grpc_generate)
''', append=True)

        tools.replace_in_file(protobuf_config_cmake_path,
                              '''file(RELATIVE_PATH _rel_dir ${DIR} ${_abs_dir})''',
                              '''string(FIND "${_rel_dir}" "../" _is_in_parent_folder)''')
        tools.replace_in_file(protobuf_config_cmake_path,
                              '''if(NOT "${_rel_dir}" MATCHES "^\.\.[/\\\\].*")''',
                              '''if (NOT ${_is_in_parent_folder} EQUAL 0)''')

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions['gRPC_BUILD_CODEGEN'] = "ON" if self.options.build_codegen else "OFF"
        cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "ON" if self.options.build_csharp_ext else "OFF"
        cmake.definitions['gRPC_BUILD_TESTS'] = "OFF"
        cmake.definitions['gRPC_INSTALL'] = "ON"
        cmake.definitions['gRPC_USE_PROTO_LITE'] = "OFF"

        cmake.definitions['gRPC_ABSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "package"
        cmake.definitions['gRPC_RE2_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "module"
        cmake.definitions['gRPC_INSTALL_CMAKEDIR'] = "lib/cmake/gRPC"

        cmake.definitions['protobuf_BUILD_SHARED_LIBS'] = "OFF"
        cmake.definitions['gRPC_BUILD_SHARED_LIBS'] = "OFF"

        cmake.definitions['protobuf_DEBUG_POSTFIX'] = ""

        cmake.definitions['protobuf_INSTALL'] = "ON"
        cmake.definitions["protobuf_BUILD_TESTS"] = "OFF"
        cmake.definitions["protobuf_WITH_ZLIB"] = "ON"
        cmake.definitions["protobuf_BUILD_PROTOC_BINARIES"] = "ON" if self.options.build_codegen else "OFF"
        cmake.definitions["protobuf_BUILD_PROTOBUF_LITE"] = "OFF"

        if self.settings.compiler == "Visual Studio":
            cmake.definitions["protobuf_MSVC_STATIC_RUNTIME"] = "MT" in self.settings.compiler.runtime
            cmake.definitions["gRPC_MSVC_STATIC_RUNTIME"] = "MT" in self.settings.compiler.runtime

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    @property
    def _cmake_install_base_path(self):
        return os.path.join("cmake")

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

        self.copy(pattern="LICENSE", dst="licenses")
        self.copy('grpc.cmake', dst=self._cmake_install_base_path)
        self.copy('*', dst='include', src='{}/third_party/googleapis'.format(self._source_subfolder), keep_path=True)
        self.copy('*', dst='include', src='{}/include'.format(self._source_subfolder))
        self.copy('*.cmake', dst='lib', src='{}/lib'.format(self._build_subfolder), keep_path=True)
        self.copy("*.lib", dst="lib", src="", keep_path=False)
        self.copy("*.a", dst="lib", src="", keep_path=False)
        self.copy("*", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        self.cpp_info.libs = [
            "grpc++_alts",
            "grpc++_unsecure",
            "grpc++_reflection",
            "grpc++_error_details",
            "grpc++",
            "grpc_unsecure",
        ]
        if self.options.build_codegen:
            self.cpp_info.libs += [
                "grpc_plugin_support",
            ]
        self.cpp_info.libs += [
            "grpcpp_channelz",
            "grpc",
            "gpr",
            "address_sorting",
            "upb",
            "protobuf-lite",
            "protobuf",
        ]
        if self.options.build_codegen:
            self.cpp_info.libs += [
                "protoc",
            ]

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)

        # self.cpp_info.builddirs = [
        #    self._cmake_install_base_path,
        # ]
        self.cpp_info.build_modules = [
            os.path.join(self._cmake_install_base_path, "grpc.cmake"),
        ]
