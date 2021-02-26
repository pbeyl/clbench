# Cloud Access Benchmark

This is a simple script to measure user cloud experience by timing a number of page loads through automated Chrome Browser

Using this approach can offer insight into performance of cloud web proxies compared to a baseline like direct to net.

This is arguable more accurate than an internet speed test since this is testing actual page load times and therefore reflect actual user experience.

## Usage

1. Populate urls.csv with a list of test sites
2. Test a baseline direct to cloud performance by disabling any steering client or proxy settings
3. Run the first series of tests using script
   
    `python clbench.py`
4. Enable steering client/proxy to route traffic via SWG
5. Complete second series of tests
6. Graph the test results using the graph option in the script menu

## Pre-requisites

- Google Chrome browser must be installed
- python3

## Installation

- Extract files to a directory
- Install required python modules
  
    `pip install -r requirements.txt`
    
## Windows
- Double click run.bat
    
## OSX Detailed Install

- Change to Cloud Access Benchmark folder in terminal
- Create virtual environment
 
    `$ virtualenv venv -p /usr/bin/python3`
    
- Activate virtual environment
 
    `$ source venv/bin/activate`
    
- Install the required pre-requisites to virtual environment
 
    `(venv) $ pip install -r requirements.txt`

- Run the cloud_access_benchmark.py script

	`$ python clbench.py`_