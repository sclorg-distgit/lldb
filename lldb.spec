%{?scl:%scl_package lldb}
%{!?scl:%global pkg_name %{name}}

Name:		%{?scl_prefix}lldb
Version:	4.0.1
Release:	5%{?dist}
Summary:	Next generation high-performance debugger

License:	NCSA
URL:		http://lldb.llvm.org/
Source0:	http://llvm.org/releases/%{version}/%{pkg_name}-%{version}.src.tar.xz
Source1:	http://llvm.org/releases/%{version}/llvm-%{version}.src.tar.xz
Source2:	http://llvm.org/releases/%{version}/cfe-%{version}.src.tar.xz

ExclusiveArch:  %{arm} aarch64 %{ix86} x86_64

# lldb: libedit produces garbled, unusable input on Linux
Patch0: r303907-libedit.patch
Patch1: 0001-Fix-LLDB-crash-accessing-unknown-DW_FORM_-attributes.patch

BuildRequires:	%{?scl_prefix}cmake
BuildRequires:  ncurses-devel
BuildRequires:  swig
BuildRequires:  libffi-devel
BuildRequires:  zlib-devel
BuildRequires:  libxml2-devel
BuildRequires:  libedit-devel

%description
LLDB is a next generation, high-performance debugger. It is built as a set
of reusable components which highly leverage existing libraries in the
larger LLVM Project, such as the Clang expression parser and LLVM
disassembler.

%package devel
Summary:	Development header files for LLDB
Requires:	%{?scl_prefix}%{pkg_name}%{?_isa} = %{version}-%{release}

%description devel
The package contains header files for the LLDB debugger.

%package -n %{?scl_prefix}python-lldb
Summary:	Python module for LLDB
BuildRequires:	python2-devel
Requires:	python-six
Requires:	%{?scl_prefix}lldb = %{version}-%{release}

%description -n %{?scl_prefix}python-lldb
The package contains the LLDB Python module.

%prep
%setup -T -q -b 1 -n llvm-%{version}.src
%setup -T -q -b 2 -n cfe-%{version}.src

%setup -q -n %{pkg_name}-%{version}.src
%patch0 -p1
%patch1 -p1

# HACK so that lldb can find its custom readline.so, because we move it
# after install.
sed -i -e "s~import sys~import sys\nsys.path.insert\(1, '%{?scl:%{_scl_root}}%{python_sitearch}/lldb'\)~g" source/Interpreter/embedded_interpreter.py

%build

%global __cmake %{_bindir}/cmake

# This is the location of the Clang and LLVM build that LLDB will link statically to.
INSTALLDIR=%{_builddir}/install-lldb-static

# Add 'lldb-' prefix to the Clang/LLVM source directory to avoid debug info path
# clashes with the regular Clang/LLVM package.
cd %{_builddir}
mv llvm-%{version}.src lldb-llvm-%{version}.src
mv cfe-%{version}.src lldb-cfe-%{version}.src

# Build static LLVM libraries for LLDB.
cd lldb-llvm-%{version}.src
mkdir -p _build
cd _build

%{_bindir}/cmake .. \
        -DBUILD_SHARED_LIBS:BOOL=OFF \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
%ifarch s390
        -DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
        -DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if 0%{?__isa_bits} == 64
        -DLLVM_LIBDIR_SUFFIX=64 \
%else
        -DLLVM_LIBDIR_SUFFIX= \
%endif
        \
        -DLLVM_TARGETS_TO_BUILD="X86;AArch64" \
        -DLLVM_ENABLE_LIBCXX:BOOL=OFF \
        -DLLVM_ENABLE_ZLIB:BOOL=ON \
        -DLLVM_ENABLE_FFI:BOOL=ON \
        -DLLVM_ENABLE_RTTI:BOOL=ON \
%if %{with gold}
        -DLLVM_BINUTILS_INCDIR=%{_includedir} \
%endif
        \
        -DLLVM_BUILD_RUNTIME:BOOL=ON \
        \
        -DLLVM_INCLUDE_TOOLS:BOOL=ON \
        -DLLVM_BUILD_TOOLS:BOOL=ON \
        \
        -DLLVM_INCLUDE_TESTS:BOOL=OFF \
        -DLLVM_BUILD_TESTS:BOOL=OFF \
        \
        -DLLVM_INCLUDE_EXAMPLES:BOOL=OFF \
        -DLLVM_BUILD_EXAMPLES:BOOL=OFF \
        \
        -DLLVM_INCLUDE_UTILS:BOOL=ON \
        -DLLVM_INSTALL_UTILS:BOOL=OFF \
        \
        -DLLVM_INCLUDE_DOCS:BOOL=OFF \
        -DLLVM_BUILD_DOCS:BOOL=OFF \
        -DLLVM_ENABLE_SPHINX:BOOL=OFF \
        -DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
        \
        -DLLVM_BUILD_LLVM_DYLIB:BOOL=OFF \
        -DLLVM_LINK_LLVM_DYLIB:BOOL=OFF \
        -DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
        -DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
        \
        -DSPHINX_WARNINGS_AS_ERRORS=OFF \
        -DCMAKE_VERBOSE_MAKEFILE=ON \
        -DCMAKE_INSTALL_PREFIX=$INSTALLDIR

make %{?_smp_mflags}
make %{?_smp_mflags} install

# Build static Clang libraries for LLDB.
cd ../../lldb-cfe-%{version}.src
mkdir -p _build
cd _build

%{_bindir}/cmake .. \
        -DLLVM_LINK_LLVM_DYLIB:BOOL=OFF \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DLLVM_CONFIG:FILEPATH=$INSTALLDIR/bin/llvm-config \
        \
        -DCLANG_ENABLE_ARCMT:BOOL=ON \
        -DCLANG_ENABLE_STATIC_ANALYZER:BOOL=ON \
        -DCLANG_INCLUDE_DOCS:BOOL=OFF \
        -DCLANG_INCLUDE_TESTS:BOOL=OFF \
        -DCLANG_PLUGIN_SUPPORT:BOOL=ON \
        -DENABLE_LINKER_BUILD_ID:BOOL=ON \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
        -DLLVM_ENABLE_EH=ON \
        -DLLVM_ENABLE_RTTI=ON \
        -DLLVM_ENABLE_SPHINX=ON \
        -DCLANG_BUILD_TOOLS=OFF \
        \
        -DCLANG_BUILD_EXAMPLES:BOOL=OFF \
%if 0%{?__isa_bits} == 64
        -DLLVM_LIBDIR_SUFFIX=64 \
%else
        -DLLVM_LIBDIR_SUFFIX= \
%endif
        -DCMAKE_VERBOSE_MAKEFILE=ON \
        -DCMAKE_INSTALL_PREFIX=$INSTALLDIR

make %{?_smp_mflags}
make %{?_smp_mflags} install

# Now build LLDB itself.
cd ../../%{pkg_name}-%{version}.src
mkdir -p _build
cd _build

# Python version detection is broken

LDFLAGS="%{__global_ldflags} -lpthread -ldl"

CFLAGS="%{optflags} -Wno-error=format-security"
CXXFLAGS="%{optflags} -Wno-error=format-security"

# Tell CMake where it can find LLVMConfig.cmake.
%if 0%{?__isa_bits} == 64
export LLVM_DIR=$INSTALLDIR/lib64/cmake/llvm
%else
export LLVM_DIR=$INSTALLDIR/lib/cmake/llvm
%endif

%cmake .. \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DBUILD_SHARED_LIBS:BOOL=OFF \
        -DLLVM_LINK_LLVM_DYLIB:BOOL=OFF \
	-DLLVM_CONFIG:FILEPATH=$INSTALLDIR/bin/llvm-config \
	\
	-DLLDB_DISABLE_CURSES:BOOL=OFF \
	-DLLDB_DISABLE_LIBEDIT:BOOL=OFF \
	-DLLDB_DISABLE_PYTHON:BOOL=OFF \
%if 0%{?__isa_bits} == 64
        -DLLVM_LIBDIR_SUFFIX=64 \
%else
        -DLLVM_LIBDIR_SUFFIX= \
%endif
	\
	-DPYTHON_EXECUTABLE:STRING=%{__python} \
	-DPYTHON_VERSION_MAJOR:STRING=$(%{__python} -c "import sys; print sys.version_info.major") \
	-DPYTHON_VERSION_MINOR:STRING=$(%{__python} -c "import sys; print sys.version_info.minor")

make %{?_smp_mflags}

%install
cd _build
make install DESTDIR=%{buildroot}

# remove static libraries
rm -fv %{buildroot}%{_libdir}/*.a

# python: fix binary libraries location
liblldb=$(basename $(readlink -e %{buildroot}%{_libdir}/liblldb.so))
ln -vsf "../../../${liblldb}" %{buildroot}%{?scl:%{_scl_root}}%{python_sitearch}/lldb/_lldb.so
mv -v %{buildroot}%{?scl:%{_scl_root}}%{python_sitearch}/readline.so %{buildroot}%{?scl:%{_scl_root}}%{python_sitearch}/lldb/readline.so

# remove bundled six.py
rm -f %{buildroot}%{?scl:%{_scl_root}}%{python_sitearch}/six.*

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%{_bindir}/lldb*
%{_libdir}/liblldb.so.*

%files devel
%{_includedir}/lldb
%{_libdir}/*.so

%files -n %{?scl_prefix}python-lldb
%{?scl:%{_scl_root}}%{python_sitearch}/lldb

%changelog
* Wed Aug 16 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-5
- Statically link llvm and clang libs
  Resolves: #1479847

* Wed Aug 16 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-4
-  Fix crash when loading Fedora debuginfo
   Resloves: #1479529

* Mon Jul 31 2017 Jan Kratochvil <jan.kratochvil@redhat.com> - 4.0.1-3
- Backport lldb r303907
  Resolves: #1356140

* Thu Jun 22 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-2
- Fix requires for python-lldb

* Wed Jun 21 2017 Tom Stellard <tstellar@redhat.com> - 4.0.1-1
- Build for llvm-toolset-7 rename

* Wed Jun 07 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-3
- Build for llvm-toolset-7 rename

* Thu May 18 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-2
- Fix Requires

* Fri Mar 24 2017 Tom Stellard <tstellar@redhat.com> - 4.0.0-1
- lldb 4.0.0

* Tue Mar 21 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-4
- Add explicit Requires for llvm-libs and clang-libs

* Fri Mar 17 2017 Tom Stellard <tstellar@redhat.org> - 3.9.1-3
- Adjust python sys.path so lldb can find readline.so

* Tue Mar 14 2017 Tom Stellard <tstellar@redhat.com> - 3.9.1-2
- Fix build with gcc 7

* Thu Mar 02 2017 Dave Airlie <airlied@redhat.com - 3.9.1-1
- lldb 3.9.1

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 14 2016 Nathaniel McCallum <npmccallum@redhat.com> - 3.9.0-3
- Disable libedit support until upstream fixes it (#1356140)

* Wed Nov  2 2016 Peter Robinson <pbrobinson@fedoraproject.org> 3.9.0-2
- Set upstream supported architectures in an ExclusiveArch

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- lldb 3.9.0
- fixup some issues with MIUtilParse by removing it
- build with -fno-rtti

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.8.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- lldb 3.8.0

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.3
- lldb 3.8.0 rc3

* Wed Feb 24 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.2
- dynamically link to llvm

* Thu Feb 18 2016 Dave Airlie <airlied@redhat.com> - 3.8.0-0.1
- lldb 3.8.0 rc2

* Sun Feb 14 2016 Dave Airlie <airlied@redhat.com> 3.7.1-3
- rebuild lldb against latest llvm

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
