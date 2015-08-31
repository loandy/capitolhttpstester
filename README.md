# Capitol HTTPS Tester
*Examining SSL certificates for senate.gov and house.gov*

## Introduction

This code tests US Capitol websites for valid HTTPS configurations. There are
two major bits of code: `capitolhttpstester.py`and `maketable.py`.

The article that accompanies this post can be found [here](
https://sunlightfoundation.com/blog/2015/05/26/sunlight-analysis-reveals-15-of-congressional-websites-are-https-ready).

## Dependencies

* [pip](https://pip.pypa.io/en/latest/installing.html)
* [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)

## Getting Started

To get the basic setup, run the following commands from your terminal:

```sh
$ virtualenv --no-site-packages virt
$ source virt/bin/activate
$ pip install -r requirements.txt
$ cp settings.py.example settings.py
$ edit settings.py # Place your Sunlight API key here.
```

If you wish to use npm/Grunt, the following commands will install the requisite node modules, kick off the data-gathering script, and then render the results into a final HTML report:

```sh
$ npm install
$ grunt --filename=example_filename.json
```
The resulting data are placed in output.json by default if no filename is provided, but an arbitrary filename may be provided through the --filename option when running Grunt.

If you wish to only generate the data, or refresh the HTML report, you utilize the following Grunt tasks respectively:

```sh
$ grunt:data --filename=example_filename.json
```

```sh
$ grunt:build --filename=example_filename.json
```

For this project, Grunt is primarily used for the minification of the resulting HTML report.  If you do not want to use npm/Grunt, simply run the Python scripts manually instead:

```sh
$ python capitolhttpstester.py > output.json
$ python render_template.py output.json
```

The generated HTML document report should be located under the `rendered` directory as `test_results.html`.

## Important Files

`capitolhttpstest.py` -- Retrieves data and creates a json summary

`render_template.py` -- Parses JSON summary and generates a webpage summarizing the results.

`get-cert.sh` -- Simple script to go and get SSL certificate for hostname, because learning how to use OpenSSL is painful.

`install.sh` -- Simple script to create to get this thing up and running. Not the same as actually making a package!

`settings.py.example` -- Should be copied to `settings.py` with a functioning Sunlight API key.

All code should be covered under GPLv2.0.

--timball@sunlightfoundation.com
2015-05-25
