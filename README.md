# Coverage Reporting Tools

Wrappers around DynamoRio's drcov scripts that make them easier to use.

### Prerequisites

The only dependency we have is DynamoRio itself. You can download it from `https://github.com/DynamoRIO/dynamorio`.

### coverage.py

Coverage is a wrapper over `drcov`. The main difference is that it allows you to supply a `samples` directory. Inside this directory there are test case files that will be used to run the target software under `drcov's` coverage instrumentation.

This script requires you to provide an `output` and `samples` directory. The `output` directory will be used to create a project like directory tree that will contain the coverage traces created by `drcov`.

You will also have to supply the script to `DynamoRio's` installation path by using the `-p` argument.

```
usage: coverage.py [-h] -p DR_PATH -o OUTPUT [-d DEBUG_LEVEL] -s SAMPLES
                   command [command ...]
```

### report.py

Report is another wrapper that connects `drcov2lcov` and `genhtml` together. Basically it takes as input the coverage traces created by `coverage.py` and creates an html report.

This script requires you to supply an `output` directory (the one created by `coverage.py`) and the path to `DynamoRio's` installation directory.

You can also supply a single `source filter`. A source filter will only report hits in the files that match the filter. For instance if you supply a filter with `-f JavaScriptCore`, the report will only contain hits inside files that contained `JavaScriptCore` in its path.

The last but most important parameter is the `source mapping` parameter. You can specify as many as you want. The source mapping intended use is to fix missing paths in the report. Sometimes, applications are built on build servers, so debugging symbols will point to source files in directories that may not present on the analyst's machine. By specifiying `source mapping` entries, you can rewrite those paths and make them point to a path that exists on your machine.

For instance `-m ../../Source /tmp/webkit/Source` will map a relative path to the `Source` directory, to an absolute path.

```
usage: report.py [-h] -p DR_PATH -o OUTPUT [-d DEBUG_LEVEL] [-f SRC_FILTER]
                 [-m SRC_MAP SRC_MAP]
```

## Usage example

In this example, we are collecting coverage information about `jsc`.

```
# Collect coverage for files inside `samples`.
python coverage.py                              \
    -p /home/anon/DynamoRIO-Linux-7.0.0-RC1     \
    -o javascriptcore_out                       \
    -s samples                                  \
    -- jsc main.js -- %TESTCASE%

# Generate an html report of the collected coverage.
python report.py                                \
    -p /home/anon/DynamoRIO-Linux-7.0.0-RC1     \
    -o javascriptcore_out                       \
    -f JavaScriptCore                           \
    -m ../../Source /tmp/webkit/Source          \
    -m DerivedSources /tmp/webkit/Source/WebKitBuild/Release/DerivedSources

# Run a webserver to see the results.
pushd $REPORT_DIR
python -m SimpleHTTPServer 2> /dev/null
popd
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
